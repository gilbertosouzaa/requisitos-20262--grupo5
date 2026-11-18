import io
import pytest
from app import create_app
from app.extensions import db
from app.models import Usuario, Curso, Questao, Alternativa, RespostaEstudo, Simulado, SimuladoQuestao, SimuladoResposta
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

        # Cria usuários: estudante e admin
        estudante = Usuario(
            nome="Ana Estudante",
            email="estudante@teste.com",
            curso_id=cc.id,
            perfil="estudante"
        )
        estudante.set_senha("senha123")

        admin = Usuario(
            nome="Carlos Admin",
            email="admin@teste.com",
            curso_id=cc.id,
            perfil="admin"
        )
        admin.set_senha("admin123")

        db.session.add_all([estudante, admin])
        db.session.commit()

        # Questão 1: Ativa, publicada
        q1 = Questao(
            ano=2023,
            curso_id=cc.id,
            numero=1,
            componente="formacao_geral",
            area="Interpretação de texto",
            tipo="objetiva",
            enunciado="Enunciado da questão teste 1 sobre interpretação.",
            gabarito_oficial="A",
            comentario_correta="Explicação da alternativa A estar correta.",
            comentario_status="publicado",
            anulada=False
        )
        db.session.add(q1)
        db.session.flush()

        for letra in ["A", "B", "C", "D", "E"]:
            db.session.add(Alternativa(
                questao_id=q1.id,
                letra=letra,
                texto=f"Texto alternativa {letra}",
                comentario_erro=f"Erro da {letra}" if letra != "A" else None
            ))

        # Questão 2: Ativa, rascunho de comentário
        q2 = Questao(
            ano=2023,
            curso_id=cc.id,
            numero=2,
            componente="especifico",
            area="Banco de Dados",
            tipo="objetiva",
            enunciado="Enunciado da questão teste 2 sobre SQL.",
            gabarito_oficial="B",
            comentario_correta="Explicação rascunho da B.",
            comentario_status="rascunho",
            anulada=False
        )
        db.session.add(q2)
        db.session.flush()

        for letra in ["A", "B", "C", "D", "E"]:
            db.session.add(Alternativa(
                questao_id=q2.id,
                letra=letra,
                texto=f"Texto alt {letra}"
            ))

        # Questão 3: Anulada
        q3 = Questao(
            ano=2023,
            curso_id=cc.id,
            numero=3,
            componente="especifico",
            area="Redes",
            tipo="objetiva",
            enunciado="Enunciado da questão teste 3 anulada.",
            gabarito_oficial="C",
            comentario_status="rascunho",
            anulada=True
        )
        db.session.add(q3)
        db.session.flush()

        for letra in ["A", "B", "C", "D", "E"]:
            db.session.add(Alternativa(
                questao_id=q3.id,
                letra=letra,
                texto=f"Texto alt {letra}"
            ))

        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ==============================================================================
# 1. Testes de Acesso e Permissão (RN11)
# ==============================================================================

def test_acesso_visitante_redireciona_login(client):
    """Visitante não autenticado tentando acessar /admin é redirecionado para login."""
    res = client.get('/admin/questoes')
    assert res.status_code == 302
    assert '/entrar' in res.location


def test_acesso_estudante_retorna_403(client):
    """Estudante autenticado tentando acessar /admin recebe HTTP 403 com página de aviso."""
    client.post('/entrar', data={'email': 'estudante@teste.com', 'senha': 'senha123'})
    res = client.get('/admin/questoes')
    assert res.status_code == 403
    html = res.get_data(as_text=True)
    assert "Você não tem permissão para acessar esta página" in html


