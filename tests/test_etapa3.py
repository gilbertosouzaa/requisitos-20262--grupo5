import pytest
import os
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models import Usuario, Curso, Questao, Alternativa, Simulado, SimuladoQuestao, SimuladoResposta, RespostaEstudo
from app.seed import seed_database
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_database()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Cria um cliente logado com o usuário estudante Ana Souza."""
    with client.session_transaction() as sess:
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    return client



def obter_csrf_token(client, url='/simulados/novo'):
    """Auxiliar para extrair o CSRF token do HTML renderizado."""
    res = client.get(url)
    import re
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', res.data.decode('utf-8'))
    return match.group(1) if match else ''


def test_t08_rn03_prova_completa_exclui_anuladas(auth_client, app):
    """RN03: Questões anuladas pelo INEP não entram no simulado (38 questões para ENADE 2023)."""
    with app.app_context():
        # Limpa simulados anteriores da Ana
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        db.session.commit()

    csrf = obter_csrf_token(auth_client, '/simulados/novo')
    res = auth_client.post('/simulados/novo', data={
        'csrf_token': csrf,
        'tipo': 'completo',
        'edicao': '2023'
    }, follow_redirects=True)

    assert res.status_code == 200
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        sim = Simulado.query.filter_by(usuario_id=user.id).first()
        assert sim is not None
        assert sim.tipo == 'completo'
        assert sim.edicao_ano == 2023
        assert sim.duracao_segundos == 14400

        # Verifica quantidade de questões associadas: 40 do banco menos 2 anuladas = 38
        assert len(sim.questoes_assoc) == 38
        for sq in sim.questoes_assoc:
            assert sq.questao.anulada is False


def test_t08_rn06_simulado_parcial_duracao_proporcional(auth_client, app):
    """RN06: No simulado parcial, o tempo é proporcional: 6 minutos por questão (10 questões = 3600s = 1h00)."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        db.session.commit()

    csrf = obter_csrf_token(auth_client, '/simulados/novo')
    res = auth_client.post('/simulados/novo', data={
        'csrf_token': csrf,
        'tipo': 'parcial',
        'componente': 'especifico',
        'area': 'todas',
        'quantidade': '10'
    }, follow_redirects=True)

    assert res.status_code == 200
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        sim = Simulado.query.filter_by(usuario_id=user.id).first()
        assert sim is not None
        assert sim.tipo == 'parcial'
        assert sim.duracao_segundos == 10 * 360  # 3600 segundos
        assert len(sim.questoes_assoc) == 10


def test_t08_regra_apenas_um_simulado_ativo(auth_client, app):
    """O estudante só pode ter 1 simulado em andamento por vez; ao tentar outro, é levado ao aberto."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        sim = Simulado(
            usuario_id=user.id,
            tipo='completo',
            edicao_ano=2023,
            duracao_segundos=14400
        )
        db.session.add(sim)
        db.session.commit()
        sim_id = sim.id

    # Tenta acessar novo simulado por GET
    res = auth_client.get('/simulados/novo')
    assert res.status_code == 302
    assert f'/simulados/{sim_id}' in res.location

    # Tenta criar outro por POST
    csrf = obter_csrf_token(auth_client, f'/simulados/{sim_id}')
    res_post = auth_client.post('/simulados/novo', data={
        'csrf_token': csrf,
        'tipo': 'parcial',
        'quantidade': '5'
    })
    assert res_post.status_code == 302
    assert f'/simulados/{sim_id}' in res_post.location


def test_t09_rn04_api_nunca_devolve_gabarito(auth_client, app):
    """RN04: No simulado em andamento, a API NUNCA devolve gabarito_oficial, comentarios nem padrao_resposta."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        sim = Simulado(
            usuario_id=user.id,
            tipo='completo',
            edicao_ano=2023,
            duracao_segundos=14400
        )
        db.session.add(sim)
        db.session.flush()
        q = Questao.query.filter_by(anulada=False).first()
        sq = SimuladoQuestao(simulado_id=sim.id, questao_id=q.id, ordem=1)
        db.session.add(sq)
        db.session.commit()
        sim_id = sim.id

    res = auth_client.get(f'/api/simulados/{sim_id}')
    assert res.status_code == 200
    data = res.get_json()
    assert 'questoes' in data
    assert len(data['questoes']) > 0
    q_data = data['questoes'][0]

    # Verifica ausência dos campos confidenciais
    assert 'gabarito_oficial' not in q_data
    assert 'comentario_correta' not in q_data
    assert 'padrao_resposta' not in q_data
    for alt in q_data['alternativas']:
        assert 'comentario_erro' not in alt


