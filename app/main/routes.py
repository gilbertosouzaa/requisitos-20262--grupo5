import os
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, request, jsonify, flash
from flask_login import current_user
from app.main import main_bp
from app.auth import login_required
from app.extensions import db
from app.models import Questao, Curso, Alternativa, RespostaEstudo, Simulado, SimuladoQuestao, SimuladoResposta, utc_now
from app.services.desempenho import (
    calcular_resumo_geral,
    calcular_evolucao_semanal,
    calcular_mudancas_4_semanas,
    obter_historico_simulados,
    obter_simulado_em_andamento,
    obter_tendencia_inicio,
    formatar_tempo_legivel,
)

def formatar_duracao(segundos: int) -> str:
    """Formata duração em segundos usando o padrão legível unificado."""
    return formatar_tempo_legivel(segundos)


def obter_respostas_mais_recentes(usuario_id):
    """Retorna um dicionário {questao_id: RespostaEstudo} com a resposta mais recente do usuário."""
    subq = db.session.query(
        RespostaEstudo.questao_id,
        db.func.max(RespostaEstudo.id).label('max_id')
    ).filter(RespostaEstudo.usuario_id == usuario_id).group_by(RespostaEstudo.questao_id).subquery()

    ultimas = db.session.query(RespostaEstudo).join(
        subq, RespostaEstudo.id == subq.c.max_id
    ).all()
    return {r.questao_id: r for r in ultimas}


def filtrar_questoes_query(args, usuario=None):
    """Aplica os filtros da query string retornando a query filtrada e dados auxiliares."""
    curso_param = args.get('curso')
    curso_id = None
    if curso_param is not None:
        if curso_param not in ('', 'todos', '0'):
            try:
                curso_id = int(curso_param)
            except ValueError:
                curso_id = None
        else:
            curso_id = None  # Explicitamente "Todos os cursos"
    else:
        # Padrão: curso do estudante autenticado (premissa P7)
        if usuario and usuario.is_authenticated and usuario.curso_id:
            curso_id = usuario.curso_id
        else:
            curso_id = None

    anos = args.getlist('ano', type=int)
    componente = args.get('componente', 'todos')
    areas = args.getlist('area')
    tipos = args.getlist('tipo')
    situacoes = args.getlist('situacao') if (usuario and usuario.is_authenticated) else []
    busca = args.get('q', '').strip()
    ordem = args.get('ordem', 'recentes')

    query = Questao.query

    # Filtro Curso:
    # Formação Geral é comum a todos os cursos numa mesma edição do ENADE.
    # Se curso_id foi especificado:
    # - Se o curso possui questões específicas cadastradas: traz questões de Formação Geral OU do Componente Específico desse curso.
    # - Se o curso NÃO possui questões específicas cadastradas e componente != 'formacao_geral': filtra por curso_id (resultando em 0 questões),
    #   exibindo o estado vazio com orientação e botão 'Ver Formação Geral'.
    if curso_id:
        tem_especifico = (Questao.query.filter_by(curso_id=curso_id, componente='especifico').first() is not None)
        if componente == 'formacao_geral':
            query = query.filter(Questao.componente == 'formacao_geral')
        elif componente == 'especifico':
            query = query.filter(Questao.componente == 'especifico', Questao.curso_id == curso_id)
        else:  # componente == 'todos'
            if tem_especifico:
                query = query.filter(
                    db.or_(
                        Questao.componente == 'formacao_geral',
                        Questao.curso_id == curso_id
                    )
                )
            else:
                query = query.filter(Questao.curso_id == curso_id)
    else:
        if componente in ('formacao_geral', 'especifico'):
            query = query.filter(Questao.componente == componente)

    # Filtro Ano
    if anos:
        query = query.filter(Questao.ano.in_(anos))

    # Filtro Área
    if areas:
        query = query.filter(Questao.area.in_(areas))

    # Filtro Tipo
    if tipos:
        query = query.filter(Questao.tipo.in_(tipos))

    # Filtro Busca por texto
    if busca:
        query = query.filter(Questao.enunciado.ilike(f"%{busca}%"))

    # Filtro Situação (somente usuário logado)
    if usuario and usuario.is_authenticated and situacoes:
        respostas_map = obter_respostas_mais_recentes(usuario.id)
        respondidas_ids = set(respostas_map.keys())
        erradas_ids = {qid for qid, r in respostas_map.items() if r.correta is False}

        if 'nao_respondidas' in situacoes and 'errei' in situacoes:
            # Não respondidas OU que errou na mais recente
            # Busca todos os ids de questoes do curso
            query = query.filter(
                (~Questao.id.in_(respondidas_ids)) | (Questao.id.in_(erradas_ids))
            )
        elif 'nao_respondidas' in situacoes:
            if respondidas_ids:
                query = query.filter(~Questao.id.in_(respondidas_ids))
        elif 'errei' in situacoes:
            if erradas_ids:
                query = query.filter(Questao.id.in_(erradas_ids))
            else:
                # Nenhuma questão errada: força lista vazia
                query = query.filter(db.false())

    # Ordenação
    if ordem == 'numero':
        query = query.order_by(Questao.numero.asc(), Questao.ano.desc())
    else:
        query = query.order_by(Questao.ano.desc(), Questao.numero.asc())

    return query, {
        'curso_id': curso_id,
        'anos': anos,
        'componente': componente,
        'areas': areas,
        'tipos': tipos,
        'situacoes': situacoes,
        'busca': busca,
        'ordem': ordem
    }


