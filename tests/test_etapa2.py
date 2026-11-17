import pytest
from app import create_app
from app.extensions import db
from app.models import Usuario, Curso, Questao, Alternativa, RespostaEstudo
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

        # Cria cursos
        cc = Curso(nome="Ciência da Computação")
        si = Curso(nome="Sistemas de Informação")
        db.session.add_all([cc, si])
        db.session.commit()

        # Cria estudante de teste
        ana = Usuario(
            nome="Ana Souza",
            email="ana@teste.com",
            curso_id=cc.id,
            perfil="estudante"
        )
        ana.set_senha("12345678")
        db.session.add(ana)
        db.session.commit()

        # Cria questões para testes
        # Q1: CC 2023 FG Objetiva - Atualidades - Correta: B (Com comentário)
        q1 = Questao(
            ano=2023,
            curso_id=cc.id,
            numero=1,
            componente="formacao_geral",
            area="Atualidades",
            tipo="objetiva",
            enunciado="Enunciado da questão 1 sobre atualidades globais. [questão fictícia para protótipo]",
            gabarito_oficial="B",
            comentario_correta="A opção B é a correta pela análise histórica.",
            comentario_status="publicado",
            anulada=False
        )
        db.session.add(q1)
        db.session.flush()
        for letra in ["A", "B", "C", "D", "E"]:
            db.session.add(Alternativa(
                questao_id=q1.id,
                letra=letra,
                texto=f"Texto da alternativa {letra}",
                comentario_erro=None if letra == "B" else f"Erro da alternativa {letra}"
            ))

        # Q2: CC 2023 Específico Objetiva - Banco de Dados - Correta: C (SEM comentário para testar "Comentário em elaboração")
        q2 = Questao(
            ano=2023,
            curso_id=cc.id,
            numero=2,
            componente="especifico",
            area="Banco de Dados",
            tipo="objetiva",
            enunciado="Enunciado da questão 2 sobre álgebra relacional. [questão fictícia para protótipo]",
            gabarito_oficial="C",
            comentario_correta=None,  # Sem comentário proposital
            anulada=False
        )
        db.session.add(q2)
        db.session.flush()
        for letra in ["A", "B", "C", "D", "E"]:
            db.session.add(Alternativa(
                questao_id=q2.id,
                letra=letra,
                texto=f"Texto da alternativa {letra}",
                comentario_erro=None
            ))

        # Q3: CC 2023 Específico Objetiva - Redes - Anulada pelo INEP - Correta: A
        q3 = Questao(
            ano=2023,
            curso_id=cc.id,
            numero=3,
            componente="especifico",
            area="Redes",
            tipo="objetiva",
            enunciado="Enunciado da questão 3 sobre roteamento IP. [questão fictícia para protótipo]",
            gabarito_oficial="A",
            comentario_correta="Comentário sobre a anulação do item.",
            anulada=True  # Anulada pelo INEP (RN03)
        )
        db.session.add(q3)
        db.session.flush()
        for letra in ["A", "B", "C", "D", "E"]:
            db.session.add(Alternativa(
                questao_id=q3.id,
                letra=letra,
                texto=f"Texto da alternativa {letra}",
                comentario_erro=None
            ))

        # Q4: CC 2023 Específico Discursiva - Engenharia de Software
        q4 = Questao(
            ano=2023,
            curso_id=cc.id,
            numero=4,
            componente="especifico",
            area="Engenharia de Software",
            tipo="discursiva",
            enunciado="Enunciado da discursiva sobre microsserviços. [questão fictícia para protótipo]",
            gabarito_oficial="DISCURSIVA",
            padrao_resposta="Padrão esperado com análise de arquitetura orientada a eventos.",
            anulada=False
        )
        db.session.add(q4)

        # Q5: SI 2021 Específico Objetiva - Sistemas de Informação
        q5 = Questao(
            ano=2021,
            curso_id=si.id,
            numero=1,
            componente="especifico",
            area="Engenharia de Software",
            tipo="objetiva",
            enunciado="Enunciado de Sistemas de Informação 2021. [questão fictícia para protótipo]",
            gabarito_oficial="D",
            comentario_correta="Explicação da questão 1 de SI.",
            anulada=False
        )
        db.session.add(q5)
        db.session.flush()
        for letra in ["A", "B", "C", "D", "E"]:
            db.session.add(Alternativa(
                questao_id=q5.id,
                letra=letra,
                texto=f"Texto da alternativa {letra}",
                comentario_erro=None
            ))

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


