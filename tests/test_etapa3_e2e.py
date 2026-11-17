import pytest
import re
from app import create_app
from app.extensions import db
from app.models import Usuario, Curso, Questao, Simulado, SimuladoQuestao, SimuladoResposta
from app.seed import seed_database
from config import TestConfig


def extract_csrf(html):
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    return match.group(1) if match else ''


def test_etapa3_complete_e2e_flow():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.create_all()
        seed_database()

    print("\n--- INICIANDO TESTE E2E DA ETAPA 3 ---")

    # 1. Login com Ana Souza
    res_login_page = client.get('/entrar')
    csrf_login = extract_csrf(res_login_page.get_data(as_text=True))
    res_login = client.post('/entrar', data={
        'csrf_token': csrf_login,
        'email': 'ana@teste.com',
        'senha': '12345678'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert 'Olá, Ana Souza' in res_login.get_data(as_text=True)
    print("[OK] Login realizado com sucesso")

    # 2. Tela T08 - Montar Simulado
    res_novo = client.get('/simulados/novo')
    assert res_novo.status_code == 200
    html_novo = res_novo.get_data(as_text=True)
    assert 'Novo simulado' in html_novo
    assert '2 questões anuladas' in html_novo
    assert '38' in html_novo
    print("[OK] T08 Montar simulado carregada com dados de edições e aviso de questões anuladas (RN03)")

    # 3. Iniciar Prova Completa ENADE 2023
    csrf_novo = extract_csrf(html_novo)
    res_criar = client.post('/simulados/novo', data={
        'csrf_token': csrf_novo,
        'tipo': 'completo',
        'edicao': '2023'
    }, follow_redirects=True)
    assert res_criar.status_code == 200
    html_sim = res_criar.get_data(as_text=True)
    assert 'Simulado · Prova completa ENADE 2023' in html_sim
    assert 'role="timer"' in html_sim
    print("[OK] Simulado completo criado e redirecionado para T09")

    # Obter id do simulado
    with app.app_context():
        user = Usuario.query.filter_by(email='ana@teste.com').first()
        sim = Simulado.query.filter_by(usuario_id=user.id, finalizado_em=None).first()
        assert sim is not None
        sim_id = sim.id
        assert len(sim.questoes_assoc) == 38
        q1_id = sim.questoes_assoc[0].questao_id
        q1_gabarito = sim.questoes_assoc[0].questao.gabarito_oficial

    # 4. API T09 - Sem gabarito (RN04)
    res_api = client.get(f'/api/simulados/{sim_id}')
    assert res_api.status_code == 200
    api_data = res_api.get_json()
    assert api_data['total_questoes'] == 38
    for q_item in api_data['questoes']:
        assert 'gabarito_oficial' not in q_item
        assert 'comentario_correta' not in q_item
        assert 'padrao_resposta' not in q_item
    print("[OK] RN04: API /api/simulados/<id> não expõe gabarito nem comentários")

    # 5. RNF07: Salvar respostas via PUT
    res_put = client.put(f'/api/simulados/{sim_id}/respostas/{q1_id}', json={
        'alternativa_marcada': q1_gabarito
    })
    assert res_put.status_code == 200
    assert res_put.get_json()['sucesso'] is True
    print("[OK] RNF07: Salvamento automático via PUT efetuado com sucesso")

    # 6. T05: Início com simulado ativo
    res_inicio = client.get('/inicio')
    assert res_inicio.status_code == 200
    html_inicio = res_inicio.get_data(as_text=True)
    assert 'Você tem um simulado em andamento' in html_inicio
    assert 'Continuar simulado' in html_inicio
    print("[OK] T05 Início exibe faixa de simulado ativo com link para continuar")

    # 7. T10 / RF12: Finalização do simulado via API
    res_fin = client.post(f'/api/simulados/{sim_id}/finalizar', json={
        'motivo': 'entrega'
    })
    assert res_fin.status_code == 200
    assert res_fin.get_json()['sucesso'] is True
    redirect_url = res_fin.get_json()['redirect_url']
    print("[OK] RF12: Finalização do simulado via API concluída")

    # 8. RN07: Tentativa de alterar resposta após finalização deve retornar 409
    res_put_depois = client.put(f'/api/simulados/{sim_id}/respostas/{q1_id}', json={
        'alternativa_marcada': 'A'
    })
    assert res_put_depois.status_code == 409
    print("[OK] RN07: Alteração em simulado finalizado rejeitada com 409 Conflict")

    # 9. T11: Resultado do Simulado (US08, RN08, RN09)
    res_res = client.get(redirect_url)
    assert res_res.status_code == 200
    html_res = res_res.get_data(as_text=True)
    assert 'Resultado · Prova completa ENADE 2023' in html_res
    assert '100%' in html_res  # 1 respondida e 1 correta
    assert 'Acerto por área' in html_res
    assert 'Correção questão a questão' in html_res
    print("[OK] T11 Resultado do simulado renderizado com KPIs, áreas e tabela de revisão")

    # 10. Revisão de questão do simulado
    res_rev = client.get(f'/simulados/{sim_id}/questao/{q1_id}')
    assert res_rev.status_code == 200
    html_rev = res_rev.get_data(as_text=True)
    assert 'Você acertou!' in html_rev
    assert 'Gabarito comentado' in html_rev
    print("[OK] Tela de revisão comentada de questão no simulado funcional")

    # 11. T12: Painel de Desempenho (RF15, US09)
    res_desemp = client.get('/desempenho')
    assert res_desemp.status_code == 200
    html_desemp = res_desemp.get_data(as_text=True)
    assert 'Meu desempenho' in html_desemp
    assert '100%' in html_desemp
    assert 'simulados concluídos' in html_desemp
    assert 'Acerto por área' in html_desemp
    print("[OK] T12 Painel de desempenho exibe métricas agregadas por área")

    # 12. T05: Início com Último Simulado
    res_inicio_fim = client.get('/inicio')
    assert res_inicio_fim.status_code == 200
    html_inicio_fim = res_inicio_fim.get_data(as_text=True)
    assert 'Último simulado' in html_inicio_fim
    assert 'Prova completa ENADE 2023' in html_inicio_fim
    assert 'Ver resultado' in html_inicio_fim
    print("[OK] T05 Início exibe card do último simulado concluído")

    with app.app_context():
        db.session.remove()
        db.drop_all()
    print("--- TESTE E2E DA ETAPA 3 FINALIZADO COM SUCESSO! ---\n")