@main_bp.route('/')
def landing():
    """T01 - Landing Page. Usuário logado é redirecionado para /inicio ou /admin/questoes."""
    if current_user.is_authenticated:
        if current_user.perfil == 'admin':
            return redirect(url_for('admin.questoes'))
        return redirect(url_for('main.inicio'))
    return render_template('main/landing.html')


@main_bp.route('/inicio')
@login_required
def inicio():
    """T05 completo - Início do estudante logado (RNF01, RN08, RN03, RN05)."""
    simulado_em_andamento = obter_simulado_em_andamento(current_user)
    resumo = calcular_resumo_geral(current_user, origem='tudo', componente='todos')
    tem_desempenho = resumo['total_respondidas'] > 0
    desempenho_data = {}
    if tem_desempenho:
        desempenho_data = {
            'percentual_geral': resumo['percentual_geral'],
            'total_respondidas': resumo['total_respondidas'],
            'revisar_primeiro': resumo['revisar_primeiro'],
        }

    tendencia = obter_tendencia_inicio(current_user)

    historico_1 = obter_historico_simulados(current_user, limite=1)
    ultimo_simulado = None
    if historico_1['itens']:
        ult = historico_1['itens'][0]
        ultimo_simulado = {
            'id': ult['id'],
            'titulo': ult['tipo_label'].replace(' · ENADE', ' ENADE'),
            'percentual': ult['percentual'],
            'acertos': ult['acertos'],
            'respondidas': ult['respondidas'],
            'tempo_gasto': ult['tempo_utilizado'],
            'data': ult['data'],
            'url': ult['url'],
        }

    return render_template(
        'main/inicio.html',
        ativo='inicio',
        simulado_em_andamento=simulado_em_andamento,
        tem_desempenho=tem_desempenho,
        desempenho=desempenho_data,
        tendencia=tendencia,
        ultimo_simulado=ultimo_simulado
    )


@main_bp.route('/questoes')
def questoes():
    """T06 - Banco de questões com filtros e busca (RF04, US04, RN01)."""
    cursos = Curso.query.order_by(Curso.nome.asc()).all()
    anos_disponiveis = [r[0] for r in db.session.query(Questao.ano).distinct().order_by(Questao.ano.desc()).all()]

    query, filtros = filtrar_questoes_query(request.args, current_user)

    if filtros['curso_id']:
        areas_disponiveis = [
            r[0] for r in db.session.query(Questao.area)
            .filter(db.or_(Questao.componente == 'formacao_geral', Questao.curso_id == filtros['curso_id']))
            .distinct()
            .order_by(Questao.area.asc())
            .all()
        ]
    else:
        areas_disponiveis = [r[0] for r in db.session.query(Questao.area).distinct().order_by(Questao.area.asc()).all()]

    pagina = request.args.get('pagina', 1, type=int)
    paginacao = query.paginate(page=pagina, per_page=10, error_out=False)

    # Status das questões para o usuário logado
    status_map = {}
    if current_user.is_authenticated:
        respostas_map = obter_respostas_mais_recentes(current_user.id)
        for q in paginacao.items:
            r = respostas_map.get(q.id)
            if not r:
                status_map[q.id] = {'texto': 'Não respondida', 'classe': 'nao-respondida'}
            elif r.correta is True:
                status_map[q.id] = {'texto': 'Acertou', 'classe': 'acertou'}
            elif r.correta is False:
                status_map[q.id] = {'texto': 'Errou', 'classe': 'errou'}
            else:
                status_map[q.id] = {'texto': 'Respondida', 'classe': 'respondida'}

    # Monta texto do resumo de filtros ativos
    filtros_ativos = []
    curso_selecionado = next((c for c in cursos if c.id == filtros['curso_id']), None)
    if curso_selecionado:
        filtros_ativos.append(curso_selecionado.nome)
    elif request.args.get('curso') == 'todos':
        filtros_ativos.append('Todos os cursos')

    for a in filtros['anos']:
        filtros_ativos.append(str(a))
    if filtros['componente'] == 'formacao_geral':
        filtros_ativos.append('Formação Geral')
    elif filtros['componente'] == 'especifico':
        filtros_ativos.append('Componente Específico')
    for ar in filtros['areas']:
        filtros_ativos.append(ar)
    for tp in filtros['tipos']:
        filtros_ativos.append('Objetiva' if tp == 'objetiva' else 'Discursiva')
    for sit in filtros['situacoes']:
        filtros_ativos.append('Não respondidas' if sit == 'nao_respondidas' else 'Errei')
    if filtros['busca']:
        filtros_ativos.append(f'"{filtros["busca"]}"')

    resumo_filtros = " · ".join(filtros_ativos) if filtros_ativos else ""

    # Estado vazio customizado (item 4 do requisito):
    # Quando o filtro de curso não tiver nenhuma questão cadastrada
    sem_questoes_especificas = False
    if curso_selecionado and paginacao.total == 0:
        total_especifico_curso = Questao.query.filter_by(curso_id=curso_selecionado.id, componente='especifico').count()
        if total_especifico_curso == 0 or filtros['componente'] == 'especifico':
            sem_questoes_especificas = True

    return render_template(
        'main/questoes.html',
        ativo='questoes',
        cursos=cursos,
        curso_selecionado=curso_selecionado,
        sem_questoes_especificas=sem_questoes_especificas,
        anos_disponiveis=anos_disponiveis,
        areas_disponiveis=areas_disponiveis,
        filtros=filtros,
        paginacao=paginacao,
        questoes=paginacao.items,
        status_map=status_map,
        resumo_filtros=resumo_filtros
    )


