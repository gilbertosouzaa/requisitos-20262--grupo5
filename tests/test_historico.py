from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
from config import TestConfig
from app import create_app
from app.extensions import db
from app.models import (
    Usuario, Questao, RespostaEstudo, Simulado, SimuladoQuestao, SimuladoResposta
)
from app.seed import seed_database, seed_historico_usuario
from app.services.desempenho import (
    calcular_evolucao_semanal,
    calcular_mudancas_4_semanas,
    obter_historico_simulados,
    inicio_semana_sp,
)

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_database()
    # Contexto da aplicação NÃO fica aberto durante as requisições (ver tests/test_usuarios.py)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, senha):
    return client.post('/entrar', data={'email': email, 'senha': senha}, follow_redirects=False)


def _errada(gabarito: str) -> str:
    for letra in ("A", "B", "C", "D", "E"):
        if letra != gabarito:
            return letra
    return "A"


def test_agrupamento_semana_segunda_a_domingo_sao_paulo(app):
    """Domingo 23h30 em Brasília (que já é segunda 02h30 UTC) pertence à semana que termina naquele domingo."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q = Questao.query.filter_by(tipo='objetiva', anulada=False).first()

        # Referência: quarta-feira 2026-11-25 12:00 BRT (semana começa segunda 2026-11-23)
        agora_ref = datetime(2026, 11, 25, 12, 0, tzinfo=SAO_PAULO_TZ).astimezone(timezone.utc)

        # Resposta no domingo 2026-11-22 23:30 BRT (= segunda 2026-11-23 02:30 UTC!)
        domingo_noite_brt = datetime(2026, 11, 22, 23, 30, tzinfo=SAO_PAULO_TZ)
        domingo_noite_utc_naive = domingo_noite_brt.astimezone(timezone.utc).replace(tzinfo=None)

        assert domingo_noite_utc_naive.weekday() == 0  # Em UTC já é segunda-feira!
        assert inicio_semana_sp(domingo_noite_utc_naive).isoformat() == '2026-11-16'

        # Resposta na segunda-feira 2026-11-23 10:00 BRT
        segunda_manha_utc_naive = (
            datetime(2026, 11, 23, 10, 0, tzinfo=SAO_PAULO_TZ)
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
        )

        db.session.add(RespostaEstudo(
            usuario_id=ana.id,
            questao_id=q.id,
            alternativa_marcada=q.gabarito_oficial,
            correta=True,
            respondida_em=domingo_noite_utc_naive
        ))
        db.session.add(RespostaEstudo(
            usuario_id=ana.id,
            questao_id=q.id,
            alternativa_marcada=_errada(q.gabarito_oficial),
            correta=False,
            respondida_em=segunda_manha_utc_naive
        ))
        db.session.commit()

        evolucao = calcular_evolucao_semanal(ana, agora=agora_ref)
        por_inicio = {s['inicio'].isoformat(): s for s in evolucao['semanas']}

        # Domingo 23h30 BRT caiu na semana de 16/11 (100% acerto)
        assert por_inicio['2026-11-16']['respondidas'] == 1
        assert por_inicio['2026-11-16']['percentual'] == 100

        # Segunda 10h00 BRT caiu na semana de 23/11 (0% acerto)
        assert por_inicio['2026-11-23']['respondidas'] == 1
        assert por_inicio['2026-11-23']['percentual'] == 0


def test_anuladas_discursivas_e_branco_fora_do_percentual(app):
    """Anuladas, discursivas e questões em branco não entram no % de acerto (RN03, RN08)."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q_obj_valida = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        q_anulada = Questao.query.filter_by(tipo='objetiva', anulada=True).first()
        q_disc = Questao.query.filter_by(tipo='discursiva', anulada=False).first()

        agora = datetime.now(timezone.utc)
        sem_ant = agora - timedelta(weeks=1)

        # Estudo: 1 objetiva válida correta + 1 anulada + 1 discursiva
        db.session.add_all([
            RespostaEstudo(
                usuario_id=ana.id, questao_id=q_obj_valida.id,
                alternativa_marcada=q_obj_valida.gabarito_oficial, correta=True, respondida_em=agora
            ),
            RespostaEstudo(
                usuario_id=ana.id, questao_id=q_anulada.id,
                alternativa_marcada=_errada(q_anulada.gabarito_oficial), correta=False, respondida_em=agora
            ),
            RespostaEstudo(
                usuario_id=ana.id, questao_id=q_disc.id,
                texto_resposta="Resposta discursiva", correta=None, respondida_em=agora
            ),
        ])

        # Simulado finalizado na semana anterior: 1 objetiva correta, 1 objetiva em branco, 1 anulada errada, 1 discursiva
        q_obj_2 = Questao.query.filter(
            Questao.tipo == 'objetiva', Questao.anulada == False, Questao.id != q_obj_valida.id
        ).first()
        sim = Simulado(
            usuario_id=ana.id, tipo='parcial', componente='especifico', area='todas',
            iniciado_em=sem_ant - timedelta(minutes=20), duracao_segundos=1800,
            finalizado_em=sem_ant, finalizado_por='entrega'
        )
        db.session.add(sim)
        db.session.flush()
        for idx, q in enumerate([q_obj_valida, q_obj_2, q_anulada, q_disc], start=1):
            db.session.add(SimuladoQuestao(simulado_id=sim.id, questao_id=q.id, ordem=idx))

        db.session.add(SimuladoResposta(
            simulado_id=sim.id, questao_id=q_obj_valida.id,
            alternativa_marcada=q_obj_valida.gabarito_oficial
        ))
        # q_obj_2 deixada em branco (sem alternativa_marcada)
        db.session.add(SimuladoResposta(
            simulado_id=sim.id, questao_id=q_anulada.id,
            alternativa_marcada=_errada(q_anulada.gabarito_oficial)
        ))
        db.session.add(SimuladoResposta(
            simulado_id=sim.id, questao_id=q_disc.id,
            texto_resposta="Discursiva no simulado"
        ))
        db.session.commit()

        evolucao = calcular_evolucao_semanal(ana, agora=agora)
        # Apenas 1 objetiva válida na semana atual (100%) e 1 objetiva válida no simulado da semana anterior (100%)
        assert evolucao['ultimas_4_resp'] == 2
        assert evolucao['ultimas_4_pct'] == 100


