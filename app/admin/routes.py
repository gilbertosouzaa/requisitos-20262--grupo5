import csv
import io
import os
import uuid
from datetime import datetime, timezone
from flask import (
    render_template, request, redirect, url_for, flash,
    jsonify, current_app, send_from_directory, Response, session, abort
)
from werkzeug.utils import secure_filename
from flask_login import current_user

from app.admin import admin_bp
from app.auth import requer_perfil
from app.extensions import db
from app.models import (
    Curso, Questao, Alternativa, RespostaEstudo,
    SimuladoQuestao, SimuladoResposta, utc_now
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.route('/')
@requer_perfil('admin')
def index():
    """Redireciona a raiz do admin para a lista de questões."""
    return redirect(url_for('admin.questoes'))


# ==============================================================================
# Servir arquivos de Upload
# ==============================================================================

@admin_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve imagens salvas na pasta instance/uploads."""
    uploads_dir = os.path.join(current_app.instance_path, 'uploads')
    return send_from_directory(uploads_dir, filename)


# ==============================================================================
# T13: Lista de Questões (RF19, US10)
# ==============================================================================

@admin_bp.route('/questoes')
@requer_perfil('admin')
def questoes():
    """T13 - Lista de questões cadastradas com filtros, paginação e ações."""
    # Resumo / KPIs
    total_cadastradas = Questao.query.count()
    total_anuladas = Questao.query.filter_by(anulada=True).count()
    total_sem_comentario = Questao.query.filter(Questao.comentario_status != 'publicado').count()

    # Filtros via query string (GET)
    busca = request.args.get('busca', '').strip()
    curso_id = request.args.get('curso', type=int)
    ano = request.args.get('ano', type=int)
    area = request.args.get('area', '').strip()
    situacao = request.args.get('situacao', 'todas')
    page = request.args.get('page', 1, type=int)

    query = Questao.query

    if busca:
        if busca.isdigit():
            query = query.filter((Questao.numero == int(busca)) | (Questao.enunciado.ilike(f'%{busca}%')))
        else:
            query = query.filter(Questao.enunciado.ilike(f'%{busca}%'))

    if curso_id:
        query = query.filter(Questao.curso_id == curso_id)

    if ano:
        query = query.filter(Questao.ano == ano)

    if area:
        query = query.filter(Questao.area == area)

    if situacao == 'ativas':
        query = query.filter(Questao.anulada == False)  # noqa: E712
    elif situacao == 'anuladas':
        query = query.filter(Questao.anulada == True)   # noqa: E712
    elif situacao == 'sem_comentario':
        query = query.filter(Questao.comentario_status != 'publicado')

    # Ordenação padrão: mais recentes primeiro e número crescente
    query = query.order_by(Questao.ano.desc(), Questao.numero.asc())

    # Paginação de 20 em 20
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    questoes_lista = pagination.items

    # Listas auxiliares para os filtros
    cursos = Curso.query.order_by(Curso.nome).all()
    anos = [r[0] for r in db.session.query(Questao.ano).distinct().order_by(Questao.ano.desc()).all()]
    areas = [r[0] for r in db.session.query(Questao.area).distinct().order_by(Questao.area).all()]

    return render_template(
        'admin/questoes.html',
        ativo='questoes',
        questoes=questoes_lista,
        pagination=pagination,
        total_cadastradas=total_cadastradas,
        total_anuladas=total_anuladas,
        total_sem_comentario=total_sem_comentario,
        cursos=cursos,
        anos=anos,
        areas=areas,
        busca=busca,
        curso_id=curso_id,
        ano=ano,
        area=area,
        situacao=situacao
    )


@admin_bp.route('/questoes/<int:id>/anular', methods=['POST'])
@requer_perfil('admin')
def toggle_anular_questao(id):
    """Inverte o estado de anulação de uma questão."""
    questao = db.session.get(Questao, id)
    if not questao:
        flash("Questão não encontrada.", "erro")
        return redirect(url_for('admin.questoes'))

    questao.anulada = not questao.anulada
    questao.atualizada_em = utc_now()
    db.session.commit()

    if questao.anulada:
        flash(f"Questão {questao.numero} do ENADE {questao.ano} marcada como anulada.", "sucesso")
    else:
        flash(f"Anulação da questão {questao.numero} do ENADE {questao.ano} desmarcada.", "sucesso")

    return redirect(request.referrer or url_for('admin.questoes'))


@admin_bp.route('/questoes/verificar-respostas/<int:id>')
@requer_perfil('admin')
def verificar_respostas_questao(id):
    """API para verificação de respostas antes da remoção (T13)."""
    questao = db.session.get(Questao, id)
    if not questao:
        return jsonify({'erro': 'Questão não encontrada.'}), 404

    count_estudo = RespostaEstudo.query.filter_by(questao_id=id).count()
    count_sim_q = SimuladoQuestao.query.filter_by(questao_id=id).count()
    count_sim_r = SimuladoResposta.query.filter_by(questao_id=id).count()
    total = count_estudo + count_sim_q + count_sim_r

    return jsonify({
        'id': questao.id,
        'numero': questao.numero,
        'ano': questao.ano,
        'tem_respostas': total > 0,
        'total_respostas': total
    })


@admin_bp.route('/questoes/<int:id>/remover', methods=['POST'])
@requer_perfil('admin')
def remover_questao(id):
    """
    Remove uma questão definitivamente.
    Bloqueia e rejeita caso a questão já tenha respostas associadas.
    """
    questao = db.session.get(Questao, id)
    if not questao:
        flash("Questão não encontrada.", "erro")
        return redirect(url_for('admin.questoes'))

    count_estudo = RespostaEstudo.query.filter_by(questao_id=id).count()
    count_sim_q = SimuladoQuestao.query.filter_by(questao_id=id).count()
    count_sim_r = SimuladoResposta.query.filter_by(questao_id=id).count()
    total_respostas = count_estudo + count_sim_q + count_sim_r

    if total_respostas > 0:
        flash("Esta questão já foi respondida por estudantes. Marque como anulada em vez de remover.", "erro")
        return redirect(url_for('admin.questoes')), 400

    num = questao.numero
    ano = questao.ano

    # Remove alternativas
    Alternativa.query.filter_by(questao_id=id).delete()

    # Remove arquivo de imagem físico se existir
    if questao.imagem_arquivo:
        try:
            caminho_img = os.path.join(current_app.instance_path, 'uploads', questao.imagem_arquivo)
            if os.path.exists(caminho_img):
                os.remove(caminho_img)
        except Exception:
            pass

    db.session.delete(questao)
    db.session.commit()

    flash(f"Questão {num} do ENADE {ano} removida definitivamente.", "sucesso")
    return redirect(url_for('admin.questoes'))


# ==============================================================================
# T14: Formulário de Questão (RF19, US10, RN02)
# ==============================================================================

@admin_bp.route('/questoes/nova', methods=['GET', 'POST'])
@requer_perfil('admin')
def nova_questao():
    """T14 - Cadastro de nova questão."""
    duplicar_id = request.args.get('duplicar', type=int)
    questao_duplicada = None
    if duplicar_id and request.method == 'GET':
        questao_duplicada = db.session.get(Questao, duplicar_id)

    cursos = Curso.query.order_by(Curso.nome).all()

    if request.method == 'POST':
        erros, questao_id = processar_salvar_questao(None)
        if not erros:
            flash("Questão cadastrada com sucesso!", "sucesso")
            return redirect(url_for('admin.questoes'))
        return render_template(
            'admin/questao_form.html',
            ativo='questoes',
            modo='nova',
            questao=None,
            cursos=cursos,
            erros=erros,
            dados=request.form
        ), 400

    # GET
    dados_iniciais = {}
    if questao_duplicada:
        dados_iniciais = {
            'curso_id': questao_duplicada.curso_id,
            'ano': questao_duplicada.ano,
            'numero': '',
            'componente': questao_duplicada.componente,
            'area': questao_duplicada.area,
            'tipo': questao_duplicada.tipo,
            'enunciado': questao_duplicada.enunciado,
            'gabarito_oficial': questao_duplicada.gabarito_oficial,
            'padrao_resposta': questao_duplicada.padrao_resposta or '',
            'anulada': '1' if questao_duplicada.anulada else '0'
        }
        for alt in questao_duplicada.alternativas:
            dados_iniciais[f'alt_{alt.letra}'] = alt.texto

    return render_template(
        'admin/questao_form.html',
        ativo='questoes',
        modo='nova',
        questao=None,
        cursos=cursos,
        erros=[],
        dados=dados_iniciais
    )


@admin_bp.route('/questoes/<int:id>/editar', methods=['GET', 'POST'])
@requer_perfil('admin')
def editar_questao(id):
    """T14 - Edição de questão existente."""
    questao = db.session.get(Questao, id)
    if not questao:
        flash("Questão não encontrada.", "erro")
        return redirect(url_for('admin.questoes'))

    cursos = Curso.query.order_by(Curso.nome).all()

    if request.method == 'POST':
        erros, _ = processar_salvar_questao(questao)
        if not erros:
            flash("Questão atualizada com sucesso!", "sucesso")
            return redirect(url_for('admin.questoes'))
        return render_template(
            'admin/questao_form.html',
            ativo='questoes',
            modo='editar',
            questao=questao,
            cursos=cursos,
            erros=erros,
            dados=request.form
        ), 400

    # Prepara dados da questão existente
    dados = {
        'curso_id': questao.curso_id,
        'ano': questao.ano,
        'numero': questao.numero,
        'componente': questao.componente,
        'area': questao.area,
        'tipo': questao.tipo,
        'enunciado': questao.enunciado,
        'imagem_descricao': questao.imagem_descricao or '',
        'gabarito_oficial': questao.gabarito_oficial,
        'padrao_resposta': questao.padrao_resposta or '',
        'anulada': '1' if questao.anulada else '0'
    }
    for alt in questao.alternativas:
        dados[f'alt_{alt.letra}'] = alt.texto

    return render_template(
        'admin/questao_form.html',
        ativo='questoes',
        modo='editar',
        questao=questao,
        cursos=cursos,
        erros=[],
        dados=dados
    )


def processar_salvar_questao(questao_existente=None):
    """Valida e persiste questão (nova ou edição) conforme RN02 e regras de negócio."""
    erros = []
    form = request.form

    curso_id = form.get('curso_id', type=int)
    ano = form.get('ano', type=int)
    numero = form.get('numero', type=int)
    componente = form.get('componente', '').strip()
    area = form.get('area', '').strip()
    tipo = form.get('tipo', '').strip()
    enunciado = form.get('enunciado', '').strip()
    anulada = bool(form.get('anulada'))
    gabarito_oficial = form.get('gabarito_oficial', '').strip().upper()
    padrao_resposta = form.get('padrao_resposta', '').strip()
    imagem_descricao = form.get('imagem_descricao', '').strip()
    remover_imagem = bool(form.get('remover_imagem'))

    # RN02: Toda questão tem ano, componente, área, tipo e gabarito oficial.
    # Curso é obrigatório somente para o Componente Específico.
    if componente == 'especifico':
        if not curso_id:
            erros.append({'campo': 'curso_id', 'mensagem': 'Selecione o curso para questões do Componente Específico.'})
    else:
        curso_id = None

    if not ano:
        erros.append({'campo': 'ano', 'mensagem': 'Informe o ano do ENADE.'})
    elif ano < 1990 or ano > 2100:
        erros.append({'campo': 'ano', 'mensagem': 'Ano inválido.'})

    if not numero or numero <= 0:
        erros.append({'campo': 'numero', 'mensagem': 'Informe um número de questão válido.'})

    if componente not in ('formacao_geral', 'especifico'):
        erros.append({'campo': 'componente', 'mensagem': 'Selecione o componente (Formação Geral ou Componente Específico).'})

    if not area:
        erros.append({'campo': 'area', 'mensagem': 'Informe a área de conhecimento.'})

    if tipo not in ('objetiva', 'discursiva'):
        erros.append({'campo': 'tipo', 'mensagem': 'Selecione o tipo da questão (Objetiva ou Discursiva).'})

    if not enunciado:
        erros.append({'campo': 'enunciado', 'mensagem': 'O enunciado da questão é obrigatório.'})

    # Validações específicas por tipo
    alternativas_texto = {}
    if tipo == 'objetiva':
        if not gabarito_oficial or gabarito_oficial not in ('A', 'B', 'C', 'D', 'E'):
            erros.append({'campo': 'gabarito_oficial', 'mensagem': 'Selecione o gabarito oficial (A–E).'})
        for letra in ('A', 'B', 'C', 'D', 'E'):
            t = form.get(f'alt_{letra}', '').strip()
            alternativas_texto[letra] = t
            if not t:
                erros.append({'campo': f'alt_{letra}', 'mensagem': f'Preencha o texto da alternativa {letra}.'})
    elif tipo == 'discursiva':
        gabarito_oficial = 'DISCURSIVA'
        if not padrao_resposta:
            erros.append({'campo': 'padrao_resposta', 'mensagem': 'Informe o padrão de resposta esperado pelo INEP.'})

    # Restrição de unicidade
    if ano and numero:
        if componente == 'formacao_geral':
            q_dup = Questao.query.filter_by(ano=ano, componente='formacao_geral', numero=numero).first()
            if q_dup and (not questao_existente or q_dup.id != questao_existente.id):
                erros.append({'campo': 'numero', 'mensagem': f'Já existe uma questão de Formação Geral número {numero} no ENADE {ano}.'})
        elif curso_id:
            q_dup = Questao.query.filter_by(ano=ano, curso_id=curso_id, numero=numero).first()
            if q_dup and (not questao_existente or q_dup.id != questao_existente.id):
                erros.append({'campo': 'numero', 'mensagem': f'Já existe uma questão de número {numero} no ENADE {ano} para este curso.'})

    # Upload de imagem opcional (PNG, JPG até 2MB)
    arquivo_imagem = request.files.get('imagem')
    nome_arquivo_salvo = None

    if arquivo_imagem and arquivo_imagem.filename:
        if not allowed_file(arquivo_imagem.filename):
            erros.append({'campo': 'imagem', 'mensagem': 'Formato de imagem inválido. Use apenas PNG ou JPG.'})
        else:
            # Checa tamanho lendo bytes
            arquivo_imagem.seek(0, os.SEEK_END)
            tamanho = arquivo_imagem.tell()
            arquivo_imagem.seek(0)
            if tamanho > MAX_FILE_SIZE:
                erros.append({'campo': 'imagem', 'mensagem': 'O arquivo de imagem deve ter no máximo 2MB.'})
            elif not imagem_descricao:
                erros.append({'campo': 'imagem_descricao', 'mensagem': 'A descrição da imagem (acessibilidade) é obrigatória ao anexar uma imagem.'})
            else:
                uploads_dir = os.path.join(current_app.instance_path, 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                ext = arquivo_imagem.filename.rsplit('.', 1)[1].lower()
                nome_arquivo_salvo = f"{uuid.uuid4().hex}.{ext}"
                caminho_destino = os.path.join(uploads_dir, nome_arquivo_salvo)
                arquivo_imagem.save(caminho_destino)

    if erros:
        # Se salvou imagem temporária e deu erro em outro campo, remove arquivo
        if nome_arquivo_salvo:
            try:
                os.remove(os.path.join(current_app.instance_path, 'uploads', nome_arquivo_salvo))
            except Exception:
                pass
        return erros, None

    # Persistência
    if questao_existente:
        q = questao_existente
        q.curso_id = curso_id
        q.ano = ano
        q.numero = numero
        q.componente = componente
        q.area = area
        q.tipo = tipo
        q.enunciado = enunciado
        q.anulada = anulada
        q.gabarito_oficial = gabarito_oficial
        q.padrao_resposta = padrao_resposta if tipo == 'discursiva' else None
        q.atualizada_em = utc_now()

        if remover_imagem:
            if q.imagem_arquivo:
                try:
                    os.remove(os.path.join(current_app.instance_path, 'uploads', q.imagem_arquivo))
                except Exception:
                    pass
            q.imagem_arquivo = None
            q.imagem_descricao = None
        elif nome_arquivo_salvo:
            if q.imagem_arquivo:
                try:
                    os.remove(os.path.join(current_app.instance_path, 'uploads', q.imagem_arquivo))
                except Exception:
                    pass
            q.imagem_arquivo = nome_arquivo_salvo
            q.imagem_descricao = imagem_descricao
        elif imagem_descricao:
            q.imagem_descricao = imagem_descricao

        if tipo == 'objetiva':
            # Atualiza alternativas
            for alt in q.alternativas:
                if alt.letra in alternativas_texto:
                    alt.texto = alternativas_texto[alt.letra]
            # Se faltar alguma alternativa, cria
            letras_existentes = {alt.letra for alt in q.alternativas}
            for letra, texto in alternativas_texto.items():
                if letra not in letras_existentes:
                    db.session.add(Alternativa(questao_id=q.id, letra=letra, texto=texto))
        else:
            # Se passou a ser discursiva, limpa alternativas
            Alternativa.query.filter_by(questao_id=q.id).delete()

    else:
        # Nova questão
        q = Questao(
            curso_id=curso_id,
            ano=ano,
            numero=numero,
            componente=componente,
            area=area,
            tipo=tipo,
            enunciado=enunciado,
            imagem_arquivo=nome_arquivo_salvo,
            imagem_descricao=imagem_descricao if nome_arquivo_salvo else None,
            anulada=anulada,
            gabarito_oficial=gabarito_oficial,
            padrao_resposta=padrao_resposta if tipo == 'discursiva' else None,
            comentario_status='rascunho',
            criada_em=utc_now(),
            atualizada_em=utc_now()
        )
        db.session.add(q)
        db.session.flush()

        if tipo == 'objetiva':
            for letra in ('A', 'B', 'C', 'D', 'E'):
                alt = Alternativa(
                    questao_id=q.id,
                    letra=letra,
                    texto=alternativas_texto[letra]
                )
                db.session.add(alt)

    db.session.commit()
    return [], q.id


# ==============================================================================
# T15: Editor de Comentário e Fila de Comentários (RF20, US11)
# ==============================================================================

@admin_bp.route('/comentarios')
@requer_perfil('admin', 'professor')
def comentarios():
    """T15 - Fila de questões sem comentário publicado para priorização."""
    curso_id = request.args.get('curso', type=int)
    ano = request.args.get('ano', type=int)
    page = request.args.get('page', 1, type=int)

    query = Questao.query.filter(Questao.comentario_status != 'publicado')

    if curso_id:
        query = query.filter(Questao.curso_id == curso_id)
    if ano:
        query = query.filter(Questao.ano == ano)

    query = query.order_by(Questao.ano.desc(), Questao.numero.asc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    cursos = Curso.query.order_by(Curso.nome).all()
    anos = [r[0] for r in db.session.query(Questao.ano).distinct().order_by(Questao.ano.desc()).all()]

    return render_template(
        'admin/comentarios_lista.html',
        ativo='comentarios',
        questoes=pagination.items,
        pagination=pagination,
        cursos=cursos,
        anos=anos,
        curso_id=curso_id,
        ano=ano
    )


@admin_bp.route('/questoes/<int:id>/comentario', methods=['GET', 'POST'])
@requer_perfil('admin', 'professor')
def editar_comentario(id):
    """T15 - Editor de gabarito comentado com prévia ao vivo."""
    questao = db.session.get(Questao, id)
    if not questao:
        flash("Questão não encontrada.", "erro")
        return redirect(url_for('admin.questoes'))

    if request.method == 'POST':
        action = request.form.get('action')  # 'rascunho' ou 'publicar'
        comentario_correta = request.form.get('comentario_correta', '').strip()
        comentario_fonte = request.form.get('comentario_fonte', '').strip()

        # Determina status
        if action == 'publicar':
            novo_status = 'publicado'
        elif action == 'rascunho':
            novo_status = 'rascunho'
        else:
            novo_status = request.form.get('comentario_status', 'rascunho')

        # Validação: comentário da correta é obrigatório ao publicar
        if novo_status == 'publicado' and not comentario_correta:
            flash("O comentário da alternativa correta / padrão de resposta é obrigatório para publicação.", "erro")
            return render_template(
                'admin/comentario_editor.html',
                ativo='comentarios',
                questao=questao,
                comentario_correta=comentario_correta,
                comentario_fonte=comentario_fonte,
                status_atual=novo_status,
                erro_campo='comentario_correta'
            ), 400

        questao.comentario_correta = comentario_correta
        questao.comentario_fonte = comentario_fonte or None
        questao.comentario_status = novo_status
        questao.comentario_atualizado_em = utc_now()
        questao.comentario_atualizado_por = current_user.id

        # Atualiza comentários das alternativas incorretas (se objetiva)
        if questao.tipo == 'objetiva':
            for alt in questao.alternativas:
                if alt.letra != questao.gabarito_oficial:
                    alt.comentario_erro = request.form.get(f'comentario_erro_{alt.letra}', '').strip() or None

        db.session.commit()

        if novo_status == 'publicado':
            flash(f"Comentário da questão {questao.numero} publicado com sucesso! Estudantes já podem visualizá-lo.", "sucesso")
        else:
            flash(f"Comentário da questão {questao.numero} salvo como rascunho.", "sucesso")

        return redirect(url_for('admin.questoes'))

    return render_template(
        'admin/comentario_editor.html',
        ativo='comentarios',
        questao=questao,
        comentario_correta=questao.comentario_correta or '',
        comentario_fonte=questao.comentario_fonte or '',
        status_atual=questao.comentario_status
    )


# ==============================================================================
# Importação de Edição em CSV (RNF10)
# ==============================================================================

CSV_HEADERS_ESPERADOS = [
    'ano', 'curso', 'numero', 'componente', 'area', 'tipo',
    'enunciado', 'alt_a', 'alt_b', 'alt_c', 'alt_d', 'alt_e',
    'gabarito', 'padrao_resposta', 'anulada'
]


@admin_bp.route('/questoes/importar', methods=['GET', 'POST'])
@requer_perfil('admin')
def importar_questoes():
    """
    Importação em 2 etapas de questões via CSV:
    Etapa 1: Upload e validação total (RN02 + unicidade). Se houver erro, exibe tabela sem salvar.
    Etapa 2: Confirmação e commit atômico de todas as questões.
    """
    if request.method == 'POST':
        # Etapa 2: Confirmação da importação prévia
        if request.form.get('confirmar') == '1':
            questoes_validadas = session.get('csv_import_questoes')
            if not questoes_validadas:
                flash("Nenhum dado de importação pendente. Envie o arquivo novamente.", "aviso")
                return redirect(url_for('admin.importar_questoes'))

            try:
                # Transação única atômica
                cursos_cache = {c.nome.lower(): c.id for c in Curso.query.all()}

                for item in questoes_validadas:
                    curso_id = None
                    if item['componente'] == 'especifico' and item.get('curso'):
                        curso_id = cursos_cache.get(item['curso'].strip().lower())
                    q = Questao(
                        ano=item['ano'],
                        curso_id=curso_id,
                        numero=item['numero'],
                        componente=item['componente'],
                        area=item['area'],
                        tipo=item['tipo'],
                        enunciado=item['enunciado'],
                        gabarito_oficial=item['gabarito'],
                        padrao_resposta=item.get('padrao_resposta'),
                        anulada=item['anulada'],
                        comentario_status='rascunho',
                        criada_em=utc_now(),
                        atualizada_em=utc_now()
                    )
                    db.session.add(q)
                    db.session.flush()

                    if item['tipo'] == 'objetiva':
                        for letra in ('A', 'B', 'C', 'D', 'E'):
                            alt = Alternativa(
                                questao_id=q.id,
                                letra=letra,
                                texto=item['alternativas'][letra]
                            )
                            db.session.add(alt)

                db.session.commit()
                total_importado = len(questoes_validadas)
                session.pop('csv_import_questoes', None)
                flash(f"Sucesso! {total_importado} questões importadas como rascunho de comentário.", "sucesso")
                return redirect(url_for('admin.questoes'))

            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao salvar no banco de dados: {str(e)}", "erro")
                return redirect(url_for('admin.importar_questoes'))

        # Etapa 1: Processa arquivo CSV enviado
        arquivo = request.files.get('arquivo_csv')
        if not arquivo or not arquivo.filename:
            flash("Selecione um arquivo CSV para importar.", "erro")
            return redirect(url_for('admin.importar_questoes'))

        if not arquivo.filename.lower().endswith('.csv'):
            flash("O arquivo deve ter extensão .csv.", "erro")
            return redirect(url_for('admin.importar_questoes'))

        conteudo_bytes = arquivo.read()
        try:
            conteudo_texto = conteudo_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                conteudo_texto = conteudo_bytes.decode('latin-1')
            except Exception:
                flash("Não foi possível ler o arquivo. Verifique se a codificação é UTF-8.", "erro")
                return redirect(url_for('admin.importar_questoes'))

        leitor = csv.reader(io.StringIO(conteudo_texto))
        linhas = list(leitor)

        if not linhas:
            flash("O arquivo CSV está vazio.", "erro")
            return redirect(url_for('admin.importar_questoes'))

        headers_arquivo = [h.strip().lower() for h in linhas[0]]
        cabecalho_valido = all(h in headers_arquivo for h in ['ano', 'curso', 'numero', 'componente', 'area', 'tipo', 'enunciado', 'gabarito'])

        if not cabecalho_valido:
            flash("Cabeçalho CSV inválido. Utilize o modelo de exemplo para referência.", "erro")
            return redirect(url_for('admin.importar_questoes'))

        # Mapeia cursos existentes
        cursos_banco = {c.nome.lower(): c.id for c in Curso.query.all()}

        erros_linhas = []
        questoes_validas = []
        chaves_no_csv = set()

        idx_map = {h: i for i, h in enumerate(headers_arquivo)}

        def get_val(row, col_name, default=''):
            idx = idx_map.get(col_name)
            return row[idx].strip() if (idx is not None and idx < len(row)) else default

        for num_linha, row in enumerate(linhas[1:], start=2):
            if not row or all(not cell.strip() for cell in row):
                continue  # Pula linhas em branco

            erros_da_linha = []
            ano_str = get_val(row, 'ano')
            curso_str = get_val(row, 'curso')
            numero_str = get_val(row, 'numero')
            componente = get_val(row, 'componente').lower()
            area = get_val(row, 'area')
            tipo = get_val(row, 'tipo').lower()
            enunciado = get_val(row, 'enunciado')
            gabarito = get_val(row, 'gabarito').upper()
            padrao = get_val(row, 'padrao_resposta')
            anulada_str = get_val(row, 'anulada').lower()
            anulada = anulada_str in ('1', 'true', 'sim', 's', 'v')

            # Validações
            try:
                ano_val = int(ano_str)
                if ano_val < 1990 or ano_val > 2100:
                    erros_da_linha.append("Ano inválido.")
            except ValueError:
                erros_da_linha.append("Ano deve ser numérico.")
                ano_val = None

            if componente == 'especifico':
                if not curso_str:
                    erros_da_linha.append("Curso não informado para o Componente Específico.")
                elif curso_str.lower() not in cursos_banco:
                    erros_da_linha.append(f"Curso '{curso_str}' não encontrado no sistema.")
            else:
                curso_str = curso_str or "Formação Geral (Comum)"

            try:
                numero_val = int(numero_str)
                if numero_val <= 0:
                    erros_da_linha.append("Número da questão deve ser positivo.")
            except ValueError:
                erros_da_linha.append("Número da questão deve ser numérico.")
                numero_val = None

            if componente not in ('formacao_geral', 'especifico'):
                erros_da_linha.append("Componente deve ser 'formacao_geral' ou 'especifico'.")

            if not area:
                erros_da_linha.append("Área de conhecimento não informada.")

            if tipo not in ('objetiva', 'discursiva'):
                erros_da_linha.append("Tipo deve ser 'objetiva' ou 'discursiva'.")

            if not enunciado:
                erros_da_linha.append("Enunciado não informado.")

            alternativas = {}
            if tipo == 'objetiva':
                if gabarito not in ('A', 'B', 'C', 'D', 'E'):
                    erros_da_linha.append(f"Gabarito '{gabarito}' inválido para objetiva (deve ser A, B, C, D ou E).")
                for letra in ('A', 'B', 'C', 'D', 'E'):
                    alt_texto = get_val(row, f'alt_{letra.lower()}')
                    alternativas[letra] = alt_texto
                    if not alt_texto:
                        erros_da_linha.append(f"Texto da alternativa {letra} não informado.")
            elif tipo == 'discursiva':
                gabarito = 'DISCURSIVA'
                if not padrao:
                    erros_da_linha.append("Padrão de resposta esperado não informado para questão discursiva.")

            # Unicidade
            if ano_val and numero_val:
                if componente == 'formacao_geral':
                    chave = (ano_val, 'formacao_geral', numero_val)
                    if chave in chaves_no_csv:
                        erros_da_linha.append(f"Questão de Formação Geral repetida no arquivo CSV (Ano {ano_val}, nº {numero_val}).")
                    else:
                        chaves_no_csv.add(chave)

                    existente = Questao.query.filter_by(ano=ano_val, componente='formacao_geral', numero=numero_val).first()
                    if existente:
                        erros_da_linha.append(f"Já existe questão cadastrada no sistema com Ano {ano_val} (Formação Geral, nº {numero_val}).")
                else:
                    if curso_str and curso_str.lower() in cursos_banco:
                        chave = (ano_val, curso_str.lower(), numero_val)
                        if chave in chaves_no_csv:
                            erros_da_linha.append(f"Questão repetida no arquivo CSV (Ano {ano_val}, {curso_str}, nº {numero_val}).")
                        else:
                            chaves_no_csv.add(chave)

                        c_id = cursos_banco.get(curso_str.lower())
                        if c_id:
                            existente = Questao.query.filter_by(ano=ano_val, curso_id=c_id, numero=numero_val).first()
                            if existente:
                                erros_da_linha.append(f"Já existe questão cadastrada no sistema com Ano {ano_val}, {curso_str}, nº {numero_val}.")

            if erros_da_linha:
                erros_linhas.append({
                    'linha': num_linha,
                    'identificador': f"ENADE {ano_str} · {curso_str} · Questão {numero_str}",
                    'erros': erros_da_linha
                })
            else:
                questoes_validas.append({
                    'ano': ano_val,
                    'curso': curso_str,
                    'numero': numero_val,
                    'componente': componente,
                    'area': area,
                    'tipo': tipo,
                    'enunciado': enunciado,
                    'alternativas': alternativas,
                    'gabarito': gabarito,
                    'padrao_resposta': padrao if tipo == 'discursiva' else None,
                    'anulada': anulada
                })

        if erros_linhas:
            # Rejeita todas as questões e mostra tabela de erros
            session.pop('csv_import_questoes', None)
            return render_template(
                'admin/importar_csv.html',
                ativo='questoes',
                erros_linhas=erros_linhas,
                total_linhas_processadas=len(linhas) - 1,
                questoes_validas=None
            )

        # Todas as linhas são válidas! Exibe pré-visualização para confirmação
        session['csv_import_questoes'] = questoes_validas
        return render_template(
            'admin/importar_csv.html',
            ativo='questoes',
            erros_linhas=None,
            questoes_validas=questoes_validas
        )

    # GET
    session.pop('csv_import_questoes', None)
    return render_template(
        'admin/importar_csv.html',
        ativo='questoes',
        erros_linhas=None,
        questoes_validas=None
    )


@admin_bp.route('/questoes/exemplo.csv')
@requer_perfil('admin')
def baixar_exemplo_csv():
    """Gera e retorna um CSV de exemplo preenchido com duas questões para referência."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_HEADERS_ESPERADOS)
    writer.writerow([
        2023, "Ciência da Computação", 1, "formacao_geral", "Interpretação de texto", "objetiva",
        "Enunciado da questão objetiva de exemplo.", "Texto alternativa A", "Texto alternativa B",
        "Texto alternativa C", "Texto alternativa D", "Texto alternativa E", "B", "", "0"
    ])
    writer.writerow([
        2023, "Ciência da Computação", 9, "formacao_geral", "Tecnologia e Sociedade", "discursiva",
        "Enunciado da questão discursiva de exemplo com estudo de caso.", "", "", "", "", "",
        "DISCURSIVA", "Padrão de resposta esperado pelo INEP avaliando clareza e argumentação.", "0"
    ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=exemplo_importacao_enade.csv"}
    )


# ==============================================================================
# Moderação do Fórum (Em breve - US15 P2)
# ==============================================================================

@admin_bp.route('/moderacao')
@requer_perfil('admin')
def moderacao():
    """Página 'Em construção' para moderação do fórum."""
    return render_template('admin/moderacao_em_construcao.html', ativo='moderacao')