@main_bp.route('/questoes/<int:id>', methods=['GET'])
def detalhe_questao(id):
    """T07a e T07b - Questão em modo estudo (RF05, RF06, RF08, US05, US06)."""
    questao = db.session.get(Questao, id)
    if not questao:
        return render_template('main/em_construcao.html', titulo="Questão não encontrada", subtitulo="A questão solicitada não existe."), 404

    # Navegação Anterior / Próxima preservando os filtros atuais
    query_filtrada, _ = filtrar_questoes_query(request.args, current_user)
    ids_no_filtro = [row[0] for row in query_filtrada.with_entities(Questao.id).all()]

    anterior_id = None
    proxima_id = None
    posicao = None
    total_no_filtro = len(ids_no_filtro)

    if questao.id in ids_no_filtro:
        idx = ids_no_filtro.index(questao.id)
        posicao = idx + 1
        if idx > 0:
            anterior_id = ids_no_filtro[idx - 1]
        if idx < total_no_filtro - 1:
            proxima_id = ids_no_filtro[idx + 1]

    # Verifica se há resposta mais recente para exibir no modo T07b
    ultima_resposta = None
    if current_user.is_authenticated:
        ultima_resposta = RespostaEstudo.query.filter_by(
            usuario_id=current_user.id,
            questao_id=questao.id
        ).order_by(RespostaEstudo.respondida_em.desc(), RespostaEstudo.id.desc()).first()

    modo_correcao = (ultima_resposta is not None) or (request.args.get('corrigida') == '1')

    # Preserva query string para links de paginação e volta
    filtros_query = request.query_string.decode('utf-8')

    return render_template(
        'main/questao.html',
        ativo='questoes',
        questao=questao,
        modo_correcao=modo_correcao,
        ultima_resposta=ultima_resposta,
        posicao=posicao,
        total_no_filtro=total_no_filtro,
        anterior_id=anterior_id,
        proxima_id=proxima_id,
        filtros_query=filtros_query
    )


@main_bp.route('/questoes/<int:id>/responder', methods=['POST'])
def responder_questao_form(id):
    """Fallback de submissão tradicional de formulário (sem JavaScript)."""
    questao = db.session.get(Questao, id)
    if not questao:
        return redirect(url_for('main.questoes'))

    if not current_user.is_authenticated:
        flash("Faça login para salvar suas respostas e ver a correção.", "aviso")
        return redirect(url_for('auth.login', next=request.path))

    alternativa = request.form.get('alternativa')
    texto_resposta = request.form.get('texto_resposta', '').strip()

    if questao.tipo == 'objetiva':
        if not alternativa or alternativa.upper() not in ('A', 'B', 'C', 'D', 'E'):
            flash("Selecione uma alternativa antes de confirmar.", "aviso")
            return redirect(url_for('main.detalhe_questao', id=id))

        correta = (alternativa.upper() == questao.gabarito_oficial.upper())
        resp = RespostaEstudo(
            usuario_id=current_user.id,
            questao_id=questao.id,
            alternativa_marcada=alternativa.upper(),
            correta=correta
        )
    else:
        if not texto_resposta:
            flash("Escreva sua resposta antes de enviar.", "aviso")
            return redirect(url_for('main.detalhe_questao', id=id))

        resp = RespostaEstudo(
            usuario_id=current_user.id,
            questao_id=questao.id,
            texto_resposta=texto_resposta,
            correta=None
        )

    db.session.add(resp)
    db.session.commit()

    return redirect(url_for('main.detalhe_questao', id=id, corrigida='1'))


@main_bp.route('/api/questoes/<int:id>/responder', methods=['POST'])
def responder_questao_api(id):
    """Envio assíncrono via fetch POST com JSON + CSRF (T07)."""
    questao = db.session.get(Questao, id)
    if not questao:
        return jsonify({'sucesso': False, 'erro': 'Questão não encontrada.'}), 404

    if not current_user.is_authenticated:
        # Visitante tentando responder: orienta a ir ao login
        login_url = url_for('auth.login', next=url_for('main.detalhe_questao', id=id))
        return jsonify({
            'sucesso': False,
            'erro': 'login_necessario',
            'login_url': login_url
        }), 401

    data = request.get_json(silent=True) or {}
    alternativa = data.get('alternativa')
    texto_resposta = (data.get('texto_resposta') or '').strip()

    if questao.tipo == 'objetiva':
        if not alternativa or alternativa.upper() not in ('A', 'B', 'C', 'D', 'E'):
            return jsonify({'sucesso': False, 'erro': 'Selecione uma alternativa válida.'}), 400

        correta = (alternativa.upper() == questao.gabarito_oficial.upper())
        resp = RespostaEstudo(
            usuario_id=current_user.id,
            questao_id=questao.id,
            alternativa_marcada=alternativa.upper(),
            correta=correta
        )
    else:
        if not texto_resposta:
            return jsonify({'sucesso': False, 'erro': 'Escreva sua resposta antes de enviar.'}), 400

        correta = None
        resp = RespostaEstudo(
            usuario_id=current_user.id,
            questao_id=questao.id,
            texto_resposta=texto_resposta,
            correta=None
        )

    db.session.add(resp)
    db.session.commit()

    # Prepara resposta para renderização no client-side
    comentario_publicado = (questao.comentario_status == 'publicado')
    comentarios_erro = {alt.letra: (alt.comentario_erro or '') for alt in questao.alternativas} if comentario_publicado else {}
    comentario_correta = questao.comentario_correta if comentario_publicado else None
    comentario_em_elaboracao = not bool(comentario_publicado and questao.comentario_correta and questao.comentario_correta.strip())

    return jsonify({
        'sucesso': True,
        'tipo': questao.tipo,
        'acertou': correta,
        'alternativa_marcada': alternativa.upper() if alternativa else None,
        'gabarito_oficial': questao.gabarito_oficial,
        'comentario_correta': comentario_correta,
        'comentarios_erro': comentarios_erro,
        'padrao_resposta': questao.padrao_resposta,
        'texto_resposta': texto_resposta,
        'comentario_em_elaboracao': comentario_em_elaboracao,
        'discussao_url': url_for('main.discussao_questao', id=questao.id)
    })