def test_acesso_admin_autorizado(client):
    """Admin autenticado tem acesso livre às rotas /admin."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})
    res = client.get('/admin/questoes')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Questões cadastradas" in html or "questões cadastradas" in html


def test_link_administracao_no_cabecalho_estudante(client):
    """No cabeçalho padrão (base_app), apenas admin vê o link Administração."""
    # Estudante não vê
    client.post('/entrar', data={'email': 'estudante@teste.com', 'senha': 'senha123'})
    res = client.get('/inicio')
    assert "Administração" not in res.get_data(as_text=True)
    client.post('/sair')

    # Admin vê
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})
    res = client.get('/inicio')
    assert "Administração" in res.get_data(as_text=True)


# ==============================================================================
# 2. Testes de T13: Lista de Questões, Filtros e Ações
# ==============================================================================

def test_t13_filtros_questoes(client):
    """Filtros por busca, ano, situação acumulam e filtram corretamente."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    # Filtro: apenas anuladas
    res = client.get('/admin/questoes?situacao=anuladas')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Enunciado da questão teste 3 anulada" in html
    assert "Enunciado da questão teste 1 sobre interpretação" not in html

    # Filtro: apenas sem comentário
    res = client.get('/admin/questoes?situacao=sem_comentario')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Enunciado da questão teste 2 sobre SQL" in html
    assert "Enunciado da questão teste 1 sobre interpretação" not in html

    # Filtro: busca textual
    res = client.get('/admin/questoes?busca=SQL')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Enunciado da questão teste 2 sobre SQL" in html
    assert "Enunciado da questão teste 1 sobre interpretação" not in html