def test_semana_sem_atividade_vazia_nao_zero(client, app):
    """Semana sem respostas fica vazia (sem ponto no gráfico) e aparece como 'sem atividade'."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        agora = datetime.now(timezone.utc)

        # Atividade na semana atual e há 2 semanas (semana há 1 semana fica vazia)
        db.session.add_all([
            RespostaEstudo(
                usuario_id=ana.id, questao_id=q.id,
                alternativa_marcada=q.gabarito_oficial, correta=True, respondida_em=agora
            ),
            RespostaEstudo(
                usuario_id=ana.id, questao_id=q.id,
                alternativa_marcada=_errada(q.gabarito_oficial), correta=False,
                respondida_em=agora - timedelta(weeks=2)
            ),
        ])
        db.session.commit()

        evolucao = calcular_evolucao_semanal(ana, agora=agora)
        assert evolucao['semanas'][-1]['tem_atividade'] is True
        assert evolucao['semanas'][-2]['tem_atividade'] is False
        assert evolucao['semanas'][-2]['percentual'] is None
        assert len(evolucao['svg']['pontos']) == 2
        # Semanas isoladas por lacuna não formam polyline contínuo ligando através da lacuna
        assert len(evolucao['svg']['segmentos']) == 0

    login(client, 'ana@teste.com', '12345678')
    res = client.get('/desempenho')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'sem atividade' in html


def test_filtros_origem_e_componente_aplicados_a_evolucao(client, app):
    """Filtros de Origem e Componente valem também para a evolução semanal e endpoint parcial."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q_fg = Questao.query.filter_by(componente='formacao_geral', tipo='objetiva', anulada=False).first()
        q_esp = Questao.query.filter_by(componente='especifico', tipo='objetiva', anulada=False).first()
        agora = datetime.now(timezone.utc)

        # Estudo FG em 2 semanas (100%)
        db.session.add_all([
            RespostaEstudo(
                usuario_id=ana.id, questao_id=q_fg.id,
                alternativa_marcada=q_fg.gabarito_oficial, correta=True, respondida_em=agora
            ),
            RespostaEstudo(
                usuario_id=ana.id, questao_id=q_fg.id,
                alternativa_marcada=q_fg.gabarito_oficial, correta=True, respondida_em=agora - timedelta(weeks=1)
            ),
        ])
        # Estudo Específico apenas em 1 semana (0%)
        db.session.add(RespostaEstudo(
            usuario_id=ana.id, questao_id=q_esp.id,
            alternativa_marcada=_errada(q_esp.gabarito_oficial), correta=False, respondida_em=agora
        ))
        db.session.commit()

    login(client, 'ana@teste.com', '12345678')

    # Componente FG: tem 2 semanas com atividade -> exibe SVG
    res_fg = client.get('/api/desempenho/evolucao?origem=estudo&componente=formacao_geral&evolucao_area=geral')
    assert res_fg.status_code == 200
    assert '<svg' in res_fg.get_data(as_text=True)

    # Componente Específico: só 1 semana -> não exibe SVG
    res_esp = client.get('/api/desempenho/evolucao?origem=estudo&componente=especifico&evolucao_area=geral')
    assert res_esp.status_code == 200
    html_esp = res_esp.get_data(as_text=True)
    assert '<svg' not in html_esp
    assert 'Continue estudando: o gráfico aparece a partir de 2 semanas com respostas.' in html_esp

    # Origem só simulados: 0 semanas -> não exibe SVG
    res_sim = client.get('/api/desempenho/evolucao?origem=simulados&componente=todos&evolucao_area=geral')
    assert '<svg' not in res_sim.get_data(as_text=True)