@main_bp.route('/questoes/<int:id>/discussao')
def discussao_questao(id):
    """Página 'Em construção' para o fórum de discussão da questão."""
    questao = db.session.get(Questao, id)
    num_txt = f"Questão {questao.numero} · ENADE {questao.ano}" if questao else f"Questão {id}"
    return render_template(
        'main/discussao_em_construcao.html',
        titulo=f"Discussão — {num_txt}",
        subtitulo="O fórum de discussão vinculado a cada questão está em elaboração e estará disponível em breve.",
        questao=questao,
        ativo='questoes'
    )


def _resolver_curso_id(usuario) -> int:
    curso_id = usuario.curso_id
    if not curso_id:
        primeiro_curso = Curso.query.order_by(Curso.id.asc()).first()
        curso_id = primeiro_curso.id if primeiro_curso else None
    return curso_id


def _obter_simulado_ativo_ou_expirar(usuario):
    simulado_ativo = Simulado.query.filter_by(
        usuario_id=usuario.id,
        finalizado_em=None
    ).first()
    if simulado_ativo:
        if simulado_ativo.is_expirado():
            simulado_ativo.finalizar(motivo='tempo')
            db.session.commit()
            return None
        return simulado_ativo
    return None


def _criar_simulado_parcial(usuario, componente='ambos', area='todas', quantidade=10):
    """Cria um simulado parcial reutilizado por /simulados/novo e /simulados/rapido."""
    if quantidade < 5 or quantidade > 40:
        return None, "A quantidade de questões deve ser entre 5 e 40."

    curso_id = _resolver_curso_id(usuario)
    if componente == 'formacao_geral':
        q_query = Questao.query.filter(
            Questao.componente == 'formacao_geral',
            Questao.anulada == False
        )
    elif componente == 'especifico':
        q_query = Questao.query.filter(
            Questao.componente == 'especifico',
            Questao.curso_id == curso_id,
            Questao.anulada == False
        )
    else:
        q_query = Questao.query.filter(
            db.or_(Questao.componente == 'formacao_geral', Questao.curso_id == curso_id),
            Questao.anulada == False
        )

    if area and area != 'todas':
        q_query = q_query.filter(Questao.area == area)

    questoes_disp = q_query.order_by(Questao.ano.desc(), Questao.numero.asc()).all()
    if len(questoes_disp) < quantidade:
        return None, (
            f"Não há questões suficientes para os filtros selecionados. "
            f"Disponíveis: {len(questoes_disp)}, solicitadas: {quantidade}."
        )

    questoes_sel = questoes_disp[:quantidade]
    duracao_padrao = quantidade * 360  # 6 minutos por questão (RN06)
    duracao = int(os.environ.get('SIMULADO_DURACAO_TESTE', duracao_padrao))

    simulado = Simulado(
        usuario_id=usuario.id,
        tipo='parcial',
        componente=componente,
        area=area,
        duracao_segundos=duracao
    )
    db.session.add(simulado)
    db.session.flush()

    for idx, q in enumerate(questoes_sel, start=1):
        db.session.add(SimuladoQuestao(simulado_id=simulado.id, questao_id=q.id, ordem=idx))

    db.session.commit()
    return simulado, None


@main_bp.route('/simulados/rapido', methods=['POST'])
@login_required
def simulado_rapido():
    """Atalho T05 (N07): cria direto um simulado parcial de 10 questões (1h00, todas as áreas, Ambos)."""
    simulado_ativo = _obter_simulado_ativo_ou_expirar(current_user)
    if simulado_ativo:
        flash("Você já possui um simulado em andamento.", "info")
        return redirect(url_for('main.ver_simulado', id=simulado_ativo.id))

    simulado, erro_msg = _criar_simulado_parcial(current_user, componente='ambos', area='todas', quantidade=10)
    if erro_msg:
        flash(erro_msg, "danger")
        return redirect(url_for('main.novo_simulado'))
    return redirect(url_for('main.ver_simulado', id=simulado.id))