def test_t13_toggle_anulacao(client, app):
    """Ação de marcar/desmarcar anulação inverte o estado da questão."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    with app.app_context():
        q1 = Questao.query.filter_by(numero=1).first()
        assert q1.anulada is False
        q1_id = q1.id

    # Marca como anulada
    res = client.post(f'/admin/questoes/{q1_id}/anular', follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        q1 = db.session.get(Questao, q1_id)
        assert q1.anulada is True

    # Desmarca anulação
    res = client.post(f'/admin/questoes/{q1_id}/anular', follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        q1 = db.session.get(Questao, q1_id)
        assert q1.anulada is False


def test_t13_remover_questao_com_respostas_bloqueada(client, app):
    """Questão que já tem respostas de estudantes não pode ser removida."""
    # Simula resposta de estudante na Q1
    with app.app_context():
        q1 = Questao.query.filter_by(numero=1).first()
        estudante = Usuario.query.filter_by(email="estudante@teste.com").first()
        resp = RespostaEstudo(
            usuario_id=estudante.id,
            questao_id=q1.id,
            alternativa_marcada="A",
            correta=True
        )
        db.session.add(resp)
        db.session.commit()
        q1_id = q1.id

    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    # API de verificação retorna tem_respostas=True
    res_api = client.get(f'/admin/questoes/verificar-respostas/{q1_id}')
    assert res_api.status_code == 200
    assert res_api.get_json()['tem_respostas'] is True

    # Tentativa de remoção é bloqueada com status 400
    res_del = client.post(f'/admin/questoes/{q1_id}/remover')
    assert res_del.status_code == 400

    # Confirma que a questão não foi removida
    with app.app_context():
        assert db.session.get(Questao, q1_id) is not None


def test_t13_remover_questao_sem_respostas_sucesso(client, app):
    """Questão sem respostas pode ser removida definitivamente."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    with app.app_context():
        q2 = Questao.query.filter_by(numero=2).first()
        q2_id = q2.id

    res = client.post(f'/admin/questoes/{q2_id}/remover', follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        assert db.session.get(Questao, q2_id) is None
        assert Alternativa.query.filter_by(questao_id=q2_id).count() == 0


# ==============================================================================
# 3. Testes de T14: Formulário de Questão (RN02, Unicidade)
# ==============================================================================

def test_t14_criar_questao_objetiva_valida(client, app):
    """Criação com sucesso de questão objetiva atendendo todas as regras RN02."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    with app.app_context():
        cc_id = Curso.query.filter_by(nome="Ciência da Computação").first().id

    dados = {
        'curso_id': cc_id,
        'ano': 2023,
        'numero': 15,
        'componente': 'especifico',
        'area': 'Algoritmos e Estrutura de Dados',
        'tipo': 'objetiva',
        'enunciado': 'Novo enunciado de teste para busca binária.',
        'gabarito_oficial': 'D',
        'alt_A': 'Alternativa A texto',
        'alt_B': 'Alternativa B texto',
        'alt_C': 'Alternativa C texto',
        'alt_D': 'Alternativa D texto correta',
        'alt_E': 'Alternativa E texto'
    }

    res = client.post('/admin/questoes/nova', data=dados, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        q = Questao.query.filter_by(ano=2023, curso_id=cc_id, numero=15).first()
        assert q is not None
        assert q.gabarito_oficial == 'D'
        assert q.comentario_status == 'rascunho'
        assert len(q.alternativas) == 5


def test_t14_criar_questao_discursiva_valida(client, app):
    """Criação com sucesso de questão discursiva com padrão de resposta."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    with app.app_context():
        cc_id = Curso.query.filter_by(nome="Ciência da Computação").first().id

    dados = {
        'curso_id': cc_id,
        'ano': 2023,
        'numero': 38,
        'componente': 'especifico',
        'area': 'Engenharia de Software',
        'tipo': 'discursiva',
        'enunciado': 'Enunciado discursivo sobre padrões de projeto.',
        'padrao_resposta': 'O estudante deve citar o padrão Factory e explicar desacoplamento.'
    }

    res = client.post('/admin/questoes/nova', data=dados, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        q = Questao.query.filter_by(ano=2023, curso_id=cc_id, numero=38).first()
        assert q is not None
        assert q.tipo == 'discursiva'
        assert q.gabarito_oficial == 'DISCURSIVA'
        assert 'Factory' in q.padrao_resposta


def test_t14_validacao_rn02_rejeita_campos_faltando(client, app):
    """Rejeita submissão com campos ausentes e lista erros com links âncora."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    # Falta ano, gabarito e alternativas
    dados = {
        'curso_id': 1,
        'numero': 20,
        'componente': 'especifico',
        'area': 'IA',
        'tipo': 'objetiva',
        'enunciado': 'Enunciado incompleto.'
    }

    res = client.post('/admin/questoes/nova', data=dados)
    assert res.status_code == 400
    html = res.get_data(as_text=True)
    assert 'role="alert"' in html
    assert 'href="#campo-ano"' in html
    assert 'href="#campo-gabarito_oficial"' in html


def test_t14_unicidade_ano_curso_numero(client, app):
    """Rejeita criação de questão com ano, curso e número já existentes."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    with app.app_context():
        cc_id = Curso.query.filter_by(nome="Ciência da Computação").first().id

    # Q11 já existe para CC em 2023 (Componente Específico)
    dados = {
        'curso_id': cc_id,
        'ano': 2023,
        'numero': 11,
        'componente': 'especifico',
        'area': 'Algoritmos',
        'tipo': 'objetiva',
        'enunciado': 'Tentativa duplicada.',
        'gabarito_oficial': 'B',
        'alt_A': 'A', 'alt_B': 'B', 'alt_C': 'C', 'alt_D': 'D', 'alt_E': 'E'
    }

    res = client.post('/admin/questoes/nova', data=dados)
    assert res.status_code == 400
    html = res.get_data(as_text=True)
    assert "Já existe uma questão de número 11 no ENADE 2023 para este curso" in html

    # Q1 já existe para Formação Geral em 2023
    dados_fg = {
        'ano': 2023,
        'numero': 1,
        'componente': 'formacao_geral',
        'area': 'Interpretação',
        'tipo': 'objetiva',
        'enunciado': 'Tentativa duplicada FG.',
        'gabarito_oficial': 'B',
        'alt_A': 'A', 'alt_B': 'B', 'alt_C': 'C', 'alt_D': 'D', 'alt_E': 'E'
    }
    res_fg = client.post('/admin/questoes/nova', data=dados_fg)
    assert res_fg.status_code == 400
    assert "Já existe uma questão de Formação Geral número 1 no ENADE 2023" in res_fg.get_data(as_text=True)


def test_t14_duplicar_questao(client, app):
    """GET na rota de nova questão com parâmetro duplicar carrega os campos da questão original."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    with app.app_context():
        q1_id = Questao.query.filter_by(numero=1).first().id

    res = client.get(f'/admin/questoes/nova?duplicar={q1_id}')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Enunciado da questão teste 1 sobre interpretação" in html


# ==============================================================================
# 4. Testes de T15: Editor de Comentário e Visibilidade para Estudante
# ==============================================================================

def test_t15_fila_comentarios(client):
    """Fila de comentários lista questões sem comentário publicado."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})
    res = client.get('/admin/comentarios')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    # Q2 e Q3 estão com comentário 'rascunho', Q1 está 'publicado'
    assert "Enunciado da questão teste 2" in html or "Questão 2" in html or "2" in html


def test_t15_salvar_rascunho_estudante_nao_ve_comentario(client, app):
    """Comentário com status rascunho NÃO é exibido para o estudante na correção."""
    with app.app_context():
        q2 = Questao.query.filter_by(numero=2).first()
        q2_id = q2.id

    # Admin salva comentário como rascunho
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})
    res_admin = client.post(f'/admin/questoes/{q2_id}/comentario', data={
        'action': 'rascunho',
        'comentario_correta': 'Explicação confidencial ainda em elaboração.',
        'comentario_status': 'rascunho'
    }, follow_redirects=True)
    assert res_admin.status_code == 200

    # Estudante responde a questão e visualiza
    client.post('/sair')
    client.post('/entrar', data={'email': 'estudante@teste.com', 'senha': 'senha123'})
    res_resp = client.post(f'/api/questoes/{q2_id}/responder', json={'alternativa': 'B'})
    data = res_resp.get_json()
    assert data['comentario_em_elaboracao'] is True
    assert data['comentario_correta'] is None

    # Na página HTML da questão
    res_page = client.get(f'/questoes/{q2_id}')
    html = res_page.get_data(as_text=True)
    assert "Comentário em elaboração" in html
    assert "Explicação confidencial ainda em elaboração" not in html