def test_t09_rnf07_salvamento_automatico_resposta(auth_client, app):
    """RNF07: Salvar resposta via PUT /api/simulados/<id>/respostas/<questao_id>."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        sim = Simulado(
            usuario_id=user.id,
            tipo='completo',
            edicao_ano=2023,
            duracao_segundos=14400
        )
        db.session.add(sim)
        db.session.flush()
        q = Questao.query.filter_by(anulada=False, tipo='objetiva').first()
        sq = SimuladoQuestao(simulado_id=sim.id, questao_id=q.id, ordem=1)
        db.session.add(sq)
        db.session.commit()
        sim_id = sim.id
        q_id = q.id

    # Salva alternativa C
    res = auth_client.put(
        f'/api/simulados/{sim_id}/respostas/{q_id}',
        json={'alternativa_marcada': 'C'}
    )
    assert res.status_code == 200
    assert res.get_json()['sucesso'] is True

    with app.app_context():
        resp = SimuladoResposta.query.filter_by(simulado_id=sim_id, questao_id=q_id).first()
        assert resp is not None
        assert resp.alternativa_marcada == 'C'

    # Altera resposta para B (modificação permitida durante o simulado)
    res2 = auth_client.put(
        f'/api/simulados/{sim_id}/respostas/{q_id}',
        json={'alternativa_marcada': 'B'}
    )
    assert res2.status_code == 200
    with app.app_context():
        resp = SimuladoResposta.query.filter_by(simulado_id=sim_id, questao_id=q_id).first()
        assert resp.alternativa_marcada == 'B'


def test_t09_rn05_tempo_esgotado_finaliza_automaticamente(auth_client, app):
    """RN05: Ao zerar o tempo, o simulado é finalizado automaticamente e leva ao resultado."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        # Inicia há 5 horas atrás com duração de 4 horas
        cinco_horas_atras = datetime.now(timezone.utc) - timedelta(hours=5)
        sim = Simulado(
            usuario_id=user.id,
            tipo='completo',
            edicao_ano=2023,
            duracao_segundos=14400,
            iniciado_em=cinco_horas_atras
        )
        db.session.add(sim)
        db.session.commit()
        sim_id = sim.id

    # Acessa tela do simulado; deve auto-finalizar e redirecionar para resultado
    res = auth_client.get(f'/simulados/{sim_id}')
    assert res.status_code == 302
    assert f'/simulados/{sim_id}/resultado' in res.location

    with app.app_context():
        sim = db.session.get(Simulado, sim_id)
        assert sim.finalizado_em is not None
        assert sim.finalizado_por == 'tempo'