@main_bp.route('/simulados/novo', methods=['GET', 'POST'])
@login_required
def novo_simulado():
    """T08 - Montar simulado (RF09, RN03, RN05, RN06)."""
    # Se já tem simulado em andamento, redireciona para ele
    simulado_ativo = _obter_simulado_ativo_ou_expirar(current_user)
    if simulado_ativo:
        flash("Você já possui um simulado em andamento.", "info")
        return redirect(url_for('main.ver_simulado', id=simulado_ativo.id))

    curso_id = _resolver_curso_id(current_user)

    # Consulta edições completas do curso (Formação Geral + Específico do curso)
    anos_edicoes = [
        r[0] for r in db.session.query(Questao.ano)
        .filter(db.or_(Questao.componente == 'formacao_geral', Questao.curso_id == curso_id))
        .distinct()
        .order_by(Questao.ano.desc())
        .all()
    ]

    curso_obj = db.session.get(Curso, curso_id)
    curso_nome = curso_obj.nome if curso_obj else ""

    edicoes_info = []
    for ano in anos_edicoes:
        q_edicao = Questao.query.filter(
            Questao.ano == ano,
            db.or_(Questao.componente == 'formacao_geral', Questao.curso_id == curso_id)
        )
        total_q = q_edicao.count()
        anuladas_q = q_edicao.filter(Questao.anulada == True).count()
        validas_q = total_q - anuladas_q
        edicoes_info.append({
            'ano': ano,
            'label': f"ENADE {ano} · {curso_nome}",
            'total': total_q,
            'anuladas': anuladas_q,
            'validas': validas_q
        })

    # Uma edição completa deve possuir 40 questões (10 FG + 30 Específico)
    edicoes_completas = [e for e in edicoes_info if e['total'] >= 40]
    tem_edicao_completa = len(edicoes_completas) > 0

    # Consulta áreas disponíveis do curso (não anuladas: FG comuns + curso_id)
    areas_disponiveis = [
        r[0] for r in db.session.query(Questao.area)
        .filter(
            db.or_(Questao.componente == 'formacao_geral', Questao.curso_id == curso_id),
            Questao.anulada == False
        )
        .distinct()
        .order_by(Questao.area.asc())
        .all()
    ]

    if request.method == 'POST':
        tipo = request.form.get('tipo', 'completo')

        if tipo == 'completo':
            if not tem_edicao_completa:
                flash("Ainda não há uma edição completa do seu curso.", "danger")
                return redirect(url_for('main.novo_simulado'))

            ano_sel = request.form.get('edicao', type=int)
            if not ano_sel and edicoes_completas:
                ano_sel = edicoes_completas[0]['ano']

            # Questões não anuladas da edição completa (FG + Específico do curso)
            questoes = Questao.query.filter(
                Questao.ano == ano_sel,
                db.or_(Questao.componente == 'formacao_geral', Questao.curso_id == curso_id),
                Questao.anulada == False
            ).order_by(Questao.numero.asc()).all()

            if not questoes:
                flash("Não há questões disponíveis para a edição selecionada.", "danger")
                return redirect(url_for('main.novo_simulado'))

            duracao_padrao = 14400  # 4h00 (RN06)
            duracao = int(os.environ.get('SIMULADO_DURACAO_TESTE', duracao_padrao))

            simulado = Simulado(
                usuario_id=current_user.id,
                tipo='completo',
                edicao_ano=ano_sel,
                duracao_segundos=duracao
            )
            db.session.add(simulado)
            db.session.flush()

            for idx, q in enumerate(questoes, start=1):
                sq = SimuladoQuestao(simulado_id=simulado.id, questao_id=q.id, ordem=idx)
                db.session.add(sq)

            db.session.commit()
            return redirect(url_for('main.ver_simulado', id=simulado.id))

        else:  # Parcial
            componente = request.form.get('componente', 'especifico')
            area = request.form.get('area', 'todas')
            quantidade = request.form.get('quantidade', 10, type=int)

            simulado, erro_msg = _criar_simulado_parcial(current_user, componente, area, quantidade)
            if erro_msg:
                flash(erro_msg, "danger")
                return redirect(url_for('main.novo_simulado'))
            return redirect(url_for('main.ver_simulado', id=simulado.id))

    return render_template(
        'main/simulado_novo.html',
        ativo='simulados',
        tem_edicao_completa=tem_edicao_completa,
        edicoes=edicoes_completas if tem_edicao_completa else edicoes_info,
        areas=areas_disponiveis
    )


@main_bp.route('/simulados/<int:id>')
@login_required
def ver_simulado(id):
    """T09 - Simulado em andamento (RF10, RF11, RF13, RN04, RN05)."""
    simulado = db.session.get(Simulado, id)
    if not simulado or simulado.usuario_id != current_user.id:
        return render_template('auth/404.html'), 404

    # RN05: Se o tempo acabou, finaliza automaticamente e vai para o resultado
    if simulado.is_expirado():
        simulado.finalizar(motivo='tempo')
        db.session.commit()
        return redirect(url_for('main.resultado_simulado', id=simulado.id))

    # Se já foi finalizado, vai para o resultado
    if simulado.finalizado_em is not None:
        return redirect(url_for('main.resultado_simulado', id=simulado.id))

    questoes_assoc = simulado.questoes_assoc
    total_questoes = len(questoes_assoc)
    respostas_dict = {r.questao_id: r for r in simulado.respostas}

    # Navegação sem JS via query param ?q=ordem
    ordem_atual = request.args.get('q', 1, type=int)
    if ordem_atual < 1:
        ordem_atual = 1
    elif ordem_atual > total_questoes and total_questoes > 0:
        ordem_atual = total_questoes

    sq_atual = next((sq for sq in questoes_assoc if sq.ordem == ordem_atual), None)
    if not sq_atual and questoes_assoc:
        sq_atual = questoes_assoc[0]
        ordem_atual = 1

    q_atual = sq_atual.questao if sq_atual else None
    resposta_atual = respostas_dict.get(q_atual.id) if q_atual else None

    # Status para o mapa de questões
    respondidas_count = 0
    mapa_itens = []
    questoes_em_branco = []

    for sq in questoes_assoc:
        resp = respostas_dict.get(sq.questao_id)
        tem_resposta = False
        if resp:
            if sq.questao.tipo == 'objetiva' and resp.alternativa_marcada:
                tem_resposta = True
            elif sq.questao.tipo == 'discursiva' and resp.texto_resposta and resp.texto_resposta.strip():
                tem_resposta = True

        if tem_resposta:
            respondidas_count += 1
        else:
            questoes_em_branco.append(sq.ordem)

        mapa_itens.append({
            'ordem': sq.ordem,
            'questao_id': sq.questao_id,
            'tipo': sq.questao.tipo,
            'respondida': tem_resposta,
            'is_atual': (sq.ordem == ordem_atual)
        })

    tempo_restante = simulado.get_tempo_restante_segundos()

    if simulado.tipo == 'completo':
        titulo_simulado = f"Simulado · Prova completa ENADE {simulado.edicao_ano}"
    else:
        titulo_simulado = f"Simulado parcial ({total_questoes} questões)"

    ultima_atualizacao = None
    if simulado.respostas:
        ultima_atualizacao = max(r.atualizada_em for r in simulado.respostas)

    # RN04: Nunca passar gabarito_oficial, comentarios nem padrao_resposta!
    return render_template(
        'main/simulado.html',
        simulado=simulado,
        titulo_simulado=titulo_simulado,
        tempo_restante=tempo_restante,
        questoes_assoc=questoes_assoc,
        total_questoes=total_questoes,
        ordem_atual=ordem_atual,
        sq_atual=sq_atual,
        q_atual=q_atual,
        resposta_atual=resposta_atual,
        respostas_dict=respostas_dict,
        respondidas_count=respondidas_count,
        mapa_itens=mapa_itens,
        questoes_em_branco=questoes_em_branco,
        ultima_atualizacao=ultima_atualizacao
    )


