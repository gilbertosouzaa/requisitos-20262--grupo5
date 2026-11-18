import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Curso, Usuario, Questao, Alternativa

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