def test_regra_duas_semanas_para_exibir_grafico(client, app):
    """Com menos de 2 semanas com atividade, exibe mensagem orientativa em vez do gráfico."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        agora = datetime.now(timezone.utc)
        db.session.add(RespostaEstudo(
            usuario_id=ana.id, questao_id=q.id,
            alternativa_marcada=q.gabarito_oficial, correta=True, respondida_em=agora
        ))
        db.session.commit()

    login(client, 'ana@teste.com', '12345678')
    res1 = client.get('/desempenho')
    html1 = res1.get_data(as_text=True)
    assert 'Continue estudando: o gráfico aparece a partir de 2 semanas com respostas.' in html1
    assert 'class="evolucao-svg"' not in html1

    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        db.session.add(RespostaEstudo(
            usuario_id=ana.id, questao_id=q.id,
            alternativa_marcada=q.gabarito_oficial, correta=True,
            respondida_em=datetime.now(timezone.utc) - timedelta(weeks=1)
        ))
        db.session.commit()

    res2 = client.get('/desempenho')
    html2 = res2.get_data(as_text=True)
    assert 'class="evolucao-svg"' in html2
    assert 'Ver dados do gráfico' in html2


def test_comparacao_4_mais_4_semanas_minimo_5_por_periodo(client, app):
    """Área só entra na comparação 4+4 se tiver >= 5 objetivas respondidas em CADA período."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q_redes = Questao.query.filter_by(area='Redes', tipo='objetiva', anulada=False).first()
        q_bd = Questao.query.filter_by(area='Banco de Dados', tipo='objetiva', anulada=False).first()
        q_alg = Questao.query.filter_by(area='Algoritmos', tipo='objetiva', anulada=False).first()

        agora = datetime.now(timezone.utc)
        ant_dt = agora - timedelta(weeks=5)
        rec_dt = agora - timedelta(weeks=1)

        # Redes: 5 nas anteriores (2/5 = 40%) e 5 nas últimas (4/5 = 80%) -> entra em Melhorou (+40)
        for i in range(5):
            ok_ant = i < 2
            ok_rec = i < 4
            db.session.add(RespostaEstudo(
                usuario_id=ana.id, questao_id=q_redes.id,
                alternativa_marcada=q_redes.gabarito_oficial if ok_ant else _errada(q_redes.gabarito_oficial),
                correta=ok_ant, respondida_em=ant_dt + timedelta(minutes=i)
            ))
            db.session.add(RespostaEstudo(
                usuario_id=ana.id, questao_id=q_redes.id,
                alternativa_marcada=q_redes.gabarito_oficial if ok_rec else _errada(q_redes.gabarito_oficial),
                correta=ok_rec, respondida_em=rec_dt + timedelta(minutes=i)
            ))

        # Banco de Dados: 5 nas anteriores (4/5 = 80%) e 5 nas últimas (1/5 = 20%) -> entra em Precisa de atenção (-60)
        for i in range(5):
            ok_ant = i < 4
            ok_rec = i < 1
            db.session.add(RespostaEstudo(
                usuario_id=ana.id, questao_id=q_bd.id,
                alternativa_marcada=q_bd.gabarito_oficial if ok_ant else _errada(q_bd.gabarito_oficial),
                correta=ok_ant, respondida_em=ant_dt + timedelta(minutes=20 + i)
            ))
            db.session.add(RespostaEstudo(
                usuario_id=ana.id, questao_id=q_bd.id,
                alternativa_marcada=q_bd.gabarito_oficial if ok_rec else _errada(q_bd.gabarito_oficial),
                correta=ok_rec, respondida_em=rec_dt + timedelta(minutes=20 + i)
            ))

        # Algoritmos: apenas 4 nas anteriores e 5 nas últimas -> NÃO pode entrar!
        for i in range(4):
            db.session.add(RespostaEstudo(
                usuario_id=ana.id, questao_id=q_alg.id,
                alternativa_marcada=q_alg.gabarito_oficial, correta=True,
                respondida_em=ant_dt + timedelta(minutes=40 + i)
            ))
        for i in range(5):
            db.session.add(RespostaEstudo(
                usuario_id=ana.id, questao_id=q_alg.id,
                alternativa_marcada=_errada(q_alg.gabarito_oficial), correta=False,
                respondida_em=rec_dt + timedelta(minutes=40 + i)
            ))
        db.session.commit()

        mudancas = calcular_mudancas_4_semanas(ana, agora=agora)
        assert mudancas['tem_dados'] is True
        assert [m['area'] for m in mudancas['melhorou']] == ['Redes']
        assert mudancas['melhorou'][0]['diff'] == 40
        assert [a['area'] for a in mudancas['atencao']] == ['Banco de Dados']
        assert mudancas['atencao'][0]['diff'] == -60

    login(client, 'ana@teste.com', '12345678')
    res_inicio = client.get('/inicio')
    html_inicio = res_inicio.get_data(as_text=True)
    assert 'Ver evolução' in html_inicio
    assert '/desempenho#evolucao' in html_inicio