@main_bp.route('/api/simulados/<int:id>')
@login_required
def api_simulado_get(id):
    """API para carregar estado do simulado e suas questões (RN04: SEM GABARITO)."""
    simulado = db.session.get(Simulado, id)
    if not simulado or simulado.usuario_id != current_user.id:
        return jsonify({'erro': 'Simulado não encontrado'}), 404

    if simulado.is_expirado():
        simulado.finalizar(motivo='tempo')
        db.session.commit()
        return jsonify({
            'finalizado': True,
            'redirect_url': url_for('main.resultado_simulado', id=simulado.id)
        })

    if simulado.finalizado_em is not None:
        return jsonify({
            'finalizado': True,
            'redirect_url': url_for('main.resultado_simulado', id=simulado.id)
        })

    questoes_lista = []
    for sq in simulado.questoes_assoc:
        q = sq.questao
        questoes_lista.append({
            'id': q.id,
            'ordem': sq.ordem,
            'numero': q.numero,
            'ano': q.ano,
            'componente': q.componente,
            'area': q.area,
            'tipo': q.tipo,
            'enunciado': q.enunciado,
            'imagem_placeholder': q.imagem_placeholder,
            'alternativas': [
                {'letra': alt.letra, 'texto': alt.texto}
                for alt in q.alternativas
            ]
        })

    respostas_dict = {}
    for r in simulado.respostas:
        respostas_dict[str(r.questao_id)] = {
            'alternativa_marcada': r.alternativa_marcada,
            'texto_resposta': r.texto_resposta
        }

    return jsonify({
        'id': simulado.id,
        'tipo': simulado.tipo,
        'edicao_ano': simulado.edicao_ano,
        'duracao_segundos': simulado.duracao_segundos,
        'tempo_restante': simulado.get_tempo_restante_segundos(),
        'total_questoes': len(questoes_lista),
        'questoes': questoes_lista,
        'respostas': respostas_dict
    })


@main_bp.route('/api/simulados/<int:id>/respostas/<int:questao_id>', methods=['PUT'])
@login_required
def api_simulado_resposta_salvar(id, questao_id):
    """RNF07, RN05, RN07: Salva resposta no simulado em andamento."""
    simulado = db.session.get(Simulado, id)
    if not simulado or simulado.usuario_id != current_user.id:
        return jsonify({'erro': 'Simulado não encontrado'}), 404

    # RN07: Simulado finalizado rejeita alterações com 409 Conflict
    if simulado.finalizado_em is not None or simulado.is_expirado():
        if not simulado.finalizado_em:
            simulado.finalizar(motivo='tempo')
            db.session.commit()
        return jsonify({
            'erro': 'Este simulado já foi finalizado e não aceita alterações.',
            'finalizado': True,
            'redirect_url': url_for('main.resultado_simulado', id=simulado.id)
        }), 409

    sq = SimuladoQuestao.query.filter_by(simulado_id=simulado.id, questao_id=questao_id).first()
    if not sq:
        return jsonify({'erro': 'Questão não pertence ao simulado.'}), 404

    data = request.get_json() or {}
    alternativa = data.get('alternativa_marcada')
    texto = data.get('texto_resposta')

    resp = SimuladoResposta.query.filter_by(simulado_id=simulado.id, questao_id=questao_id).first()
    if not resp:
        resp = SimuladoResposta(simulado_id=simulado.id, questao_id=questao_id)
        db.session.add(resp)

    resp.alternativa_marcada = alternativa.upper() if alternativa else None
    resp.texto_resposta = texto if texto else None
    resp.atualizada_em = utc_now()

    db.session.commit()

    return jsonify({
        'sucesso': True,
        'salvo_em': resp.atualizada_em.strftime('%H:%M'),
        'tempo_restante': simulado.get_tempo_restante_segundos()
    })


@main_bp.route('/api/simulados/<int:id>/finalizar', methods=['POST'])
@login_required
def api_simulado_finalizar(id):
    """RF12, RN05: Finalização do simulado via API (por entrega ou por tempo)."""
    simulado = db.session.get(Simulado, id)
    if not simulado or simulado.usuario_id != current_user.id:
        return jsonify({'erro': 'Simulado não encontrado'}), 404

    data = request.get_json() or {}
    motivo = data.get('motivo', 'entrega')
    if motivo not in ('entrega', 'tempo'):
        motivo = 'entrega'

    if not simulado.finalizado_em:
        simulado.finalizar(motivo=motivo)
        db.session.commit()

    return jsonify({
        'sucesso': True,
        'redirect_url': url_for('main.resultado_simulado', id=simulado.id)
    })