# ==============================================================================
# US04 — Filtrar questões (T06)
# ==============================================================================
def test_us04_filtrar_por_curso_e_area(client, app):
    """US04: Dado que selecionei curso e área, quando aplico o filtro, então só aparecem questões que atendem aos dois critérios."""
    with app.app_context():
        cc = Curso.query.filter_by(nome="Ciência da Computação").first()

    # Filtra por Ciência da Computação e Banco de Dados (deve achar Q2)
    res = client.get(f'/questoes?curso={cc.id}&area=Banco+de+Dados')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    assert "1 questões encontradas" in conteudo or "1 quest&otilde;es encontradas" in conteudo
    assert "álgebra relacional" in conteudo
    # Não deve trazer questão de Atualidades nem de Redes
    assert "atualidades globais" not in conteudo
    assert "roteamento IP" not in conteudo


def test_us04_filtro_sem_resultados(client, app):
    """US04: Dado que nenhuma questão atende ao filtro, então vejo a mensagem 'Nenhuma questão encontrada'."""
    with app.app_context():
        cc = Curso.query.filter_by(nome="Ciência da Computação").first()

    # Filtro inexistente: CC + 2017 (não há questões em 2017)
    res = client.get(f'/questoes?curso={cc.id}&ano=2017')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    assert "Nenhuma questão encontrada" in conteudo or "Nenhuma quest&atilde;o encontrada" in conteudo


def test_us04_busca_por_texto(client, app):
    """US04: Busca por texto no enunciado filtra adequadamente."""
    with app.app_context():
        cc = Curso.query.filter_by(nome="Ciência da Computação").first()

    res = client.get(f'/questoes?curso={cc.id}&q=roteamento')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    assert "roteamento IP" in conteudo
    assert "álgebra relacional" not in conteudo


def test_us04_etiqueta_anulada_inep(client, app):
    """RN03: Questões anuladas continuam visíveis no banco com a etiqueta 'Anulada pelo INEP'."""
    with app.app_context():
        cc = Curso.query.filter_by(nome="Ciência da Computação").first()

    res = client.get(f'/questoes?curso={cc.id}')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    assert "Anulada pelo INEP" in conteudo


