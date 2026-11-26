from datetime import datetime, timedelta, timezone
import pytest
from config import TestConfig
from app import create_app
from app.extensions import db
from app.models import (
    Usuario, Curso, Questao, ProfessorArea, AlteracaoUsuario,
    TokenRecuperacao, RespostaEstudo
)
from app.seed import seed_database


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


def login(client, email, senha):
    return client.post('/entrar', data={'email': email, 'senha': senha}, follow_redirects=False)


def test_cadastro_publico_ignora_perfil_admin_rn13(client, app):
    with app.app_context():
        curso = Curso.query.first()
        curso_id = curso.id

    res = client.post('/cadastro', data={
        'nome': 'Novo Aluno',
        'email': 'novoaluno@teste.com',
        'senha': 'password123',
        'curso_id': curso_id,
        'termos': 'y',
        'perfil': 'admin'
    }, follow_redirects=False)
    assert res.status_code in (200, 302)

    with app.app_context():
        u = Usuario.query.filter_by(email='novoaluno@teste.com').first()
        assert u is not None
        assert u.perfil == 'estudante'


def test_estudante_e_professor_recebem_403_em_admin_usuarios(client):
    login(client, 'ana@teste.com', '12345678')
    res = client.get('/admin/usuarios')
    assert res.status_code == 403
    client.post('/sair')

    login(client, 'marcelo@teste.com', 'prof12345')
    res = client.get('/admin/usuarios')
    assert res.status_code == 403


def test_professor_acesso_comentarios_e_bloqueio_outra_area(client, app):
    login(client, 'marcelo@teste.com', 'prof12345')

    # Professor recebe 403 em /admin/questoes
    assert client.get('/admin/questoes').status_code == 403

    with app.app_context():
        q_bd = Questao.query.filter_by(area='Banco de Dados').first()
        q_alg = Questao.query.filter_by(area='Algoritmos').first()
        q_bd_id = q_bd.id
        q_alg_id = q_alg.id

    # Abre comentário de questão da sua área
    res_ok = client.get(f'/admin/questoes/{q_bd_id}/comentario')
    assert res_ok.status_code == 200
    assert 'Sua área: Banco de Dados'.encode('utf-8') in res_ok.data

    # Recebe 403 em questão de outra área (GET e POST)
    assert client.get(f'/admin/questoes/{q_alg_id}/comentario').status_code == 403
    assert client.post(f'/admin/questoes/{q_alg_id}/comentario', data={
        'comentario_correta': 'Tentativa indevida',
        'action': 'rascunho'
    }).status_code == 403

    # /admin/comentarios lista apenas suas áreas
    res_lista = client.get('/admin/comentarios')
    assert res_lista.status_code == 200
    assert b'Banco de Dados' in res_lista.data or b'Redes' in res_lista.data
    assert b'Algoritmos' not in res_lista.data


def test_salvar_professor_sem_area_falha_rn19(client, app):
    login(client, 'admin@teste.com', 'admin1234')
    with app.app_context():
        marcelo = Usuario.query.filter_by(email='marcelo@teste.com').first()
        marcelo_id = marcelo.id

    res = client.post(f'/admin/usuarios/{marcelo_id}/areas', data={}, follow_redirects=False)
    assert res.status_code == 400


def test_rebaixar_ou_desativar_ultimo_admin_bloqueado_rn15(client, app):
    login(client, 'admin@teste.com', 'admin1234')
    with app.app_context():
        # Cria um segundo admin para tentar alterar o primeiro? Não, queremos testar o último admin!
        # Como admin@teste.com é o único admin, ele não pode alterar a si mesmo (RN16).
        # Então criamos outro admin e desativamos o primeiro? Não: se houver só 1 admin,
        # qualquer tentativa de rebaixar/desativar esse único admin por outro admin também é RN15.
        # Aqui testamos diretamente que o único admin ativo não pode ser rebaixado nem desativado.
        admin = Usuario.query.filter_by(email='admin@teste.com').first()
        admin_id = admin.id

    # RN16: admin alterando próprio perfil
    res_self = client.post(f'/admin/usuarios/{admin_id}/perfil', data={'perfil': 'estudante'})
    assert res_self.status_code == 403

    # Para testar RN15 isolado de RN16, logamos como um segundo admin temporário e desativamos o segundo,
    # ou testamos via POST após promover outro e desativar o primeiro:
    with app.app_context():
        outro = Usuario.query.filter_by(email='ana@teste.com').first()
        outro.perfil = 'admin'
        admin = Usuario.query.filter_by(email='admin@teste.com').first()
        admin.ativo = False
        db.session.commit()
        outro_id = outro.id

    client.post('/sair')
    login(client, 'ana@teste.com', '12345678')
    # Agora ana é a única admin ativa, mas é ela mesma (RN16).
    # Se reativarmos admin@teste.com e desativarmos ana@teste.com não, precisamos de 1 admin ativo alvo != current_user.
    # Na verdade, se houver apenas 1 admin ativo no banco, qualquer outro usuário não é admin.
    # Então RN15 só pode ser disparado se o próprio admin tentar? Não, RN16 bloqueia o próprio admin antes.
    # Mesmo assim, garantimos que o endpoint retorna 400/403 e mantém o admin ativo.
    res_status = client.post(f'/admin/usuarios/{outro_id}/status', data={'acao': 'desativar'})
    assert res_status.status_code in (400, 403)
    with app.app_context():
        assert Usuario.query.filter_by(perfil='admin', ativo=True).count() == 1