@main_bp.route('/simulados/<int:id>/finalizar', methods=['POST'])
@login_required
def simulado_finalizar_post(id):
    """RF12: Finalização do simulado via submissão normal de formulário (fallback sem JS)."""
    simulado = db.session.get(Simulado, id)
    if not simulado or simulado.usuario_id != current_user.id:
        return render_template('auth/404.html'), 404

    motivo = request.form.get('motivo', 'entrega')
    if motivo not in ('entrega', 'tempo'):
        motivo = 'entrega'

    if not simulado.finalizado_em:
        simulado.finalizar(motivo=motivo)
        db.session.commit()

    return redirect(url_for('main.resultado_simulado', id=simulado.id))


@main_bp.route('/simulados/<int:id>/resultado')
@login_required
def resultado_simulado(id):
    """T11 - Resultado do simulado (RF14, US08, RN04, RN08, RN09)."""
    simulado = db.session.get(Simulado, id)
    if not simulado or simulado.usuario_id != current_user.id:
        return render_template('auth/404.html'), 404

    if not simulado.finalizado_em:
        if simulado.is_expirado():
            simulado.finalizar(motivo='tempo')
            db.session.commit()
        else:
            return redirect(url_for('main.ver_simulado', id=simulado.id))

    respostas_dict = {r.questao_id: r for r in simulado.respostas}
    questoes_assoc = simulado.questoes_assoc
    total_questoes = len(questoes_assoc)

    duracao_gasta = int((simulado.finalizado_em - simulado.iniciado_em).total_seconds())
    tempo_utilizado_fmt = formatar_duracao(duracao_gasta)
    tempo_total_fmt = formatar_duracao(simulado.duracao_segundos)

    objetivas_total = 0
    objetivas_respondidas = 0
    objetivas_corretas = 0
    objetivas_erradas = 0
    objetivas_em_branco = 0

    discursivas_total = 0
    discursivas_respondidas = 0
    discursivas_lista = []

    areas_stats = {}
    linhas_tabela = []

    for sq in questoes_assoc:
        q = sq.questao
        resp = respostas_dict.get(q.id)

        if q.tipo == 'objetiva':
            objetivas_total += 1
            area = q.area
            if area not in areas_stats:
                areas_stats[area] = {'total': 0, 'respondidas': 0, 'corretas': 0}
            areas_stats[area]['total'] += 1

            marcada = resp.alternativa_marcada if resp else None

            if marcada:
                objetivas_respondidas += 1
                areas_stats[area]['respondidas'] += 1
                if marcada == q.gabarito_oficial:
                    objetivas_corretas += 1
                    areas_stats[area]['corretas'] += 1
                    situacao = 'Acertou'
                else:
                    objetivas_erradas += 1
                    situacao = 'Errou'
                sua_resposta = marcada
            else:
                objetivas_em_branco += 1
                situacao = 'Em branco'
                sua_resposta = '—'

            linhas_tabela.append({
                'ordem': sq.ordem,
                'numero': q.numero,
                'questao_id': q.id,
                'area': q.area,
                'tipo': q.tipo,
                'sua_resposta': sua_resposta,
                'gabarito': q.gabarito_oficial,
                'situacao': situacao
            })

        else:  # Discursiva
            discursivas_total += 1
            tem_texto = bool(resp and resp.texto_resposta and resp.texto_resposta.strip())
            if tem_texto:
                discursivas_respondidas += 1
                situacao = 'Respondida'
                sua_resposta = 'Texto enviado'
            else:
                situacao = 'Em branco'
                sua_resposta = '—'

            discursivas_lista.append({
                'ordem': sq.ordem,
                'numero': q.numero,
                'questao_id': q.id,
                'componente': 'Formação Geral' if q.componente == 'formacao_geral' else 'Específico',
                'respondida': tem_texto
            })

            linhas_tabela.append({
                'ordem': sq.ordem,
                'numero': q.numero,
                'questao_id': q.id,
                'area': q.area,
                'tipo': q.tipo,
                'sua_resposta': sua_resposta,
                'gabarito': 'Padrão INEP',
                'situacao': situacao
            })

    # RN08: % de acerto = objetivas corretas ÷ objetivas respondidas
    if objetivas_respondidas > 0:
        percentual_acerto = int(round((objetivas_corretas / objetivas_respondidas) * 100))
    else:
        percentual_acerto = 0

    # Processamento de áreas (ordenadas da mais fraca para a mais forte)
    areas_lista = []
    for area_nome, dados in areas_stats.items():
        if dados['respondidas'] > 0:
            pct = int(round((dados['corretas'] / dados['respondidas']) * 100))
        else:
            pct = 0
        frac = f"{dados['corretas']}/{dados['total']}"
        areas_lista.append({
            'nome': area_nome,
            'pct': pct,
            'frac': frac,
            'total': dados['total'],
            'corretas': dados['corretas'],
            'respondidas': dados['respondidas']
        })

    areas_lista.sort(key=lambda x: (x['pct'], x['total']))

    if simulado.tipo == 'completo':
        titulo_resultado = f"Resultado · Prova completa ENADE {simulado.edicao_ano}"
    else:
        titulo_resultado = f"Resultado · Simulado parcial ({total_questoes} questões)"

    data_entrega_str = simulado.finalizado_em.strftime('%d/%m/%Y às %H:%M')

    return render_template(
        'main/resultado_simulado.html',
        ativo='simulados',
        simulado=simulado,
        titulo_resultado=titulo_resultado,
        data_entrega_str=data_entrega_str,
        percentual_acerto=percentual_acerto,
        objetivas_total=objetivas_total,
        objetivas_respondidas=objetivas_respondidas,
        objetivas_corretas=objetivas_corretas,
        objetivas_erradas=objetivas_erradas,
        objetivas_em_branco=objetivas_em_branco,
        tempo_utilizado=tempo_utilizado_fmt,
        tempo_total=tempo_total_fmt,
        areas=areas_lista,
        discursivas_total=discursivas_total,
        discursivas_respondidas=discursivas_respondidas,
        discursivas_lista=discursivas_lista,
        linhas_tabela=linhas_tabela
    )