def test_variacao_simulados_mesmo_tipo(app):
    """Variação compara apenas simulados finalizados do mesmo tipo (completo vs parcial)."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q1 = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        agora = datetime.now(timezone.utc)

        def criar_sim(tipo, horas_atras, acertar):
            fin = agora - timedelta(hours=horas_atras)
            s = Simulado(
                usuario_id=ana.id, tipo=tipo, edicao_ano=2023 if tipo == 'completo' else None,
                componente='especifico' if tipo == 'parcial' else None, area='Redes' if tipo == 'parcial' else None,
                iniciado_em=fin - timedelta(minutes=30), duracao_segundos=3600,
                finalizado_em=fin, finalizado_por='entrega'
            )
            db.session.add(s)
            db.session.flush()
            db.session.add(SimuladoQuestao(simulado_id=s.id, questao_id=q1.id, ordem=1))
            db.session.add(SimuladoResposta(
                simulado_id=s.id, questao_id=q1.id,
                alternativa_marcada=q1.gabarito_oficial if acertar else _errada(q1.gabarito_oficial)
            ))
            return s

        # Cronologia: Parcial 1 (0%) -> Completo 1 (100%) -> Parcial 2 (100%)
        p1 = criar_sim('parcial', 30, False)
        c1 = criar_sim('completo', 20, True)
        p2 = criar_sim('parcial', 10, True)
        db.session.commit()

        hist = obter_historico_simulados(ana)
        por_id = {it['id']: it for it in hist['itens']}
        assert por_id[p1.id]['variacao'] is None
        assert por_id[c1.id]['variacao'] is None  # Primeiro completo, não compara com p1!
        assert por_id[p2.id]['variacao'] == 100  # Compara com p1 (0% -> 100%)


def test_simulado_em_andamento_fora_dos_calculos_e_topo_historico(client, app):
    """Simulado em andamento não entra nos cálculos e aparece destacado no topo de /simulados/historico."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q1 = Questao.query.filter_by(tipo='objetiva', anulada=False).first()

        sim_ativo = Simulado(
            usuario_id=ana.id, tipo='parcial', componente='especifico', area='Redes',
            iniciado_em=datetime.now(timezone.utc) - timedelta(minutes=5),
            duracao_segundos=3600, finalizado_em=None
        )
        db.session.add(sim_ativo)
        db.session.flush()
        db.session.add(SimuladoQuestao(simulado_id=sim_ativo.id, questao_id=q1.id, ordem=1))
        db.session.add(SimuladoResposta(
            simulado_id=sim_ativo.id, questao_id=q1.id, alternativa_marcada=q1.gabarito_oficial
        ))
        db.session.commit()

        evolucao = calcular_evolucao_semanal(ana)
        assert evolucao['ultimas_4_resp'] == 0

    login(client, 'ana@teste.com', '12345678')
    res = client.get('/simulados/historico')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Simulado em andamento' in html
    assert 'Continuar' in html
    assert 'Você ainda não concluiu nenhum simulado.' in html


