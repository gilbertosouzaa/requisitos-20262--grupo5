import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from app.auth import auth_bp
from app.auth.forms import LoginForm, CadastroForm, RecuperarSenhaForm, RedefinirSenhaForm
from app.extensions import db
from app.models import Usuario, Curso, TokenRecuperacao, utc_now
from app.services.email import simular_envio_recuperacao

def is_safe_url(target):
    """Garante que o redirecionamento pós-login seja para uma rota interna segura."""
    if not target:
        return False
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target)
    return test_url.scheme in ('', 'http', 'https') and (test_url.netloc == '' or test_url.netloc == ref_url.netloc)


@auth_bp.route('/entrar', methods=['GET', 'POST'])
def login():
    """T02 - Login (RF02 / US02, RN11)."""
    if current_user.is_authenticated:
        if current_user.perfil == 'admin':
            return redirect(url_for('admin.questoes'))
        if current_user.perfil == 'professor':
            return redirect(url_for('admin.comentarios'))
        return redirect(url_for('main.inicio'))

    form = LoginForm()
    erro_generico = None
    next_page = request.args.get('next')

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        senha = form.senha.data

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.verificar_senha(senha):
            if not usuario.ativo:
                erro_generico = "Esta conta está desativada. Procure a coordenação do curso."
            else:
                usuario.ultimo_acesso_em = utc_now()
                db.session.commit()
                login_user(usuario)
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                if usuario.perfil == 'admin':
                    return redirect(url_for('admin.questoes'))
                if usuario.perfil == 'professor':
                    return redirect(url_for('admin.comentarios'))
                return redirect(url_for('main.inicio'))
        else:
            # US02: Erro genérico que NÃO diz qual campo está incorreto
            erro_generico = "E-mail ou senha incorretos."

    return render_template('auth/login.html', form=form, erro_generico=erro_generico, next_page=next_page)


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """T03 - Cadastro (RF01 / US01)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    form = CadastroForm()
    # Carrega os cursos disponíveis
    cursos = Curso.query.order_by(Curso.nome).all()
    form.curso_id.choices = [(c.id, c.nome) for c in cursos]

    email_ja_cadastrado = False

    if form.validate_on_submit():
        email_limpo = form.email.data.strip().lower()
        usuario_existente = Usuario.query.filter_by(email=email_limpo).first()

        if usuario_existente:
            # US01: Se o e-mail já existir, mostra mensagem junto ao campo e não cria a conta
            email_ja_cadastrado = True
        else:
            novo_usuario = Usuario(
                nome=form.nome.data.strip(),
                email=email_limpo,
                curso_id=form.curso_id.data,
                perfil='estudante'
            )
            novo_usuario.set_senha(form.senha.data)
            db.session.add(novo_usuario)
            db.session.commit()

            # Sucesso: entra no sistema e vai para /inicio
            login_user(novo_usuario)
            return redirect(url_for('main.inicio'))

    return render_template(
        'auth/cadastro.html',
        form=form,
        email_ja_cadastrado=email_ja_cadastrado
    )


@auth_bp.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    """T04 - Solicitação de recuperação de senha (RF03 / US03)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    form = RecuperarSenhaForm()

    if form.validate_on_submit():
        email_digitado = form.email.data.strip().lower()
        usuario = Usuario.query.filter_by(email=email_digitado).first()

        if usuario:
            # Cria token com expiração de 1 hora
            token_str = secrets.token_urlsafe(32)
            expira_em = datetime.now(timezone.utc) + timedelta(hours=1)
            token_obj = TokenRecuperacao(
                usuario_id=usuario.id,
                token=token_str,
                expira_em=expira_em,
                usado=False
            )
            db.session.add(token_obj)
            db.session.commit()

            link = url_for('auth.redefinir_senha', token=token_str, _external=True)
            simular_envio_recuperacao(usuario.email, link)

        # SEMPRE renderiza a tela "Verifique seu e-mail" sem revelar se o e-mail existe
        return render_template('auth/recuperar_senha_enviado.html', email=email_digitado)

    return render_template('auth/recuperar_senha.html', form=form)


@auth_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    """T04 - Redefinição de senha com verificação de validade do token (RF03 / US03)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    token_obj = TokenRecuperacao.query.filter_by(token=token).first()

    # Verifica validade do token (expirado, usado ou inexistente)
    if not token_obj or not token_obj.is_valido():
        return render_template('auth/token_expirado.html')

    form = RedefinirSenhaForm()
    if form.validate_on_submit():
        usuario = token_obj.usuario
        usuario.set_senha(form.nova_senha.data)
        token_obj.usado = True
        db.session.commit()

        flash("Senha redefinida com sucesso! Você já pode entrar com sua nova senha.", "sucesso")
        return redirect(url_for('auth.login'))

    return render_template('auth/redefinir_senha.html', form=form, token=token)


@auth_bp.route('/sair', methods=['POST'])
def logout():
    """Encerra a sessão do usuário autenticado."""
    if current_user.is_authenticated:
        logout_user()
        flash("Você saiu da sua conta.", "info")
    return redirect(url_for('auth.login'))