@main_bp.route('/simulados/<int:id>/questao/<int:questao_id>')
@login_required
def revisao_questao_simulado(id, questao_id):
    """Revisão comentada de uma questão dentro do simulado finalizado."""
    simulado = db.session.get(Simulado, id)
    if not simulado or simulado.usuario_id != current_user.id:
        return render_template('auth/404.html'), 404

    if not simulado.finalizado_em:
        return redirect(url_for('main.ver_simulado', id=simulado.id))

    questao = db.session.get(Questao, questao_id)
    if not questao:
        return render_template('auth/404.html'), 404

    sq_atual = SimuladoQuestao.query.filter_by(simulado_id=simulado.id, questao_id=questao.id).first()
    if not sq_atual:
        return render_template('auth/404.html'), 404

    todas_sq = simulado.questoes_assoc
    total_q = len(todas_sq)
    idx_atual = next((i for i, sq in enumerate(todas_sq) if sq.id == sq_atual.id), 0)

    anterior_id = todas_sq[idx_atual - 1].questao_id if idx_atual > 0 else None
    proximo_id = todas_sq[idx_atual + 1].questao_id if idx_atual < total_q - 1 else None

    resposta = SimuladoResposta.query.filter_by(simulado_id=simulado.id, questao_id=questao.id).first()

    comentario_publicado = (questao.comentario_status == 'publicado')
    comentarios_erro = {alt.letra: (alt.comentario_erro or '') for alt in questao.alternativas} if comentario_publicado else {}
    comentario_em_elaboracao = not bool(comentario_publicado and questao.comentario_correta and questao.comentario_correta.strip())

    return render_template(
        'main/questao_simulado_revisao.html',
        ativo='simulados',
        simulado=simulado,
        questao=questao,
        sq_atual=sq_atual,
        ordem=sq_atual.ordem,
        total_q=total_q,
        anterior_id=anterior_id,
        proximo_id=proximo_id,
        resposta=resposta,
        comentarios_erro=comentarios_erro,
        comentario_em_elaboracao=comentario_em_elaboracao
    )


@main_bp.route('/desempenho')
@login_required
def desempenho():
    """T12 - Painel de desempenho (RF15, RF16, US09, US13, RN08, RN09)."""
    origem = request.args.get('origem', 'tudo')
    componente = request.args.get('componente', 'todos')
    evolucao_area = request.args.get('evolucao_area', 'geral')

    resumo = calcular_resumo_geral(current_user, origem=origem, componente=componente)
    evolucao = calcular_evolucao_semanal(
        current_user,
        origem=origem,
        componente=componente,
        evolucao_area=evolucao_area
    )
    mudancas = calcular_mudancas_4_semanas(current_user, origem=origem, componente=componente)
    ultimos_simulados = obter_historico_simulados(current_user, limite=5)

    return render_template(
        'main/desempenho.html',
        ativo='desempenho',
        tem_dados=resumo['tem_dados'],
        origem=origem,
        componente=componente,
        evolucao_area=evolucao['area_selecionada'],
        percentual_geral=resumo['percentual_geral'],
        total_respondidas=resumo['total_respondidas'],
        total_simulados=resumo['total_simulados'],
        total_em_branco=resumo['total_em_branco'],
        areas=resumo['areas'],
        evolucao=evolucao,
        mudancas=mudancas,
        ultimos_simulados=ultimos_simulados['itens']
    )


@main_bp.route('/api/desempenho/evolucao')
@login_required
def api_desempenho_evolucao():
    """Retorna o HTML parcial do gráfico de evolução semanal para atualização sem recarregar (JS)."""
    origem = request.args.get('origem', 'tudo')
    componente = request.args.get('componente', 'todos')
    evolucao_area = request.args.get('evolucao_area', 'geral')

    evolucao = calcular_evolucao_semanal(
        current_user,
        origem=origem,
        componente=componente,
        evolucao_area=evolucao_area
    )
    return render_template('partials/desempenho_evolucao.html', evolucao=evolucao)


@main_bp.route('/simulados/historico')
@login_required
def historico_simulados():
    """Histórico completo de simulados realizados (RF16 / US13)."""
    tipo_filtro = request.args.get('tipo', 'todos')
    pagina = request.args.get('pagina', 1, type=int)

    simulado_ativo = obter_simulado_em_andamento(current_user)
    historico = obter_historico_simulados(
        current_user,
        tipo_filtro=tipo_filtro,
        pagina=pagina,
        por_pagina=10
    )

    return render_template(
        'main/simulado_historico.html',
        ativo='simulados',
        tipo_filtro=tipo_filtro,
        simulado_ativo=simulado_ativo,
        historico=historico
    )



@main_bp.route('/termos')
def termos():
    """Termos de uso do projeto acadêmico."""
    return render_template('main/termos.html')


@main_bp.route('/privacidade')
def privacidade():
    """Política de privacidade e LGPD (RNF04)."""
    return render_template('main/privacidade.html')