def test_privacidade_outro_usuario_nao_aparece(client, app):
    """Dados de outro usuário nunca aparecem no desempenho ou histórico (RNF04)."""
    with app.app_context():
        bruno = Usuario.query.filter_by(email='bruno@teste.com').first()
        q = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        agora = datetime.now(timezone.utc)

        # Bruno tem respostas em 2 semanas e 1 simulado finalizado
        db.session.add_all([
            RespostaEstudo(
                usuario_id=bruno.id, questao_id=q.id,
                alternativa_marcada=q.gabarito_oficial, correta=True, respondida_em=agora
            ),
            RespostaEstudo(
                usuario_id=bruno.id, questao_id=q.id,
                alternativa_marcada=q.gabarito_oficial, correta=True, respondida_em=agora - timedelta(weeks=1)
            ),
        ])
        sim_b = Simulado(
            usuario_id=bruno.id, tipo='parcial', componente='especifico', area='Sistemas Embarcados',
            iniciado_em=agora - timedelta(minutes=20), duracao_segundos=1800,
            finalizado_em=agora - timedelta(minutes=5), finalizado_por='entrega'
        )
        db.session.add(sim_b)
        db.session.flush()
        db.session.add(SimuladoQuestao(simulado_id=sim_b.id, questao_id=q.id, ordem=1))
        db.session.add(SimuladoResposta(
            simulado_id=sim_b.id, questao_id=q.id, alternativa_marcada=q.gabarito_oficial
        ))
        db.session.commit()

    # Ana não tem nenhuma resposta -> deve ver estado vazio
    login(client, 'ana@teste.com', '12345678')
    res_des = client.get('/desempenho')
    assert 'Você ainda não respondeu nenhuma questão' in res_des.get_data(as_text=True)

    res_hist = client.get('/simulados/historico')
    assert 'Você ainda não concluiu nenhum simulado.' in res_hist.get_data(as_text=True)
    assert 'Sistemas Embarcados' not in res_hist.get_data(as_text=True)


def test_historico_paginacao_e_filtro_tipo(client, app):
    """Histórico pagina de 10 em 10 e filtra por tipo (Todos / Completos / Parciais)."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        agora = datetime.now(timezone.utc)

        for i in range(12):
            tipo = 'completo' if i < 2 else 'parcial'
            fin = agora - timedelta(days=i + 1)
            s = Simulado(
                usuario_id=ana.id, tipo=tipo, edicao_ano=2023 if tipo == 'completo' else None,
                componente='especifico' if tipo == 'parcial' else None, area='Redes' if tipo == 'parcial' else None,
                iniciado_em=fin - timedelta(minutes=25), duracao_segundos=3600,
                finalizado_em=fin, finalizado_por='entrega' if i % 2 == 0 else 'tempo'
            )
            db.session.add(s)
            db.session.flush()
            db.session.add(SimuladoQuestao(simulado_id=s.id, questao_id=q.id, ordem=1))
            db.session.add(SimuladoResposta(
                simulado_id=s.id, questao_id=q.id, alternativa_marcada=q.gabarito_oficial
            ))
        db.session.commit()

    login(client, 'ana@teste.com', '12345678')

    # Página 1 de Todos: 10 linhas
    p1 = client.get('/simulados/historico?tipo=todos&pagina=1').get_data(as_text=True)
    assert '12 simulados encontrados' in p1
    assert p1.count('Ver resultado') == 10

    # Página 2 de Todos: 2 linhas
    p2 = client.get('/simulados/historico?tipo=todos&pagina=2').get_data(as_text=True)
    assert p2.count('Ver resultado') == 2

    # Filtro Completos: 2 linhas
    comp = client.get('/simulados/historico?tipo=completo').get_data(as_text=True)
    assert '2 simulados encontrados' in comp
    assert comp.count('Ver resultado') == 2

    # Filtro Parciais: 10 linhas
    parc = client.get('/simulados/historico?tipo=parcial').get_data(as_text=True)
    assert '10 simulados encontrados' in parc
    assert parc.count('Ver resultado') == 10


def test_seed_historico_idempotente(app):
    """Comando seed-historico cria dados na 1ª execução e não duplica na 2ª."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        assert seed_historico_usuario('ana@teste.com') is True

        qtd_estudo_1 = RespostaEstudo.query.filter_by(usuario_id=ana.id).count()
        qtd_sim_1 = Simulado.query.filter_by(usuario_id=ana.id).count()
        assert qtd_estudo_1 > 0
        assert qtd_sim_1 == 5

        # 2ª execução não duplica
        assert seed_historico_usuario('ana@teste.com') is False
        assert RespostaEstudo.query.filter_by(usuario_id=ana.id).count() == qtd_estudo_1
        assert Simulado.query.filter_by(usuario_id=ana.id).count() == qtd_sim_1