# ==============================================================================
# US05 — Responder questão objetiva (T07a e T07b)
# ==============================================================================
def test_us05_responder_questao_acerto(client, app):
    """US05: Dado que marquei uma alternativa correta, quando confirmo, vejo que acertei."""
    # Loga com Ana Souza
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    with app.app_context():
        q1 = Questao.query.filter_by(numero=1).first()
        q1_id = q1.id

    # Envia via API JSON (gabarito é B)
    res = client.post(f'/api/questoes/{q1_id}/responder', json={
        'alternativa': 'B'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['sucesso'] is True
    assert data['acertou'] is True
    assert data['gabarito_oficial'] == 'B'
    assert data['alternativa_marcada'] == 'B'

    # Verifica persistência no banco
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        r = RespostaEstudo.query.filter_by(usuario_id=ana.id, questao_id=q1_id).first()
        assert r is not None
        assert r.alternativa_marcada == 'B'
        assert r.correta is True


def test_us05_responder_questao_erro(client, app):
    """US05: Dado que marquei uma alternativa incorreta, quando confirmo, vejo minha resposta e a correta."""
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    with app.app_context():
        q1 = Questao.query.filter_by(numero=1).first()
        q1_id = q1.id

    # Envia via API JSON marcando C (o gabarito é B)
    res = client.post(f'/api/questoes/{q1_id}/responder', json={
        'alternativa': 'C'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['sucesso'] is True
    assert data['acertou'] is False
    assert data['alternativa_marcada'] == 'C'
    assert data['gabarito_oficial'] == 'B'


def test_us05_validacao_sem_marcar_alternativa(client, app):
    """US05: Submissão sem alternativa é rejeitada com erro."""
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    with app.app_context():
        q1_id = Questao.query.filter_by(numero=1).first().id

    res = client.post(f'/api/questoes/{q1_id}/responder', json={
        'alternativa': None
    })
    assert res.status_code == 400


def test_us05_visitante_bloqueado_ao_responder(client, app):
    """RN01: Visitante que tenta responder é orientado a fazer login."""
    with app.app_context():
        q1_id = Questao.query.filter_by(numero=1).first().id

    # API retorna 401 e URL de login com next
    res = client.post(f'/api/questoes/{q1_id}/responder', json={
        'alternativa': 'B'
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data['erro'] == 'login_necessario'
    assert f'/entrar?next=' in data['login_url']


def test_us05_responder_discursiva(client, app):
    """RF07: Envio de resposta em questão discursiva e comparação com padrão de resposta."""
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    with app.app_context():
        q4 = Questao.query.filter_by(tipo='discursiva').first()
        q4_id = q4.id

    res = client.post(f'/api/questoes/{q4_id}/responder', json={
        'texto_resposta': 'Minha proposta é utilizar filas assíncronas com mensageria.'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['sucesso'] is True
    assert data['tipo'] == 'discursiva'
    assert "arquitetura orientada a eventos" in data['padrao_resposta']


# ==============================================================================
# US06 — Ler comentário (T07b)
# ==============================================================================
def test_us06_questao_com_comentario(client, app):
    """US06: Questão com comentário exibe explicação da alternativa correta e dos erros."""
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    with app.app_context():
        q1_id = Questao.query.filter_by(numero=1).first().id

    # Responde
    client.post(f'/api/questoes/{q1_id}/responder', json={'alternativa': 'B'})

    # Acessa a página
    res = client.get(f'/questoes/{q1_id}')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    assert "Gabarito comentado" in conteudo
    assert "Por que a B está correta" in conteudo or "Por que a B est&aacute; correta" in conteudo
    assert "análise histórica" in conteudo or "an&aacute;lise hist&oacute;rica" in conteudo


def test_us06_questao_sem_comentario_mostra_em_elaboracao(client, app):
    """US06: Questão sem comentário mostra 'Comentário em elaboração' e link para o fórum."""
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    with app.app_context():
        q2_id = Questao.query.filter_by(numero=2).first().id

    # Responde
    client.post(f'/api/questoes/{q2_id}/responder', json={'alternativa': 'C'})

    # Acessa a página da questão
    res = client.get(f'/questoes/{q2_id}')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    assert "Comentário em elaboração" in conteudo or "Coment&aacute;rio em elabora&ccedil;&atilde;o" in conteudo
    assert f"/questoes/{q2_id}/discussao" in conteudo


# ==============================================================================
# T05 — Início Completo (Métricas e Desempenho)
# ==============================================================================
def test_t05_inicio_sem_respostas(client, app):
    """T05: Usuário sem respostas vê convite 'Responda algumas questões para ver seu desempenho'."""
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    res = client.get('/inicio')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    assert "Responda algumas questões para ver seu desempenho" in conteudo or "Responda algumas quest&otilde;es para ver seu desempenho" in conteudo


def test_t05_inicio_com_desempenho_calculado(client, app):
    """T05: Responde 2 questões objetivas (1 acerto, 1 erro); verifica cálculo de 50% de acerto geral (RN08 e RN03)."""
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})

    with app.app_context():
        q1_id = Questao.query.filter_by(numero=1).first().id
        q2_id = Questao.query.filter_by(numero=2).first().id
        q3_anulada_id = Questao.query.filter_by(numero=3).first().id

    # Acerta Q1 (Atualidades)
    client.post(f'/api/questoes/{q1_id}/responder', json={'alternativa': 'B'})
    # Erra Q2 (Banco de Dados)
    client.post(f'/api/questoes/{q2_id}/responder', json={'alternativa': 'A'})
    # Responde Q3 que é anulada (RN03: anulada NÃO deve entrar no cálculo)
    client.post(f'/api/questoes/{q3_anulada_id}/responder', json={'alternativa': 'A'})

    res = client.get('/inicio')
    assert res.status_code == 200
    conteudo = res.get_data(as_text=True)

    # 1 acerto de 2 questões válidas respondidas = 50%
    assert "50%" in conteudo
    assert "2" in conteudo  # 2 questões respondidas consideradas
    assert "Revisar primeiro" in conteudo
    assert "Banco de Dados" in conteudo