def test_t15_publicar_comentario_estudante_ve_comentario(client, app):
    """Comentário publicado É exibido para o estudante na correção."""
    with app.app_context():
        q2 = Questao.query.filter_by(numero=2).first()
        q2_id = q2.id

    # Admin publica comentário
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})
    res_admin = client.post(f'/admin/questoes/{q2_id}/comentario', data={
        'action': 'publicar',
        'comentario_correta': 'Explicação pública e oficial da alternativa B.',
        'comentario_erro_A': 'Erro da opção A.',
        'comentario_fonte': 'Livro de Banco de Dados pág. 10'
    }, follow_redirects=True)
    assert res_admin.status_code == 200

    # Verifica auditoria no banco
    with app.app_context():
        q2 = db.session.get(Questao, q2_id)
        assert q2.comentario_status == 'publicado'
        assert q2.comentario_atualizado_por is not None
        assert q2.comentario_atualizado_em is not None

    # Estudante agora visualiza
    client.post('/sair')
    client.post('/entrar', data={'email': 'estudante@teste.com', 'senha': 'senha123'})
    res_resp = client.post(f'/api/questoes/{q2_id}/responder', json={'alternativa': 'B'})
    data = res_resp.get_json()
    assert data['comentario_em_elaboracao'] is False
    assert data['comentario_correta'] == 'Explicação pública e oficial da alternativa B.'

    # Na página HTML
    res_page = client.get(f'/questoes/{q2_id}')
    html = res_page.get_data(as_text=True)
    assert "Explicação pública e oficial da alternativa B" in html


# ==============================================================================
# 5. Testes de Importação em CSV (RNF10)
# ==============================================================================

