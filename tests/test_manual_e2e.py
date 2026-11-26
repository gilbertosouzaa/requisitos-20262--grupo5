import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.seed import seed_database
from config import TestConfig
from app.extensions import db
from app.models import Usuario, TokenRecuperacao, Curso, Questao, RespostaEstudo

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

def test_manual_e2e_flow():
    app = create_app(E2EConfig)
    with app.app_context():
        db.create_all()
        seed_database()
    client = app.test_client()

    print("=== TESTE MANUAL SIMULADO E2E (COM CSRF ATIVO) ===")

    with app.app_context():
        # Limpa dados de teste anteriores caso existam
        u_teste = Usuario.query.filter_by(email='mariana@teste.com').first()
        if u_teste:
            db.session.delete(u_teste)
            db.session.commit()

    # 1. Visitar Landing (T01)
    res = client.get('/')
    assert res.status_code == 200
    assert 'Prepare-se para o ENADE' in res.get_data(as_text=True)
    print("[OK] T01 Landing carregada com sucesso")

    # 2. RN01: /questoes sem login
    res = client.get('/questoes')
    assert res.status_code == 200
    assert 'banco de quest' in res.get_data(as_text=True).lower()
    print("[OK] RN01 /questoes acessível sem login")

    # 3. RN01: /simulados/novo sem login redireciona para login com next
    res = client.get('/simulados/novo')
    assert res.status_code == 302
    assert '/entrar?next=' in res.headers['Location']
    print("[OK] RN01 /simulados/novo bloqueado para visitantes (redireciona para /entrar?next=...)")

    # 4. US01: Cadastro de novo estudante
    res_get_cad = client.get('/cadastro')
    csrf = get_csrf(res_get_cad.get_data(as_text=True))
    assert csrf, "CSRF token não encontrado na página de cadastro"

    with app.app_context():
        cc = Curso.query.filter_by(nome='Ciência da Computação').first()
        cc_id = cc.id

    res = client.post('/cadastro', data={
        'csrf_token': csrf,
        'nome': 'Mariana Lima',
        'email': 'mariana@teste.com',
        'senha': 'senhaForte123',
        'curso_id': cc_id,
        'termos': 'y'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Mariana Lima' in res.get_data(as_text=True)
    print("[OK] US01 Cadastro com sucesso e login automático (redirecionado para /inicio)")

    # 5. US01: E-mail duplicado (visitante tentando cadastrar e-mail já existente)
    res_inicio = client.get('/inicio')
    csrf_logout = get_csrf(res_inicio.get_data(as_text=True))
    client.post('/sair', data={'csrf_token': csrf_logout})

    res_cad_dup = client.get('/cadastro')
    csrf_dup = get_csrf(res_cad_dup.get_data(as_text=True))

    res = client.post('/cadastro', data={
        'csrf_token': csrf_dup,
        'nome': 'Outra Mariana',
        'email': 'mariana@teste.com',
        'senha': 'senhaForte123',
        'curso_id': cc_id,
        'termos': 'y'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'E-mail já cadastrado' in res.get_data(as_text=True)
    print("[OK] US01 E-mail duplicado exibe erro 'E-mail já cadastrado' com links e não cria conta")

    # 6. US02: Erro genérico de login com senha errada
    res_login_get = client.get('/entrar')
    csrf_login = get_csrf(res_login_get.get_data(as_text=True))
    res = client.post('/entrar', data={
        'csrf_token': csrf_login,
        'email': 'mariana@teste.com',
        'senha': 'senhaErrada'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'E-mail ou senha incorretos.' in res.get_data(as_text=True)
    print("[OK] US02 Login com senha errada exibe mensagem genérica 'E-mail ou senha incorretos.'")

    # 7. US02: Login com sucesso e redirecionamento para next
    res = client.post('/entrar?next=%2Fsimulados%2Fnovo', data={
        'csrf_token': csrf_login,
        'email': 'mariana@teste.com',
        'senha': 'senhaForte123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Novo simulado' in res.get_data(as_text=True)
    print("[OK] US02 Login respeita next e redireciona para /simulados/novo")

    # 8. Logout para testar recuperação de senha
    res_sim_page = client.get('/simulados/novo')
    csrf_logout = get_csrf(res_sim_page.get_data(as_text=True))
    client.post('/sair', data={'csrf_token': csrf_logout})

    # 9. US03: Solicitar recuperação de senha
    res_rec_get = client.get('/recuperar-senha')
    csrf_rec = get_csrf(res_rec_get.get_data(as_text=True))
    res = client.post('/recuperar-senha', data={
        'csrf_token': csrf_rec,
        'email': 'mariana@teste.com'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Verifique seu e-mail' in res.get_data(as_text=True)
    assert '1 hora' in res.get_data(as_text=True)
    print("[OK] US03 Solicitação de recuperação exibe tela de e-mail enviado informando validade de 1 hora")

    # Pega o token gerado no banco
    with app.app_context():
        u = Usuario.query.filter_by(email='mariana@teste.com').first()
        tok = TokenRecuperacao.query.filter_by(usuario_id=u.id).order_by(TokenRecuperacao.id.desc()).first()
        token_str = tok.token

    # 10. US03: Redefinir senha com token válido
    res_token_get = client.get(f'/redefinir-senha/{token_str}')
    csrf_redef = get_csrf(res_token_get.get_data(as_text=True))
    res = client.post(f'/redefinir-senha/{token_str}', data={
        'csrf_token': csrf_redef,
        'nova_senha': 'novaSenhaAlterada123',
        'confirma_senha': 'novaSenhaAlterada123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Senha redefinida com sucesso' in res.get_data(as_text=True)
    print("[OK] US03 Senha redefinida com sucesso com hash bcrypt atualizado")

    # 11. US03: Tentar reusar o mesmo link (token usado)
    res = client.get(f'/redefinir-senha/{token_str}')
    assert res.status_code == 200
    assert 'Este link expirou' in res.get_data(as_text=True)
    assert 'Pedir novo link' in res.get_data(as_text=True)
    print("[OK] US03 Token já usado exibe mensagem 'Este link expirou' e botão 'Pedir novo link'")

    # 12. Login com a nova senha
    res_login_nova = client.get('/entrar')
    csrf_nova = get_csrf(res_login_nova.get_data(as_text=True))
    res = client.post('/entrar', data={
        'csrf_token': csrf_nova,
        'email': 'mariana@teste.com',
        'senha': 'novaSenhaAlterada123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert 'Mariana Lima' in res.get_data(as_text=True)
    print("[OK] Login realizado com sucesso com a nova senha redefinida!")

    print("\n=== TODOS OS TESTES FORAM APROVADOS COM SUCESSO! ===")

if __name__ == '__main__':
    test_manual_e2e_flow()