def test_t09_rn07_simulado_finalizado_rejeita_alteracao_com_409(auth_client, app):
    """RN07: Depois de finalizado, o simulado rejeita alterações com HTTP 409 Conflict."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        sim = Simulado(
            usuario_id=user.id,
            tipo='completo',
            edicao_ano=2023,
            duracao_segundos=14400,
            finalizado_em=datetime.now(timezone.utc),
            finalizado_por='entrega'
        )
        db.session.add(sim)
        db.session.flush()
        q = Questao.query.filter_by(anulada=False).first()
        sq = SimuladoQuestao(simulado_id=sim.id, questao_id=q.id, ordem=1)
        db.session.add(sq)
        db.session.commit()
        sim_id = sim.id
        q_id = q.id

    res = auth_client.put(
        f'/api/simulados/{sim_id}/respostas/{q_id}',
        json={'alternativa_marcada': 'A'}
    )
    assert res.status_code == 409
    assert res.get_json()['finalizado'] is True


def test_t11_us08_rn08_resultado_e_calculo_percentual(auth_client, app):
    """US08 e RN08: Cálculo do percentual no resultado (corretas ÷ respondidas) e revisão."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        sim = Simulado(
            usuario_id=user.id,
            tipo='parcial',
            duracao_segundos=3600,
            iniciado_em=datetime.now(timezone.utc) - timedelta(minutes=45),
            finalizado_em=datetime.now(timezone.utc),
            finalizado_por='entrega'
        )
        db.session.add(sim)
        db.session.flush()

        # Adiciona 4 questões objetivas não anuladas
        questoes = Questao.query.filter_by(anulada=False, tipo='objetiva').limit(4).all()
        for idx, q in enumerate(questoes, 1):
            sq = SimuladoQuestao(simulado_id=sim.id, questao_id=q.id, ordem=idx)
            db.session.add(sq)

        # Questão 1: correta
        resp1 = SimuladoResposta(simulado_id=sim.id, questao_id=questoes[0].id, alternativa_marcada=questoes[0].gabarito_oficial)
        # Questão 2: errada
        alt_errada = 'B' if questoes[1].gabarito_oficial != 'B' else 'C'
        resp2 = SimuladoResposta(simulado_id=sim.id, questao_id=questoes[1].id, alternativa_marcada=alt_errada)
        # Questão 3: correta
        resp3 = SimuladoResposta(simulado_id=sim.id, questao_id=questoes[2].id, alternativa_marcada=questoes[2].gabarito_oficial)
        # Questão 4: em branco (sem SimuladoResposta)
        db.session.add_all([resp1, resp2, resp3])
        db.session.commit()
        sim_id = sim.id
        q1_id = questoes[0].id

    # 3 respondidas, 2 corretas, 1 errada, 1 em branco
    # % acerto = 2 / 3 = 67%
    res = auth_client.get(f'/simulados/{sim_id}/resultado')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert '67%' in html
    assert '2 corretas' in html
    assert '<b>1</b>' in html
    assert 'erros' in html
    assert '1' in html and 'em branco' in html

    # Acessa revisão comentada de uma questão do simulado
    res_revisao = auth_client.get(f'/simulados/{sim_id}/questao/{q1_id}')
    assert res_revisao.status_code == 200
    html_rev = res_revisao.data.decode('utf-8')
    assert 'Você acertou!' in html_rev
    assert 'Gabarito comentado' in html_rev


def test_t12_us09_desempenho_painel_e_estado_vazio(auth_client, app):
    """T12: Painel de desempenho com filtros e estado vazio quando não há respostas."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        # Limpa dados para testar estado vazio
        Simulado.query.filter_by(usuario_id=user.id).delete()
        RespostaEstudo.query.filter_by(usuario_id=user.id).delete()
        db.session.commit()

    res_vazio = auth_client.get('/desempenho')
    assert res_vazio.status_code == 200
    assert 'Você ainda não respondeu nenhuma questão' in res_vazio.data.decode('utf-8')

    # Agora adiciona uma resposta no modo estudo e testa se o painel carrega as métricas
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        q = Questao.query.filter_by(anulada=False, tipo='objetiva', area='Redes').first()
        r = RespostaEstudo(
            usuario_id=user.id,
            questao_id=q.id,
            alternativa_marcada=q.gabarito_oficial,
            correta=True
        )
        db.session.add(r)
        db.session.commit()

    res_dados = auth_client.get('/desempenho')
    assert res_dados.status_code == 200
    html = res_dados.data.decode('utf-8')
    assert '100%' in html
    assert 'Redes' in html
    assert 'Estudar área' in html


def test_t05_inicio_mostra_faixa_simulado_ativo_e_ultimo_simulado(auth_client, app):
    """T05: Início exibe faixa de simulado em andamento quando ativo, e card de último simulado."""
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        Simulado.query.filter_by(usuario_id=user.id).delete()
        
        # Cria simulado em andamento
        sim_ativo = Simulado(
            usuario_id=user.id,
            tipo='completo',
            edicao_ano=2023,
            duracao_segundos=14400
        )
        db.session.add(sim_ativo)
        db.session.commit()

    res = auth_client.get('/inicio')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert 'Você tem um simulado em andamento' in html
    assert 'Continuar simulado' in html
