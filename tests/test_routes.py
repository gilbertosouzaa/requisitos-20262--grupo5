import pytest
from app import create_app
from app.extensions import db
from app.models import Usuario, Curso, Questao
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        curso = Curso(nome="Ciência da Computação")
        db.session.add(curso)
        db.session.commit()

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


def test_rn01_questoes_sem_login(client):
    """RN01: Questões podem ser consultadas sem login."""
    res = client.get('/questoes')
    assert res.status_code == 200
    assert "Banco de quest".encode('utf-8') in res.data.lower() or b"banco de quest" in res.data.lower()


def test_rn01_rotas_protegidas_redirecionam_para_login(client):
    """RN01: Simulados, desempenho e início exigem login e redirecionam para /entrar?next=..."""
    # /inicio
    res_inicio = client.get('/inicio')
    assert res_inicio.status_code == 302
    assert '/entrar?next=' in res_inicio.headers['Location']

    # /simulados/novo
    res_sim = client.get('/simulados/novo')
    assert res_sim.status_code == 302
    assert '/entrar?next=' in res_sim.headers['Location']

    # /desempenho
    res_desemp = client.get('/desempenho')
    assert res_desemp.status_code == 302
    assert '/entrar?next=' in res_desemp.headers['Location']


def test_t01_landing_redireciona_se_logado(client):
    """T01: Usuário logado ao acessar '/' é redirecionado para /inicio."""
    # Loga o usuário
    client.post('/entrar', data={
        'email': 'ana@teste.com',
        'senha': '12345678'
    })

    res = client.get('/')
    assert res.status_code == 302
    assert '/inicio' in res.headers['Location']


def test_t05_inicio_acesso_logado(client):
    """T05: Usuário logado acessa /inicio e vê seu nome e curso."""
    client.post('/entrar', data={
        'email': 'ana@teste.com',
        'senha': '12345678'
    })

    res = client.get('/inicio')
    assert res.status_code == 200
    assert b"Ana Souza" in res.data
    assert "Ciência da Computação".encode('utf-8') in res.data or b"Ci&ecirc;ncia da Computa&ccedil;&atilde;o" in res.data


def test_rn02_validacao_questao(app):
    """RN02: Toda questão tem ano, curso, componente, área, tipo e gabarito oficial."""
    with app.app_context():
        curso = Curso.query.first()

        # Sem área
        with pytest.raises(ValueError):
            q_sem_area = Questao(
                ano=2023,
                curso_id=curso.id,
                numero=1,
                componente="formacao_geral",
                area="",  # Inválido
                tipo="objetiva",
                enunciado="Enunciado de teste [questão fictícia para protótipo]",
                gabarito_oficial="A"
            )
            db.session.add(q_sem_area)
            db.session.commit()

        # Sem gabarito oficial
        with pytest.raises(ValueError):
            q_sem_gab = Questao(
                ano=2023,
                curso_id=curso.id,
                numero=2,
                componente="formacao_geral",
                area="Atualidades",
                tipo="objetiva",
                enunciado="Enunciado de teste [questão fictícia para protótipo]",
                gabarito_oficial=""  # Inválido
            )
            db.session.add(q_sem_gab)
            db.session.commit()
