import pytest
import re
from app import create_app
from app.extensions import db
from app.models import Usuario, Curso, Questao, Simulado, SimuladoQuestao
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


def test_engenharia_computacao_ve_fg_e_especificas(client, app):
    """Estudante de Engenharia de Computação vê questões de Formação Geral (comuns) e específicas do seu curso."""
    # Login com Bruno (Engenharia de Computação)
    res_login = client.post('/entrar', data={'email': 'bruno@teste.com', 'senha': '12345678'}, follow_redirects=True)
    assert res_login.status_code == 200

    # Acessa banco de questões (/questoes) - padrão é o curso do usuário
    res = client.get('/questoes')
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Verifica se as questões de FG (1 a 10) e específicas de EC estão presentes
    # Q1 é FG
    assert "Formação Geral" in html
    # Deve mostrar o filtro padrão com Engenharia de Computação
    assert 'selected>Engenharia de Computação</option>' in html or 'value="3" selected' in html or 'Engenharia de Computação' in html

    # Verifica opção "Todos os cursos" no select de cursos
    assert '<option value="todos"' in html
    assert 'Todos os cursos</option>' in html


def test_filtro_todos_os_cursos(client, app):
    """Ao selecionar 'Todos os cursos', lista questões de múltiplos cursos."""
    client.post('/entrar', data={'email': 'bruno@teste.com', 'senha': '12345678'}, follow_redirects=True)

    res = client.get('/questoes?curso=todos')
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "Todos os cursos" in html
    # Questões de FG e de cursos específicos aparecem
    assert "Formação Geral" in html


def test_estado_vazio_curso_sem_questoes(client, app):
    """Quando o filtro de curso não tiver questões específicas cadastradas, exibe mensagem orientativa e botão 'Ver Formação Geral'."""
    client.post('/entrar', data={'email': 'bruno@teste.com', 'senha': '12345678'}, follow_redirects=True)

    # Cria um novo curso sem nenhuma questão cadastrada
    with app.app_context():
        curso_vazio = Curso(nome="Engenharia Biomédica")
        db.session.add(curso_vazio)
        db.session.commit()
        curso_vazio_id = curso_vazio.id

    res = client.get(f'/questoes?curso={curso_vazio_id}')
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Verifica texto exato do requisito
    assert "Ainda não há questões do Componente Específico de Engenharia Biomédica. Você pode estudar as questões de Formação Geral, que valem para todos os cursos." in html
    # Verifica o botão "Ver Formação Geral"
    assert "Ver Formação Geral" in html
    assert f"componente=formacao_geral" in html


def test_simulado_novo_engenharia_computacao_desabilita_prova_completa(client, app):
    """Estudante de Engenharia de Computação (sem edição completa de 40 questões) tem 'Prova completa' desabilitada com aviso."""
    # Login com Bruno (Engenharia de Computação)
    client.post('/entrar', data={'email': 'bruno@teste.com', 'senha': '12345678'}, follow_redirects=True)

    res = client.get('/simulados/novo')
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Aviso obrigatório
    assert "Ainda não há uma edição completa do seu curso" in html

    # Radio 'tipo-completo' deve estar desabilitado
    assert 'id="tipo-completo"' in html
    assert 'disabled' in html

    # Simulado parcial deve estar checked
    assert 'id="tipo-parcial"' in html
    assert 'checked' in html

    # Tentativa de POST com tipo 'completo' deve ser rejeitada pelo servidor
    res_post = client.post('/simulados/novo', data={'tipo': 'completo', 'edicao': 2023}, follow_redirects=True)
    assert res_post.status_code == 200
    html_post = res_post.get_data(as_text=True)
    assert "Ainda não há uma edição completa do seu curso" in html_post


def test_simulado_novo_ciencia_computacao_permite_prova_completa(client, app):
    """Estudante de Ciência da Computação (que possui 40 questões em 2023) tem 'Prova completa' habilitada."""
    # Login com Ana (Ciência da Computação)
    client.post('/entrar', data={'email': 'ana@teste.com', 'senha': '12345678'}, follow_redirects=True)

    res = client.get('/simulados/novo')
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Não deve ter o aviso de indisponibilidade
    assert "Ainda não há uma edição completa do seu curso" not in html

    # Radio completo deve estar checked e NÃO disabled
    assert 'id="tipo-completo"' in html
    # Deve poder iniciar prova completa
    res_post = client.post('/simulados/novo', data={'tipo': 'completo', 'edicao': 2023})
    assert res_post.status_code == 302
    assert "/simulados/" in res_post.headers['Location']


def test_simulado_parcial_engenharia_computacao(client, app):
    """Estudante de Engenharia de Computação consegue criar e realizar simulado parcial com questões de FG e EC."""
    client.post('/entrar', data={'email': 'bruno@teste.com', 'senha': '12345678'}, follow_redirects=True)

    # Cria simulado parcial de 5 questões do componente específico
    res = client.post('/simulados/novo', data={
        'tipo': 'parcial',
        'componente': 'especifico',
        'area': 'todas',
        'quantidade': 5
    })
    assert res.status_code == 302
    simulado_url = res.headers['Location']
    simulado_id = int(simulado_url.rstrip('/').split('/')[-1])

    with app.app_context():
        simulado = db.session.get(Simulado, simulado_id)
        assert simulado is not None
        assert len(simulado.questoes_assoc) == 5
        # Todas as questões devem ser de EC
        for sq in simulado.questoes_assoc:
            assert sq.questao.curso.nome == "Engenharia de Computação"


def test_admin_form_fg_curso_opcional_especifico_obrigatorio(client, app):
    """No form de questão do Admin: curso é opcional para FG e obrigatório para Componente Específico."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin1234'})

    # 1. Tenta cadastrar questão específica SEM curso -> deve falhar
    dados_esp_sem_curso = {
        'ano': 2024,
        'numero': 1,
        'componente': 'especifico',
        'curso_id': '',
        'area': 'Algoritmos',
        'tipo': 'objetiva',
        'enunciado': 'Enunciado sem curso [questão fictícia para protótipo]',
        'gabarito_oficial': 'A',
        'alt_A': 'A', 'alt_B': 'B', 'alt_C': 'C', 'alt_D': 'D', 'alt_E': 'E'
    }
    res_esp = client.post('/admin/questoes/nova', data=dados_esp_sem_curso)
    assert res_esp.status_code == 400
    assert "Selecione o curso para questões do Componente Específico" in res_esp.get_data(as_text=True)

    # 2. Cadastra questão de Formação Geral SEM curso -> deve ter sucesso
    dados_fg_sem_curso = {
        'ano': 2024,
        'numero': 1,
        'componente': 'formacao_geral',
        'curso_id': '',
        'area': 'Atualidades',
        'tipo': 'objetiva',
        'enunciado': 'Enunciado FG sem curso [questão fictícia para protótipo]',
        'gabarito_oficial': 'C',
        'alt_A': 'A', 'alt_B': 'B', 'alt_C': 'C', 'alt_D': 'D', 'alt_E': 'E'
    }
    res_fg = client.post('/admin/questoes/nova', data=dados_fg_sem_curso)
    assert res_fg.status_code == 302

    with app.app_context():
        q_salva = Questao.query.filter_by(ano=2024, numero=1).first()
        assert q_salva is not None
        assert q_salva.componente == 'formacao_geral'
        assert q_salva.curso_id is None
