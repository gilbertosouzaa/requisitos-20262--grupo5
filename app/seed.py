import secrets
from datetime import datetime, timedelta, timezone
import click
from flask import url_for
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Curso, Usuario, Questao, Alternativa, ProfessorArea, TokenRecuperacao, AlteracaoUsuario

def seed_database():
    """Popula o banco com os cursos, usuários de teste e questões do ENADE 2023 e 2021."""
    click.echo("Iniciando seed do banco de dados...")

    # 1. Cursos
    cursos_nomes = [
        "Ciência da Computação",
        "Sistemas de Informação",
        "Engenharia de Computação"
    ]
    cursos_map = {}
    for nome in cursos_nomes:
        curso = Curso.query.filter_by(nome=nome).first()
        if not curso:
            curso = Curso(nome=nome)
            db.session.add(curso)
            db.session.flush()
        cursos_map[nome] = curso

    # 2. Usuários de teste
    # Ana Souza (Ciência da Computação)
    if not Usuario.query.filter_by(email="ana@teste.com").first():
        ana = Usuario(
            nome="Ana Souza",
            email="ana@teste.com",
            curso_id=cursos_map["Ciência da Computação"].id,
            perfil="estudante"
        )
        ana.set_senha("12345678")
        db.session.add(ana)
        click.echo("Usuário 'ana@teste.com' criado.")

    # Bruno Lima (Engenharia de Computação)
    if not Usuario.query.filter_by(email="bruno@teste.com").first():
        bruno = Usuario(
            nome="Bruno Lima",
            email="bruno@teste.com",
            curso_id=cursos_map["Engenharia de Computação"].id,
            perfil="estudante"
        )
        bruno.set_senha("12345678")
        db.session.add(bruno)
        click.echo("Usuário 'bruno@teste.com' criado.")

    # Carla Mendes (Sistemas de Informação)
    if not Usuario.query.filter_by(email="carla@teste.com").first():
        carla = Usuario(
            nome="Carla Mendes",
            email="carla@teste.com",
            curso_id=cursos_map["Sistemas de Informação"].id,
            perfil="estudante"
        )
        carla.set_senha("12345678")
        db.session.add(carla)
        click.echo("Usuário 'carla@teste.com' criado.")

    # Administrador
    if not Usuario.query.filter_by(email="admin@teste.com").first():
        admin = Usuario(
            nome="Administrador do Sistema",
            email="admin@teste.com",
            curso_id=cursos_map["Ciência da Computação"].id,
            perfil="admin"
        )
        admin.set_senha("admin1234")
        db.session.add(admin)
        click.echo("Usuário 'admin@teste.com' criado.")

    # Professor Marcelo
    if not Usuario.query.filter_by(email="marcelo@teste.com").first():
        marcelo = Usuario(
            nome="Prof. Marcelo",
            email="marcelo@teste.com",
            curso_id=cursos_map["Ciência da Computação"].id,
            perfil="professor"
        )
        marcelo.set_senha("prof12345")
        db.session.add(marcelo)
        db.session.flush()
        db.session.add(ProfessorArea(usuario_id=marcelo.id, area="Banco de Dados"))
        db.session.add(ProfessorArea(usuario_id=marcelo.id, area="Redes"))
        click.echo("Usuário 'marcelo@teste.com' criado.")

    cc_id = cursos_map["Ciência da Computação"].id
    ec_id = cursos_map["Engenharia de Computação"].id
    si_id = cursos_map["Sistemas de Informação"].id

    areas_fg = ["Interpretação de texto", "Atualidades", "Ética e cidadania"]
    areas_esp_cc = ["Algoritmos", "Estruturas de Dados", "Banco de Dados", "Redes", "Engenharia de Software"]
    areas_esp_ec = ["Sistemas Embarcados", "Circuitos Digitais", "Sistemas de Tempo Real", "Arquitetura de Computadores", "Processamento Digital de Sinais"]
    areas_esp_si = ["Governança de TI", "Engenharia de Requisitos", "Gestão de Processos de Negócio", "Segurança da Informação", "Sistemas de Apoio à Decisão"]

    letras = ["A", "B", "C", "D", "E"]

    # 3. Questões ENADE 2023 - Formação Geral (Comum a todos os cursos: curso_id = None)
    fg2023_count = Questao.query.filter_by(ano=2023, componente="formacao_geral").count()
    if fg2023_count == 0:
        click.echo("Cadastrando 10 questões de Formação Geral do ENADE 2023 (Comuns)...")
        for num in range(1, 11):
            if 1 <= num <= 8:
                comp = "formacao_geral"
                area = areas_fg[(num - 1) % len(areas_fg)]
                tipo = "objetiva"
                gabarito = letras[(num * 2) % 5]
                sem_comentario = (num in [4, 7])
                comentario = None if sem_comentario else f"Comentário oficial explicativo da questão {num}: a alternativa {gabarito} é correta com base nos princípios da área de {area}."
                enunciado = f"Considere o texto temático sobre {area.lower()} e responsabilidade social no contexto contemporâneo. Com base nas premissas apresentadas, avalie as asserções a seguir. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=None,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta=comentario,
                    comentario_status='publicado' if comentario else 'rascunho',
                    padrao_resposta=None,
                    anulada=False
                )
                db.session.add(q)
                db.session.flush()

                for idx, l in enumerate(letras):
                    alt_texto = f"Afirmação correspondente à alternativa {l} sobre {area.lower()}."
                    com_erro = None if (l == gabarito or sem_comentario) else f"A alternativa {l} está incorreta pois confunde os conceitos fundamentais."
                    alt = Alternativa(
                        questao_id=q.id,
                        letra=l,
                        texto=alt_texto,
                        comentario_erro=com_erro
                    )
                    db.session.add(alt)

            elif 9 <= num <= 10:
                comp = "formacao_geral"
                area = areas_fg[num % len(areas_fg)]
                tipo = "discursiva"
                gabarito = "DISCURSIVA"
                padrao = (
                    f"Padrão de resposta esperado para a questão discursiva {num}:\n"
                    f"1. O estudante deve identificar a correlação entre {area.lower()} e o impacto social;\n"
                    "2. Propor duas medidas éticas fundamentadas na sustentabilidade;\n"
                    "3. Argumentar com coerência e coesão textual."
                )
                enunciado = f"Com base na charge e no trecho da reportagem sobre {area.lower()}, elabore um texto dissertativo-argumentativo apresentando duas propostas de intervenção. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=None,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta="Padrão de resposta disponibilizado pelo INEP.",
                    comentario_status="publicado",
                    padrao_resposta=padrao,
                    anulada=False
                )
                db.session.add(q)

    # 4. Questões ENADE 2023 - Componente Específico - Ciência da Computação (30 questões: 11 a 40)
    # Total de CC em 2023 = 10 FG + 30 Específicas = 40 (edição completa)
    cc2023_count = Questao.query.filter_by(ano=2023, curso_id=cc_id).count()
    if cc2023_count == 0:
        click.echo("Cadastrando 30 questões específicas do ENADE 2023 (Ciência da Computação)...")
        for num in range(11, 41):
            if 11 <= num <= 37:
                comp = "especifico"
                area = areas_esp_cc[(num - 11) % len(areas_esp_cc)]
                tipo = "objetiva"
                gabarito = letras[(num + 1) % 5]
                anulada = (num in [18, 25])
                sem_comentario = (num in [14, 21, 31])
                comentario = None if sem_comentario else f"Comentário da questão {num} ({area}): a alternativa {gabarito} responde corretamente ao problema proposto analisando a complexidade e invariantes."
                placeholder_img = f"[diagrama de {area.lower()} e grafo de dependências]" if num in [13, 22, 30] else None
                enunciado = f"Analise o trecho de código e as especificações técnicas da arquitetura na área de {area}. Considerando as boas práticas da computação e eficiência algorítmica, assinale a opção correta. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=cc_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    imagem_placeholder=placeholder_img,
                    gabarito_oficial=gabarito,
                    comentario_correta=comentario,
                    comentario_status='publicado' if comentario else 'rascunho',
                    padrao_resposta=None,
                    anulada=anulada
                )
                db.session.add(q)
                db.session.flush()

                for idx, l in enumerate(letras):
                    alt_texto = f"Solução proposta na alternativa {l} aplicando técnicas de {area}."
                    com_erro = None if (l == gabarito or sem_comentario) else f"A alternativa {l} é inadequada pois não atende ao tempo de execução assintótico requerido."
                    alt = Alternativa(
                        questao_id=q.id,
                        letra=l,
                        texto=alt_texto,
                        comentario_erro=com_erro
                    )
                    db.session.add(alt)

            elif 38 <= num <= 40:
                comp = "especifico"
                area = areas_esp_cc[(num - 38) % len(areas_esp_cc)]
                tipo = "discursiva"
                gabarito = "DISCURSIVA"
                padrao = (
                    f"Padrão de resposta técnico para a questão discursiva {num} ({area}):\n"
                    "1. Descrição formal do modelo relacional ou autômato de estados;\n"
                    "2. Apresentação do pseudocódigo com complexidade O(n log n);\n"
                    "3. Justificativa teórica quanto à corretude e tolerância a falhas."
                )
                enunciado = f"Uma equipe de desenvolvimento necessita modelar uma solução de alto desempenho para {area.lower()}. Apresente a arquitetura recomendada e o pseudocódigo da função principal. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=cc_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta="Padrão oficial com critérios de correção da banca examinadora.",
                    comentario_status="publicado",
                    padrao_resposta=padrao,
                    anulada=False
                )
                db.session.add(q)

    # 5. Questões ENADE 2023 - Componente Específico - Engenharia de Computação (12 questões: 11 a 22)
    ec2023_count = Questao.query.filter_by(ano=2023, curso_id=ec_id).count()
    if ec2023_count == 0:
        click.echo("Cadastrando 12 questões específicas do ENADE 2023 (Engenharia de Computação)...")
        for num in range(11, 23):
            if 11 <= num <= 20:
                comp = "especifico"
                area = areas_esp_ec[(num - 11) % len(areas_esp_ec)]
                tipo = "objetiva"
                gabarito = letras[(num + 2) % 5]
                anulada = (num == 15)  # Q15 anulada
                comentario = f"Comentário da questão {num} ({area}): a alternativa {gabarito} aborda com precisão os parâmetros de temporização e arquitetura de hardware."
                enunciado = f"Considere a implementação de um sistema crítico em hardware na área de {area}. Com base nos requisitos de latência, consumo energético e sincronismo de clock, assinale a opção correta. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=ec_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta=comentario,
                    comentario_status='publicado',
                    padrao_resposta=None,
                    anulada=anulada
                )
                db.session.add(q)
                db.session.flush()

                for idx, l in enumerate(letras):
                    alt_texto = f"Configuração de circuito ou módulo proposta na opção {l} para {area}."
                    com_erro = None if (l == gabarito) else f"A alternativa {l} viola as margens de ruído ou requisitos de tempo de setup e hold."
                    alt = Alternativa(
                        questao_id=q.id,
                        letra=l,
                        texto=alt_texto,
                        comentario_erro=com_erro
                    )
                    db.session.add(alt)

            elif 21 <= num <= 22:
                comp = "especifico"
                area = areas_esp_ec[(num - 21) % len(areas_esp_ec)]
                tipo = "discursiva"
                gabarito = "DISCURSIVA"
                padrao = (
                    f"Padrão de resposta técnico para a questão discursiva {num} ({area}):\n"
                    "1. Especificação de registradores e temporizadores de interrupção;\n"
                    "2. Diagrama lógico do circuito e tabela de estados;\n"
                    "3. Equacionamento temporal do pipeline e análise de taxa de transferência."
                )
                enunciado = f"Projete a arquitetura de controle e o fluxo de dados para um módulo de {area.lower()}. Justifique as decisões de projeto considerando tempo de propagação e taxa de amostragem. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=ec_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta="Padrão oficial com critérios de correção da banca examinadora.",
                    comentario_status="publicado",
                    padrao_resposta=padrao,
                    anulada=False
                )
                db.session.add(q)

    # 6. Questões ENADE 2023 - Componente Específico - Sistemas de Informação (12 questões: 11 a 22)
    si2023_count = Questao.query.filter_by(ano=2023, curso_id=si_id).count()
    if si2023_count == 0:
        click.echo("Cadastrando 12 questões específicas do ENADE 2023 (Sistemas de Informação)...")
        for num in range(11, 23):
            if 11 <= num <= 20:
                comp = "especifico"
                area = areas_esp_si[(num - 11) % len(areas_esp_si)]
                tipo = "objetiva"
                gabarito = letras[(num + 3) % 5]
                anulada = False
                comentario = f"Comentário da questão {num} ({area}): a alternativa {gabarito} reflete as melhores práticas de governança e alinhamento estratégico."
                enunciado = f"No contexto de governança e processos de negócio para {area.lower()}, analise o cenário corporativo apresentado e assinale a alternativa adequada. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=si_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta=comentario,
                    comentario_status='publicado',
                    padrao_resposta=None,
                    anulada=anulada
                )
                db.session.add(q)
                db.session.flush()

                for idx, l in enumerate(letras):
                    alt_texto = f"Prática organizacional descrita na alternativa {l} para {area}."
                    com_erro = None if (l == gabarito) else f"A alternativa {l} não está em conformidade com as diretrizes do framework COBIT ou ITIL."
                    alt = Alternativa(
                        questao_id=q.id,
                        letra=l,
                        texto=alt_texto,
                        comentario_erro=com_erro
                    )
                    db.session.add(alt)

            elif 21 <= num <= 22:
                comp = "especifico"
                area = areas_esp_si[(num - 21) % len(areas_esp_si)]
                tipo = "discursiva"
                gabarito = "DISCURSIVA"
                padrao = (
                    f"Padrão de resposta técnico para a questão discursiva {num} ({area}):\n"
                    "1. Identificação dos stakeholders e mapeamento dos requisitos de conformidade;\n"
                    "2. Modelagem dos processos AS-IS e TO-BE com notação BPMN;\n"
                    "3. Plano de contingência e indicadores-chave de desempenho (KPIs)."
                )
                enunciado = f"Elabore uma proposta de transformação digital integrando {area.lower()} às estratégias de negócio da organização. Apresente os indicadores-chave de desempenho (KPIs) recomendados. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2023,
                    curso_id=si_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta="Padrão oficial com critérios de correção da banca examinadora.",
                    comentario_status="publicado",
                    padrao_resposta=padrao,
                    anulada=False
                )
                db.session.add(q)

    # 7. Questões ENADE 2021 - Formação Geral (Comum: curso_id = None)
    fg2021_count = Questao.query.filter_by(ano=2021, componente="formacao_geral").count()
    if fg2021_count == 0:
        click.echo("Cadastrando 4 questões de Formação Geral do ENADE 2021 (Comuns)...")
        for num in range(1, 5):
            if 1 <= num <= 3:
                comp = "formacao_geral"
                area = areas_fg[(num - 1) % len(areas_fg)]
                tipo = "objetiva"
                gabarito = letras[num % 5]
                enunciado = f"Leia o excerto acerca das transformações na sociedade digital e {area.lower()}. Indique a conclusão válida. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2021,
                    curso_id=None,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta=f"A opção {gabarito} sintetiza a tese do autor.",
                    comentario_status="publicado",
                    padrao_resposta=None,
                    anulada=False
                )
                db.session.add(q)
                db.session.flush()
                for l in letras:
                    alt = Alternativa(
                        questao_id=q.id,
                        letra=l,
                        texto=f"Proposição {l} para a questão {num} de 2021.",
                        comentario_erro=None if l == gabarito else f"Item {l} incorreto."
                    )
                    db.session.add(alt)

            elif num == 4:
                comp = "formacao_geral"
                area = "Ética e cidadania"
                tipo = "discursiva"
                padrao = "Padrão de resposta esperado com fundamentação sociológica e diretrizes legais vigentes."
                enunciado = "Discorra sobre a governança de dados pessoais e o princípio da transparência pública. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2021,
                    curso_id=None,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial="DISCURSIVA",
                    comentario_correta="Padrão oficial INEP 2021.",
                    comentario_status="publicado",
                    padrao_resposta=padrao,
                    anulada=False
                )
                db.session.add(q)

    # 8. Questões ENADE 2021 - Ciência da Computação (Componente Específico: 5 a 15)
    cc2021_count = Questao.query.filter_by(ano=2021, curso_id=cc_id).count()
    if cc2021_count == 0:
        click.echo("Cadastrando 11 questões específicas do ENADE 2021 (Ciência da Computação)...")
        for num in range(5, 16):
            if 5 <= num <= 14:
                comp = "especifico"
                area = areas_esp_cc[(num - 5) % len(areas_esp_cc)]
                tipo = "objetiva"
                gabarito = letras[(num * 3) % 5]
                anulada = (num == 14)  # 1 questão anulada em 2021
                sem_comentario = (num in [7, 11])
                comentario = None if sem_comentario else f"Comentário da questão {num} de 2021: a opção {gabarito} atende à definição teórica de {area}."
                enunciado = f"Com relação aos protocolos e estruturas em {area}, avalie as implementações sob a ótica da escalabilidade. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2021,
                    curso_id=cc_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial=gabarito,
                    comentario_correta=comentario,
                    comentario_status='publicado' if comentario else 'rascunho',
                    padrao_resposta=None,
                    anulada=anulada
                )
                db.session.add(q)
                db.session.flush()
                for l in letras:
                    alt = Alternativa(
                        questao_id=q.id,
                        letra=l,
                        texto=f"Alternativa {l} sobre {area} (2021).",
                        comentario_erro=None if (l == gabarito or sem_comentario) else f"Opção {l} incorreta."
                    )
                    db.session.add(alt)

            elif num == 15:
                comp = "especifico"
                area = "Banco de Dados"
                tipo = "discursiva"
                padrao = (
                    "Padrão esperado para a questão 15:\n"
                    "1. Identificação de anomalias de concorrência em níveis de isolamento;\n"
                    "2. Proposta de reescrita da consulta SQL com planos otimizados;\n"
                    "3. Demonstração de propriedades ACID garantidas."
                )
                enunciado = "Considere um sistema bancário distribuído com alta concorrência de transações. Elabore uma estratégia de isolamento que previna leituras sujas e deadlocks. [questão fictícia para protótipo]"
                q = Questao(
                    ano=2021,
                    curso_id=cc_id,
                    numero=num,
                    componente=comp,
                    area=area,
                    tipo=tipo,
                    enunciado=enunciado,
                    gabarito_oficial="DISCURSIVA",
                    comentario_correta="Padrão oficial INEP 2021.",
                    comentario_status="publicado",
                    padrao_resposta=padrao,
                    anulada=False
                )
                db.session.add(q)

    db.session.commit()
    click.echo("Seed concluído com sucesso!")


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Cria todas as tabelas do banco de dados."""
    db.create_all()
    click.echo("Banco de dados inicializado.")


@click.command("seed")
@with_appcontext
def seed_command():
    """Popula o banco com os dados iniciais."""
    db.create_all()
    seed_database()


@click.command("criar-admin")
@click.option("--nome", required=True, help="Nome completo do administrador.")
@click.option("--email", required=True, help="E-mail do administrador.")
@with_appcontext
def criar_admin_command(nome, email):
    """Cria um administrador ou promove um usuário existente e gera link de senha (48h)."""
    db.create_all()
    email_norm = email.strip().lower()
    usuario = Usuario.query.filter_by(email=email_norm).first()

    if usuario:
        perfil_ant = usuario.perfil
        usuario.perfil = "admin"
        usuario.ativo = True
        db.session.add(AlteracaoUsuario(
            usuario_alvo_id=usuario.id,
            alterado_por_id=None,
            tipo="perfil",
            valor_anterior=perfil_ant,
            valor_novo="admin",
            motivo="via linha de comando"
        ))
        click.echo(f"Usuário '{email_norm}' promovido a administrador.")
    else:
        usuario = Usuario(
            nome=nome.strip(),
            email=email_norm,
            perfil="admin",
            ativo=True
        )
        usuario.set_senha(secrets.token_urlsafe(32))
        db.session.add(usuario)
        db.session.flush()
        db.session.add(AlteracaoUsuario(
            usuario_alvo_id=usuario.id,
            alterado_por_id=None,
            tipo="criacao",
            valor_anterior=None,
            valor_novo="admin",
            motivo="via linha de comando"
        ))
        click.echo(f"Administrador '{email_norm}' criado.")

    token_str = secrets.token_urlsafe(32)
    expira_em = datetime.now(timezone.utc) + timedelta(hours=48)
    token_obj = TokenRecuperacao(
        usuario_id=usuario.id,
        token=token_str,
        expira_em=expira_em,
        usado=False
    )
    db.session.add(token_obj)
    db.session.commit()

    link = f"/redefinir-senha/{token_str}"
    click.echo(f"Link para definir a senha (válido por 48h): {link}")


def seed_historico_usuario(email: str) -> bool:
    """Popula ~7 semanas de histórico de estudo e 5 simulados finalizados para demonstração (idempotente)."""
    from app.models import Simulado, SimuladoQuestao, SimuladoResposta, RespostaEstudo

    email_norm = email.strip().lower()
    usuario = Usuario.query.filter_by(email=email_norm).first()
    if not usuario:
        click.echo(f"Usuário '{email_norm}' não encontrado.")
        return False

    # Idempotência: verifica se já existe histórico suficiente (respostas retroativas ou simulados finalizados)
    agora = datetime.now(timezone.utc)
    limite_retro = agora - timedelta(days=7)
    respostas_retro = RespostaEstudo.query.filter(
        RespostaEstudo.usuario_id == usuario.id,
        RespostaEstudo.respondida_em < limite_retro
    ).count()
    simulados_fin = Simulado.query.filter(
        Simulado.usuario_id == usuario.id,
        Simulado.finalizado_em != None  # noqa: E711
    ).count()

    if respostas_retro > 0 or simulados_fin >= 5:
        click.echo(f"Histórico de demonstração já existe para '{email_norm}'. Nada foi duplicado.")
        return False

    # Busca questões objetivas válidas (não anuladas) do curso do usuário + Formação Geral
    questoes_obj = Questao.query.filter(
        Questao.tipo == "objetiva",
        Questao.anulada == False,  # noqa: E712
        db.or_(Questao.componente == "formacao_geral", Questao.curso_id == usuario.curso_id)
    ).order_by(Questao.ano.desc(), Questao.numero.asc()).all()

    if not questoes_obj:
        click.echo("Nenhuma questão objetiva disponível. Execute 'flask seed' primeiro.")
        return False

    por_area = {}
    for q in questoes_obj:
        por_area.setdefault(q.area, []).append(q)

    # Seleciona até 3 áreas com melhora gradual e 1 área com queda
    areas_disponiveis = list(por_area.keys())
    areas_melhora = [a for a in ["Redes", "Banco de Dados", "Algoritmos"] if a in por_area]
    if len(areas_melhora) < 2:
        areas_melhora = areas_disponiveis[:2]
    area_queda = "Estruturas de Dados" if "Estruturas de Dados" in por_area else (
        next((a for a in areas_disponiveis if a not in areas_melhora), None)
    )

    # Semanas: 7, 6, 5, 4 (anteriores) e 2, 1, 0 (últimas 4, deixando semana 3 sem atividade para mostrar interrupção no gráfico)
    semanas_offsets = [7, 6, 5, 4, 2, 1, 0]

    def _errada(gabarito: str) -> str:
        for letra in ("A", "B", "C", "D", "E"):
            if letra != gabarito:
                return letra
        return "A"

    # Gera respostas no modo estudo (~7 semanas)
    for w_off in semanas_offsets:
        eh_recente = (w_off <= 2)
        base_dt = agora - timedelta(weeks=w_off, days=1)

        # Áreas com melhora: ~33% nas 4 anteriores -> ~83% nas últimas 4 (3 respostas por semana = 12 no ant, 9 no rec)
        for area_nome in areas_melhora:
            qs = por_area[area_nome]
            # 2 a 3 respostas por semana garantindo >= 5 em cada período
            qtd_sem = 3
            for idx in range(qtd_sem):
                q = qs[(w_off + idx) % len(qs)]
                if not eh_recente:
                    acertar = (idx == 0 and w_off <= 5)
                else:
                    acertar = (idx < 2 or w_off == 0)
                marcada = q.gabarito_oficial if acertar else _errada(q.gabarito_oficial)
                db.session.add(RespostaEstudo(
                    usuario_id=usuario.id,
                    questao_id=q.id,
                    alternativa_marcada=marcada,
                    correta=acertar,
                    respondida_em=base_dt + timedelta(hours=idx * 2)
                ))

        # Área com queda: ~83% nas 4 anteriores -> ~33% nas últimas 4
        if area_queda:
            qs_q = por_area[area_queda]
            for idx in range(3):
                q = qs_q[(w_off + idx) % len(qs_q)]
                if not eh_recente:
                    acertar = (idx < 2 or w_off == 7)
                else:
                    acertar = (idx == 0 and w_off == 2)
                marcada = q.gabarito_oficial if acertar else _errada(q.gabarito_oficial)
                db.session.add(RespostaEstudo(
                    usuario_id=usuario.id,
                    questao_id=q.id,
                    alternativa_marcada=marcada,
                    correta=acertar,
                    respondida_em=base_dt + timedelta(hours=8 + idx)
                ))

    # Gera 4 simulados parciais e 1 completo finalizados em semanas diferentes
    # Completo (5 semanas atrás, ~60% de acerto)
    qs_2023 = Questao.query.filter(
        Questao.ano == 2023,
        Questao.anulada == False,  # noqa: E712
        db.or_(Questao.componente == "formacao_geral", Questao.curso_id == usuario.curso_id)
    ).order_by(Questao.numero.asc()).all()

    if qs_2023:
        fin_comp = agora - timedelta(weeks=5, days=2)
        ini_comp = fin_comp - timedelta(hours=3, minutes=15)
        sim_comp = Simulado(
            usuario_id=usuario.id,
            tipo="completo",
            edicao_ano=2023,
            iniciado_em=ini_comp,
            duracao_segundos=14400,
            finalizado_em=fin_comp,
            finalizado_por="entrega"
        )
        db.session.add(sim_comp)
        db.session.flush()
        for ordem, q in enumerate(qs_2023, start=1):
            db.session.add(SimuladoQuestao(simulado_id=sim_comp.id, questao_id=q.id, ordem=ordem))
            if q.tipo == "objetiva":
                acertar = (ordem % 5 != 0 and ordem % 3 != 0)  # ~53-60%
                marcada = q.gabarito_oficial if acertar else _errada(q.gabarito_oficial)
                db.session.add(SimuladoResposta(
                    simulado_id=sim_comp.id,
                    questao_id=q.id,
                    alternativa_marcada=marcada,
                    atualizada_em=fin_comp - timedelta(minutes=10)
                ))

    # 4 simulados parciais em semanas diferentes (6, 4, 2, 1 semanas atrás) com evolução 40% -> 50% -> 70% -> 80%
    parciais_config = [
        (6, "Redes", 4, "entrega"),
        (4, "Banco de Dados", 5, "entrega"),
        (2, "Algoritmos", 7, "tempo"),
        (1, "Redes", 8, "entrega"),
    ]
    for w_off, area_alvo, num_acertos, motivo in parciais_config:
        qs_area = por_area.get(area_alvo) or questoes_obj
        qs_sel = (qs_area * 3)[:10]  # 10 questões
        if not qs_sel:
            continue
        fin_p = agora - timedelta(weeks=w_off, days=3)
        gasto_min = 60 if motivo == "tempo" else 38
        ini_p = fin_p - timedelta(minutes=gasto_min)
        sim_p = Simulado(
            usuario_id=usuario.id,
            tipo="parcial",
            componente="especifico",
            area=area_alvo,
            iniciado_em=ini_p,
            duracao_segundos=3600,
            finalizado_em=fin_p,
            finalizado_por=motivo
        )
        db.session.add(sim_p)
        db.session.flush()
        # Evita questao_id duplicado em SimuladoQuestao/SimuladoResposta se área tiver < 10 questões
        vistas = set()
        ordem = 1
        for q in qs_area:
            if q.id in vistas:
                continue
            vistas.add(q.id)
            db.session.add(SimuladoQuestao(simulado_id=sim_p.id, questao_id=q.id, ordem=ordem))
            acertar = (ordem <= max(1, round(num_acertos * len(qs_area) / 10)))
            marcada = q.gabarito_oficial if acertar else _errada(q.gabarito_oficial)
            db.session.add(SimuladoResposta(
                simulado_id=sim_p.id,
                questao_id=q.id,
                alternativa_marcada=marcada,
                atualizada_em=fin_p - timedelta(minutes=2)
            ))
            ordem += 1
            if ordem > 10:
                break

    db.session.commit()
    click.echo(f"Histórico de demonstração criado com sucesso para '{email_norm}'.")
    return True


@click.command("seed-historico")
@click.option("--email", default="ana@teste.com", help="E-mail do estudante para popular o histórico.")
@with_appcontext
def seed_historico_command(email):
    """Popula ~7 semanas de respostas e 5 simulados finalizados para demonstração."""
    db.create_all()
    seed_historico_usuario(email)
