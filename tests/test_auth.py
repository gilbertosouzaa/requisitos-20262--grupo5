import pytest
from datetime import datetime, timedelta, timezone
from app import create_app
from app.extensions import db, bcrypt
from app.models import Usuario, Curso, TokenRecuperacao, Questao
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Popula um curso de teste
        curso = Curso(nome="Ciência da Computação")
        db.session.add(curso)
        db.session.commit()

        # Popula usuário Ana Souza
        ana = Usuario(
            nome="Ana Souza",
            email="ana@teste.com",
            curso_id=curso.id,
            perfil="estudante"
        )
        ana.set_senha("12345678")
        db.session.add(ana)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


# ==============================================================================
# US01 — Criar conta
# ==============================================================================
def test_us01_cadastro_sucesso(client, app):
    """US01: Cadastro com sucesso cria conta e loga o estudante."""
    with app.app_context():
        curso = Curso.query.first()
        curso_id = curso.id

    res = client.post('/cadastro', data={
        'nome': 'Carlos Silva',
        'email': 'carlos@teste.com',
        'senha': 'senhaSegura123',
        'curso_id': curso_id,
        'termos': 'y'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Carlos Silva" in res.data
    assert b"Ol\xc3\xa1, Carlos Silva" in res.data or b"Carlos Silva" in res.data

    with app.app_context():
        usuario = Usuario.query.filter_by(email='carlos@teste.com').first()
        assert usuario is not None
        assert usuario.nome == 'Carlos Silva'
        # RNF03: Senha com hash bcrypt
        assert usuario.senha_hash.startswith('$2b$') or usuario.senha_hash.startswith('$2a$')
        assert usuario.verificar_senha('senhaSegura123') is True
        assert usuario.verificar_senha('senhaErrada') is False


def test_us01_cadastro_email_duplicado(client, app):
    """US01: Se o e-mail já existe, exibe 'E-mail já cadastrado' e não cria nova conta."""
    with app.app_context():
        curso = Curso.query.first()
        curso_id = curso.id
        total_usuarios_antes = Usuario.query.count()

    res = client.post('/cadastro', data={
        'nome': 'Outra Ana',
        'email': 'ana@teste.com',  # Já cadastrado no fixture
        'senha': 'senhaSegura123',
        'curso_id': curso_id,
        'termos': 'y'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert "E-mail já cadastrado".encode('utf-8') in res.data or b"E-mail j&aacute; cadastrado" in res.data

    with app.app_context():
        total_usuarios_depois = Usuario.query.count()
        assert total_usuarios_depois == total_usuarios_antes


def test_us01_cadastro_senha_curta(client, app):
    """US01: Senha com menos de 8 caracteres não deve ser aceita."""
    with app.app_context():
        curso_id = Curso.query.first().id

    res = client.post('/cadastro', data={
        'nome': 'Lucas Teste',
        'email': 'lucas@teste.com',
        'senha': '12345',  # < 8
        'curso_id': curso_id,
        'termos': 'y'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert "8 caracteres".encode('utf-8') in res.data
    # Garante que usuário não foi criado
    with app.app_context():
        assert Usuario.query.filter_by(email='lucas@teste.com').first() is None



# ==============================================================================
# US02 — Entrar e Sair
# ==============================================================================
def test_us02_login_sucesso(client):
    """US02: E-mail e senha corretos levam à tela inicial."""
    res = client.post('/entrar', data={
        'email': 'ana@teste.com',
        'senha': '12345678'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Ana Souza" in res.data
    assert b"In\xc3\xadcio" in res.data or b"In&iacute;cio" in res.data


def test_us02_login_senha_incorreta(client):
    """US02: Erro genérico 'E-mail ou senha incorretos' sem indicar qual campo errou."""
    res = client.post('/entrar', data={
        'email': 'ana@teste.com',
        'senha': 'senha_errada'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert "E-mail ou senha incorretos.".encode('utf-8') in res.data


def test_us02_login_email_inexistente(client):
    """US02: Mesmo erro genérico para e-mail não existente."""
    res = client.post('/entrar', data={
        'email': 'naoexiste@teste.com',
        'senha': '12345678'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert "E-mail ou senha incorretos.".encode('utf-8') in res.data


def test_us02_logout(client):
    """US02: Logout encerra a sessão."""
    # Primeiro loga
    client.post('/entrar', data={
        'email': 'ana@teste.com',
        'senha': '12345678'
    }, follow_redirects=True)

    # Depois sai
    res = client.post('/sair', follow_redirects=True)
    assert res.status_code == 200
    assert b"Entrar" in res.data


# ==============================================================================
# US03 — Recuperar Senha
# ==============================================================================
def test_us03_solicitar_recuperacao(client, app):
    """US03: Informar e-mail cadastrado gera token válido por 1 hora e exibe mensagem padrão."""
    res = client.post('/recuperar-senha', data={
        'email': 'ana@teste.com'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Verifique seu e-mail" in res.data
    assert "O link vale por".encode('utf-8') in res.data or b"O link vale por" in res.data
    assert "1 hora".encode('utf-8') in res.data

    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        token = TokenRecuperacao.query.filter_by(usuario_id=ana.id).order_by(TokenRecuperacao.id.desc()).first()
        assert token is not None
        assert token.usado is False
        assert token.is_valido() is True


def test_us03_solicitar_recuperacao_email_inexistente(client):
    """US03: E-mail não cadastrado mostra a mesma mensagem amigável sem revelar sua ausência."""
    res = client.post('/recuperar-senha', data={
        'email': 'inexistente@teste.com'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Verifique seu e-mail" in res.data
    assert b"inexistente@teste.com" in res.data


def test_us03_redefinir_senha_sucesso(client, app):
    """US03: Com token válido, permite criar nova senha e atualiza o hash."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        token = TokenRecuperacao(
            usuario_id=ana.id,
            token="token_valido_12345",
            expira_em=datetime.now(timezone.utc) + timedelta(hours=1),
            usado=False
        )
        db.session.add(token)
        db.session.commit()

    # GET na rota com token
    res = client.get('/redefinir-senha/token_valido_12345')
    assert res.status_code == 200
    assert "Definir nova senha".encode('utf-8') in res.data or b"Definir nova senha" in res.data

    # POST com nova senha
    res_post = client.post('/redefinir-senha/token_valido_12345', data={
        'nova_senha': 'novaSenha8765',
        'confirma_senha': 'novaSenha8765'
    }, follow_redirects=True)

    assert res_post.status_code == 200
    assert "Senha redefinida com sucesso".encode('utf-8') in res_post.data or b"redefinida com sucesso" in res_post.data

    # Verifica que token foi marcado como usado e a nova senha funciona
    with app.app_context():
        token_atualizado = TokenRecuperacao.query.filter_by(token="token_valido_12345").first()
        assert token_atualizado.usado is True
        ana_atualizada = Usuario.query.filter_by(email='ana@teste.com').first()
        assert ana_atualizada.verificar_senha('novaSenha8765') is True


def test_us03_token_expirado_ou_usado(client, app):
    """US03: Token expirado orienta usuário a pedir um novo link."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        # Token com expiração no passado (mais de 1 hora atrás)
        token_expirado = TokenRecuperacao(
            usuario_id=ana.id,
            token="token_expirado_999",
            expira_em=datetime.now(timezone.utc) - timedelta(minutes=10),
            usado=False
        )
        # Token já usado
        token_usado = TokenRecuperacao(
            usuario_id=ana.id,
            token="token_ja_usado_888",
            expira_em=datetime.now(timezone.utc) + timedelta(hours=1),
            usado=True
        )
        db.session.add_all([token_expirado, token_usado])
        db.session.commit()

    # Tentativa com token expirado
    res_exp = client.get('/redefinir-senha/token_expirado_999')
    assert res_exp.status_code == 200
    assert "Este link expirou".encode('utf-8') in res_exp.data or b"Este link expirou" in res_exp.data
    assert "Pedir novo link".encode('utf-8') in res_exp.data or b"Pedir novo link" in res_exp.data

    # Tentativa com token já usado
    res_usado = client.get('/redefinir-senha/token_ja_usado_888')
    assert res_usado.status_code == 200
    assert "Este link expirou".encode('utf-8') in res_usado.data or b"Este link expirou" in res_usado.data