@pytest.mark.parametrize("segundos,esperado", [
    (0, "menos de 1 min"),
    (59, "menos de 1 min"),
    (60, "1 min"),
    (2280, "38 min"),
    (3599, "59 min"),
    (3600, "1h00"),
    (3660, "1h01"),
    (11700, "3h15"),
    (14400, "4h00"),
])
def test_formatar_tempo_legivel_bordas(segundos, esperado):
    """Testa todos os casos de borda da formatação legível de tempo (B2)."""
    from app.services.desempenho import formatar_tempo_legivel
    assert formatar_tempo_legivel(segundos) == esperado


def test_variacao_simulados_parciais_mesmo_grupo_componente_area(app):
    """Parcial de Redes compara apenas com parcial anterior de Redes, não com Algoritmos (B1)."""
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q1 = Questao.query.filter_by(tipo='objetiva', anulada=False).first()
        agora = datetime.now(timezone.utc)

        def criar_parcial(area, horas_atras, acertar):
            fin = agora - timedelta(hours=horas_atras)
            s = Simulado(
                usuario_id=ana.id, tipo='parcial',
                componente='especifico', area=area,
                iniciado_em=fin - timedelta(minutes=20), duracao_segundos=3600,
                finalizado_em=fin, finalizado_por='entrega'
            )
            db.session.add(s)
            db.session.flush()
            db.session.add(SimuladoQuestao(simulado_id=s.id, questao_id=q1.id, ordem=1))
            db.session.add(SimuladoResposta(
                simulado_id=s.id, questao_id=q1.id,
                alternativa_marcada=q1.gabarito_oficial if acertar else _errada(q1.gabarito_oficial)
            ))
            return s

        # Cronologia: Redes (0%) -> Algoritmos (100%) -> Redes (100%) -> todas (0%)
        r1 = criar_parcial('Redes', 40, False)
        a1 = criar_parcial('Algoritmos', 30, True)
        r2 = criar_parcial('Redes', 20, True)
        t1 = criar_parcial('todas', 10, False)
        db.session.commit()

        hist = obter_historico_simulados(ana)
        por_id = {it['id']: it for it in hist['itens']}
        assert por_id[r1.id]['variacao'] is None
        assert por_id[a1.id]['variacao'] is None  # Primeiro de Algoritmos, não compara com Redes!
        assert por_id[r2.id]['variacao'] == 100   # Compara com r1 (0% -> 100%)
        assert por_id[t1.id]['variacao'] is None  # 'todas' é grupo próprio


def test_simulado_rapido_10_questoes_e_retomada(client, app):
    """Atalho Simulado rápido cria parcial de 10 questões (1h00, Ambos, todas) ou retoma ativo."""
    login(client, 'ana@teste.com', '12345678')
    res = client.post('/simulados/rapido', follow_redirects=False)
    assert res.status_code == 302
    assert '/simulados/' in res.headers['Location']

    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        sim = Simulado.query.filter_by(usuario_id=ana.id, finalizado_em=None).first()
        assert sim is not None
        assert sim.tipo == 'parcial'
        assert sim.componente == 'ambos'
        assert sim.area == 'todas'
        assert sim.duracao_segundos == 3600  # 10 * 6 min = 1h00
        assert len(sim.questoes_assoc) == 10
        sim_id = sim.id

    # Se já houver simulado em andamento, leva até ele
    res2 = client.post('/simulados/rapido', follow_redirects=False)
    assert res2.status_code == 302
    assert f'/simulados/{sim_id}' in res2.headers['Location']