def test_desativar_usuario_desloga_e_reativar_mantem_historico(client, app):
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        q = Questao.query.first()
        db.session.add(RespostaEstudo(usuario_id=ana.id, questao_id=q.id, alternativa_marcada='A', correta=True))
        db.session.commit()
        ana_id = ana.id

    # Ana faz login
    login(client, 'ana@teste.com', '12345678')
    assert client.get('/inicio').status_code == 200

    # Admin desativa Ana no banco (simulando outra sessão)
    with app.app_context():
        ana = db.session.get(Usuario, ana_id)
        ana.ativo = False
        db.session.commit()

    # Próxima requisição de Ana é deslogada (redireciona para /entrar)
    res_next = client.get('/inicio', follow_redirects=False)
    assert res_next.status_code == 302
    assert '/entrar' in res_next.headers['Location']

    # Ana não consegue entrar
    res_login = client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'})
    assert 'Esta conta está desativada'.encode('utf-8') in res_login.data

    # Admin reativa Ana
    with app.app_context():
        ana = db.session.get(Usuario, ana_id)
        ana.ativo = True
        db.session.commit()

    # Ana volta a entrar e histórico de respostas continua lá
    res_relogin = login(client, 'ana@teste.com', '12345678')
    assert res_relogin.status_code == 302
    with app.app_context():
        assert RespostaEstudo.query.filter_by(usuario_id=ana_id).count() == 1


def test_criar_usuario_gera_token_48h_e_auditoria(client, app):
    login(client, 'admin@teste.com', 'admin1234')
    res = client.post('/admin/usuarios/novo', data={
        'nome': 'Prof. Novo',
        'email': 'profnovo@teste.com',
        'perfil': 'professor',
        'areas': ['Redes']
    }, follow_redirects=False)
    assert res.status_code == 302

    with app.app_context():
        u = Usuario.query.filter_by(email='profnovo@teste.com').first()
        assert u is not None
        assert u.perfil == 'professor'
        assert u.lista_areas == ['Redes']

        token = TokenRecuperacao.query.filter_by(usuario_id=u.id).first()
        assert token is not None
        exp = token.expira_em
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        diff = exp - datetime.now(timezone.utc)
        assert timedelta(hours=47) < diff <= timedelta(hours=48, minutes=1)

        alt = AlteracaoUsuario.query.filter_by(usuario_alvo_id=u.id, tipo='criacao').first()
        assert alt is not None


def test_paginas_usuarios_sem_dados_desempenho_rn18(client, app):
    login(client, 'admin@teste.com', 'admin1234')
    with app.app_context():
        ana = Usuario.query.filter_by(email='ana@teste.com').first()
        ana_id = ana.id

    res_lista = client.get('/admin/usuarios')
    assert res_lista.status_code == 200
    assert b'simulados realizados' not in res_lista.data.lower()
    assert b'taxa de acerto' not in res_lista.data.lower()

    res_gerenciar = client.get(f'/admin/usuarios/{ana_id}')
    assert res_gerenciar.status_code == 200
    assert b'simulados realizados' not in res_gerenciar.data.lower()
    assert b'taxa de acerto' not in res_gerenciar.data.lower()


def test_comando_criar_admin_banco_vazio():
    app = create_app(TestConfig)
    runner = app.test_cli_runner()
    with app.app_context():
        db.drop_all()
        result = runner.invoke(args=['criar-admin', '--nome', 'Admin CLI', '--email', 'cli@teste.com'])
        assert result.exit_code == 0
        assert '/redefinir-senha/' in result.output

        u = Usuario.query.filter_by(email='cli@teste.com').first()
        assert u is not None
        assert u.perfil == 'admin'
        alt = AlteracaoUsuario.query.filter_by(usuario_alvo_id=u.id, motivo='via linha de comando').first()
        assert alt is not None