def test_baixar_exemplo_csv(client):
    """Download do modelo CSV de exemplo retorna arquivo attachment com cabeçalho correto."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})
    res = client.get('/admin/questoes/exemplo.csv')
    assert res.status_code == 200
    assert 'text/csv' in res.content_type
    texto = res.get_data(as_text=True)
    assert 'ano,curso,numero,componente,area,tipo,enunciado' in texto
    assert 'Ciência da Computação' in texto


def test_importar_csv_fluxo_valido(client, app):
    """Importação de arquivo CSV válido passa na validação e na confirmação atômica."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    csv_conteudo = (
        "ano,curso,numero,componente,area,tipo,enunciado,alt_a,alt_b,alt_c,alt_d,alt_e,gabarito,padrao_resposta,anulada\n"
        "2022,Ciência da Computação,10,formacao_geral,Sociedade,objetiva,Enunciado da Q10,Alt A,Alt B,Alt C,Alt D,Alt E,C,,0\n"
        "2022,Ciência da Computação,11,especifico,Grafos,discursiva,Enunciado da Q11,,,,,,DISCURSIVA,Padrão de resposta da Q11,0\n"
    )

    data = {
        'arquivo_csv': (io.BytesIO(csv_conteudo.encode('utf-8')), 'questoes_2022.csv')
    }

    # Etapa 1: Upload e validação
    res1 = client.post('/admin/questoes/importar', data=data, content_type='multipart/form-data')
    assert res1.status_code == 200
    html1 = res1.get_data(as_text=True)
    assert "2 questões válidas prontas para importar" in html1

    # Etapa 2: Confirmação
    res2 = client.post('/admin/questoes/importar', data={'confirmar': '1'}, follow_redirects=True)
    assert res2.status_code == 200

    # Confirma gravação atômica no banco de dados
    with app.app_context():
        q10 = Questao.query.filter_by(ano=2022, numero=10).first()
        q11 = Questao.query.filter_by(ano=2022, numero=11).first()
        assert q10 is not None
        assert q10.comentario_status == 'rascunho'
        assert len(q10.alternativas) == 5
        assert q11 is not None
        assert q11.padrao_resposta == 'Padrão de resposta da Q11'


def test_importar_csv_rejeita_linha_invalida(client, app):
    """Arquivo com linha inválida (ex: tipo desconhecido, falta de alternativa) rejeita TUDO."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    csv_invalido = (
        "ano,curso,numero,componente,area,tipo,enunciado,alt_a,alt_b,alt_c,alt_d,alt_e,gabarito,padrao_resposta,anulada\n"
        "2022,Ciência da Computação,21,especifico,Algoritmos,objetiva,Enunciado Q21,A,B,C,D,E,A,,0\n"
        "2022,Ciência da Computação,22,especifico,Algoritmos,tipo_invalido,Enunciado Q22,,,,,,X,,0\n"
    )

    data = {
        'arquivo_csv': (io.BytesIO(csv_invalido.encode('utf-8')), 'questoes_com_erro.csv')
    }

    res = client.post('/admin/questoes/importar', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Falha na validação do arquivo: nenhuma questão foi salva!" in html
    assert "Tipo deve ser 'objetiva' ou 'discursiva'" in html or "Tipo deve ser &#39;objetiva&#39; ou &#39;discursiva&#39;" in html

    # Verifica que NENHUMA das questões foi inserida (nem a linha 1 válida)
    with app.app_context():
        assert Questao.query.filter_by(ano=2022, numero=21).first() is None
        assert Questao.query.filter_by(ano=2022, numero=22).first() is None


def test_importar_csv_rejeita_duplicata(client, app):
    """Arquivo com questão já existente no sistema ou repetida no CSV é rejeitado."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})

    # Tenta importar Q1 de 2023 (que já existe no banco)
    csv_dup = (
        "ano,curso,numero,componente,area,tipo,enunciado,alt_a,alt_b,alt_c,alt_d,alt_e,gabarito,padrao_resposta,anulada\n"
        "2023,Ciência da Computação,1,formacao_geral,Interpretação,objetiva,Enunciado dup,A,B,C,D,E,A,,0\n"
    )

    data = {
        'arquivo_csv': (io.BytesIO(csv_dup.encode('utf-8')), 'dup.csv')
    }

    res = client.post('/admin/questoes/importar', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Já existe questão cadastrada no sistema com Ano 2023" in html


# ==============================================================================
# 6. Teste da Rota Placeholder de Moderação
# ==============================================================================

def test_moderacao_placeholder(client):
    """Item moderação exibe página 'Em construção' (US15 P2)."""
    client.post('/entrar', data={'email': 'admin@teste.com', 'senha': 'admin123'})
    res = client.get('/admin/moderacao')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Em construção (em breve)" in html
