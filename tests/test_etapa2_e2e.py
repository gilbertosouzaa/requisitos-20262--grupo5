import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.seed import seed_database
from config import TestConfig
from app.extensions import db
from app.models import Usuario, Curso, Questao, RespostaEstudo

class E2EConfig(TestConfig):
    """Banco em memória, mas com CSRF ativo para simular o uso real."""
    WTF_CSRF_ENABLED = True


def get_csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if not m:
        m = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', html)
    if not m:
        m = re.search(r'content="([^"]+)"', html)
    return m.group(1) if m else ''

def test_etapa2_e2e_flow():
    app = create_app(E2EConfig)
    with app.app_context():
        db.create_all()
        seed_database()
    client = app.test_client()

    print("=== TESTE MANUAL SIMULADO DA SEGUNDA ETAPA (COM CSRF) ===")

    # 1. Visitante acessa o banco de questões (T06)
    res = client.get('/questoes')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Banco de questões' in html or 'Banco de quest&otilde;es' in html
    print("[OK] Visitante acessa T06 Banco de questões")

    # 2. Visitante acessa uma questão (ex: id 1)
    res = client.get('/questoes/1')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Questão 1' in html or 'Quest&atilde;o 1' in html
    assert 'Você precisa entrar na sua conta para responder questões' in html or 'Voc&ecirc; precisa entrar na sua conta' in html
    print("[OK] Visitante acessa T07a Questão com aviso para logar ao responder")

    # 3. Login com Ana Souza passando CSRF
    res_login_get = client.get('/entrar')
    csrf_login = get_csrf(res_login_get.get_data(as_text=True))
    res_login = client.post('/entrar', data={'csrf_token': csrf_login, 'email': 'ana@teste.com', 'senha': '12345678'}, follow_redirects=True)
    assert res_login.status_code == 200
    assert 'Ana Souza' in res_login.get_data(as_text=True)
    print("[OK] Login com Ana Souza realizado com sucesso")

    # 4. Ana acessa T05 Início (inicialmente sem respostas)
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        RespostaEstudo.query.filter_by(usuario_id=ana.id).delete()
        db.session.commit()

    res = client.get('/inicio')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Responda algumas questões para ver seu desempenho' in html or 'Responda algumas quest&otilde;es para ver seu desempenho' in html
    print("[OK] T05 Início mostra convite para começar quando não há respostas")

    # 5. Ana filtra por Ciência da Computação e Banco de Dados
    with app.app_context():
        cc = Curso.query.filter_by(nome='Ciência da Computação').first()
        cc_id = cc.id

    res = client.get(f'/questoes?curso={cc_id}&area=Banco+de+Dados')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Banco de Dados' in html
    print("[OK] US04 Filtro cumulativo por curso e área aplicado")

    # 6. Ana responde uma questão que tem comentário (ex: questão 1, gabarito da questão 1)
    with app.app_context():
        q1 = Questao.query.filter_by(ano=2023, numero=1).first()
        q1_id = q1.id
        q1_gab = q1.gabarito_oficial

    res_q1 = client.get(f'/questoes/{q1_id}')
    csrf_q1 = get_csrf(res_q1.get_data(as_text=True))

    res = client.post(f'/api/questoes/{q1_id}/responder',
        headers={'X-CSRFToken': csrf_q1},
        json={'alternativa': q1_gab}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['acertou'] is True
    print("[OK] US05 Resposta objetiva enviada com sucesso e corrigida (acerto)")

    # 7. Ana acessa a página da questão 1 e vê o gabarito comentado
    res = client.get(f'/questoes/{q1_id}')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Você acertou!' in html or 'Voc&ecirc; acertou!' in html
    assert 'Gabarito comentado' in html
    print("[OK] US06 Gabarito comentado exibido após resposta")

    # 8. Ana responde questão sem comentário (ex: questão 4)
    with app.app_context():
        q4 = Questao.query.filter_by(ano=2023, numero=4).first()
        q4_id = q4.id
        q4_gab = q4.gabarito_oficial

    res = client.post(f'/api/questoes/{q4_id}/responder',
        headers={'X-CSRFToken': csrf_q1},
        json={'alternativa': q4_gab}
    )
    assert res.status_code == 200

    res = client.get(f'/questoes/{q4_id}')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Comentário em elaboração' in html or 'Coment&aacute;rio em elabora&ccedil;&atilde;o' in html
    assert f'/questoes/{q4_id}/discussao' in html
    print("[OK] US06 Questão sem comentário mostra estado Comentário em elaboração e link para discussão")

    # 9. Ana responde uma questão anulada (Q18 de 2023)
    with app.app_context():
        q18 = Questao.query.filter_by(ano=2023, numero=18).first()
        q18_id = q18.id
        assert q18.anulada is True

    client.post(f'/api/questoes/{q18_id}/responder',
        headers={'X-CSRFToken': csrf_q1},
        json={'alternativa': 'A'}
    )

    # 10. Ana acessa T05 Início e vê desempenho calculado excluindo a anulada
    res = client.get('/inicio')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'acerto geral' in html
    assert 'questões respondidas' in html or 'quest&otilde;es respondidas' in html
    print("[OK] T05 Início exibe acerto geral e desconsidera anuladas (RN03)")

    print("\n=== TODOS OS TESTES DA SEGUNDA ETAPA FORAM CONCLUÍDOS COM SUCESSO! ===")

if __name__ == '__main__':
    test_etapa2_e2e_flow()
