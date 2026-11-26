from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.extensions import db
from app.models import Questao, RespostaEstudo, Simulado

try:
    SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
except ZoneInfoNotFoundError:
    SAO_PAULO_TZ = timezone(timedelta(hours=-3))


def formatar_tempo_legivel(segundos: int) -> str:
    """Formata uma duração em segundos de forma legível e consistente.

    Regras:
    - < 1 minuto -> "menos de 1 min"
    - < 1 hora -> "38 min"
    - >= 1 hora -> "1h00", "3h15"
    """
    segundos = max(0, int(segundos))
    if segundos < 60:
        return "menos de 1 min"
    if segundos < 3600:
        return f"{segundos // 60} min"
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    return f"{horas}h{minutos:02d}"


def to_sao_paulo(dt: datetime) -> datetime:
    """Converte um datetime (naive tratado como UTC) para o fuso America/Sao_Paulo."""
    if dt is None:
        return datetime.now(SAO_PAULO_TZ)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SAO_PAULO_TZ)


def inicio_semana_sp(dt: datetime):
    """Retorna a data da segunda-feira (início da semana) no fuso America/Sao_Paulo."""
    dt_sp = to_sao_paulo(dt)
    return dt_sp.date() - timedelta(days=dt_sp.weekday())


def _obter_respostas_estudo_mais_recentes(usuario_id: int) -> dict:
    """Retorna um dicionário {questao_id: RespostaEstudo} com a resposta mais recente por questão."""
    respostas = (
        RespostaEstudo.query
        .filter_by(usuario_id=usuario_id)
        .order_by(RespostaEstudo.respondida_em.asc(), RespostaEstudo.id.asc())
        .all()
    )
    return {r.questao_id: r for r in respostas}


def _extrair_eventos_resposta(usuario_id: int, origem: str = 'tudo', componente: str = 'todos', area: str = None) -> list:
    """Extrai todas as respostas objetivas válidas (não anuladas) com data, área e acerto.

    Regras:
    - RN08: apenas objetivas respondidas (em branco e discursivas não entram).
    - RN03: questões anuladas não entram.
    - RN09: usa a área cadastrada na questão.
    - Evolução semanal conta CADA resposta dada na semana (inclusive repetições no modo estudo).
    - Simulados em andamento (finalizado_em is None) NÃO entram.
    """
    eventos = []

    if origem in ('tudo', 'estudo'):
        q_estudo = (
            RespostaEstudo.query
            .join(Questao, RespostaEstudo.questao_id == Questao.id)
            .filter(
                RespostaEstudo.usuario_id == usuario_id,
                Questao.tipo == 'objetiva',
                Questao.anulada == False,  # noqa: E712
                RespostaEstudo.alternativa_marcada != None  # noqa: E711
            )
        )
        if componente in ('formacao_geral', 'especifico'):
            q_estudo = q_estudo.filter(Questao.componente == componente)
        if area and area != 'geral':
            q_estudo = q_estudo.filter(Questao.area == area)

        for r in q_estudo.all():
            eventos.append({
                'data': r.respondida_em,
                'area': r.questao.area,
                'correta': bool(r.correta),
            })

    if origem in ('tudo', 'simulados'):
        simulados = (
            Simulado.query
            .filter(
                Simulado.usuario_id == usuario_id,
                Simulado.finalizado_em != None  # noqa: E711
            )
            .all()
        )
        for sim in simulados:
            for resp in sim.respostas:
                q = resp.questao
                if not q or q.tipo != 'objetiva' or q.anulada:
                    continue
                if not resp.alternativa_marcada:
                    continue
                if componente in ('formacao_geral', 'especifico') and q.componente != componente:
                    continue
                if area and area != 'geral' and q.area != area:
                    continue
                eventos.append({
                    'data': sim.finalizado_em,
                    'area': q.area,
                    'correta': (resp.alternativa_marcada == q.gabarito_oficial),
                })

    return eventos


def calcular_resumo_geral(usuario, origem: str = 'tudo', componente: str = 'todos') -> dict:
    """Calcula os KPIs gerais e o desempenho por área do usuário (RN03, RN08, RN09)."""
    simulados_finalizados = (
        Simulado.query
        .filter(
            Simulado.usuario_id == usuario.id,
            Simulado.finalizado_em != None  # noqa: E711
        )
        .all()
    )
    total_simulados_concluidos = len(simulados_finalizados)
    respostas_estudo = _obter_respostas_estudo_mais_recentes(usuario.id)

    areas_stats = {}
    total_respondidas = 0
    total_acertos = 0
    total_em_branco = 0

    if origem in ('tudo', 'simulados'):
        for sim in simulados_finalizados:
            respostas_sim = {r.questao_id: r for r in sim.respostas}
            for sq in sim.questoes_assoc:
                q = sq.questao
                if q.tipo != 'objetiva' or q.anulada:
                    continue
                if componente != 'todos' and q.componente != componente:
                    continue

                area = q.area
                if area not in areas_stats:
                    areas_stats[area] = {'respondidas': 0, 'acertos': 0, 'em_branco': 0, 'total': 0}
                areas_stats[area]['total'] += 1

                resp = respostas_sim.get(q.id)
                if resp and resp.alternativa_marcada:
                    total_respondidas += 1
                    areas_stats[area]['respondidas'] += 1
                    if resp.alternativa_marcada == q.gabarito_oficial:
                        total_acertos += 1
                        areas_stats[area]['acertos'] += 1
                else:
                    total_em_branco += 1
                    areas_stats[area]['em_branco'] += 1

    if origem in ('tudo', 'estudo'):
        for r in respostas_estudo.values():
            q = r.questao
            if q.tipo != 'objetiva' or q.anulada:
                continue
            if componente != 'todos' and q.componente != componente:
                continue

            area = q.area
            if area not in areas_stats:
                areas_stats[area] = {'respondidas': 0, 'acertos': 0, 'em_branco': 0, 'total': 0}
            areas_stats[area]['total'] += 1
            areas_stats[area]['respondidas'] += 1
            total_respondidas += 1
            if r.correta is True:
                total_acertos += 1
                areas_stats[area]['acertos'] += 1

    tem_dados = (total_respondidas > 0 or total_em_branco > 0)
    percentual_geral = int(round((total_acertos / total_respondidas) * 100)) if total_respondidas > 0 else 0

    areas_lista = []
    for area_nome, dados in areas_stats.items():
        pct = int(round((dados['acertos'] / dados['respondidas']) * 100)) if dados['respondidas'] > 0 else 0
        areas_lista.append({
            'nome': area_nome,
            'area': area_nome,
            'pct': pct,
            'percentual': pct,
            'qtd': f"{dados['acertos']} de {dados['respondidas']} questões",
            'label': f"{area_nome}: {pct}% de acerto",
            'total': dados['total'],
            'respondidas': dados['respondidas'],
            'acertos': dados['acertos'],
        })

    areas_lista.sort(key=lambda x: (x['pct'], x['respondidas']))
    revisar_primeiro = sorted(
        [a for a in areas_lista if a['respondidas'] > 0],
        key=lambda x: (x['pct'], -x['respondidas'])
    )[:2]

    return {
        'tem_dados': tem_dados,
        'percentual_geral': percentual_geral,
        'total_respondidas': total_respondidas,
        'total_acertos': total_acertos,
        'total_simulados': total_simulados_concluidos,
        'total_em_branco': total_em_branco,
        'areas': areas_lista,
        'revisar_primeiro': revisar_primeiro,
    }


def _construir_geometria_svg(semanas: list, area_label: str, variacao_pontos) -> dict:
    """Gera coordenadas, segmentos de linha (interrompidos em semanas sem atividade) e aria-label para o SVG."""
    width = 640
    height = 240
    pad_left = 44
    pad_right = 24
    pad_top = 28
    pad_bottom = 40
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    grid_lines = []
    for pct in (0, 25, 50, 75, 100):
        y = round(pad_top + plot_h * (1.0 - pct / 100.0), 1)
        grid_lines.append({'pct': pct, 'y': y})

    n = len(semanas)
    pontos = []
    segmentos = []
    segmento_atual = []

    for idx, sem in enumerate(semanas):
        x = round(pad_left + (idx / max(1, n - 1)) * plot_w, 1)
        sem['x'] = x
        if sem['tem_atividade'] and sem['percentual'] is not None:
            y = round(pad_top + plot_h * (1.0 - sem['percentual'] / 100.0), 1)
            ponto = {
                'x': x,
                'y': y,
                'label_y': round(y - 10, 1),
                'percentual': sem['percentual'],
                'semana_label': sem['label'],
                'respondidas': sem['respondidas'],
                'acertos': sem['acertos'],
            }
            pontos.append(ponto)
            segmento_atual.append(f"{x},{y}")
        else:
            if len(segmento_atual) >= 2:
                segmentos.append(" ".join(segmento_atual))
            segmento_atual = []

    if len(segmento_atual) >= 2:
        segmentos.append(" ".join(segmento_atual))

    # Aria-label descritivo
    ativos = [s for s in semanas if s['tem_atividade']]
    if len(ativos) >= 2:
        primeiro = ativos[0]
        ultimo = ativos[-1]
        tendencia_txt = ""
        if variacao_pontos is not None:
            sinal = "+" if variacao_pontos > 0 else ""
            tendencia_txt = f" Variação entre as últimas 4 semanas e as 4 anteriores: {sinal}{variacao_pontos} pontos percentuais."
        aria_label = (
            f"Gráfico de evolução semanal de acerto ({area_label}) nas últimas 8 semanas. "
            f"De {primeiro['percentual']}% na semana de {primeiro['label']} para "
            f"{ultimo['percentual']}% na semana de {ultimo['label']}.{tendencia_txt}"
        )
    else:
        aria_label = f"Gráfico de evolução semanal ({area_label}) sem dados suficientes."

    return {
        'width': width,
        'height': height,
        'pad_left': pad_left,
        'pad_right': pad_right,
        'pad_top': pad_top,
        'baseline_y': round(pad_top + plot_h, 1),
        'x_end': width - pad_right,
        'grid_lines': grid_lines,
        'pontos': pontos,
        'segmentos': segmentos,
        'aria_label': aria_label,
    }


def calcular_evolucao_semanal(
    usuario,
    origem: str = 'tudo',
    componente: str = 'todos',
    evolucao_area: str = 'geral',
    agora: datetime = None
) -> dict:
    """Calcula a evolução semanal das últimas 8 semanas (segunda a domingo, America/Sao_Paulo)."""
    agora = agora or datetime.now(timezone.utc)
    semana_atual = inicio_semana_sp(agora)

    # Primeiro extrai todos os eventos (sem filtro de área) para listar áreas disponíveis
    todos_eventos = _extrair_eventos_resposta(usuario.id, origem=origem, componente=componente, area=None)
    areas_disponiveis = sorted({ev['area'] for ev in todos_eventos if ev['area']})

    area_selecionada = evolucao_area if evolucao_area in areas_disponiveis else 'geral'
    eventos = (
        todos_eventos
        if area_selecionada == 'geral'
        else [ev for ev in todos_eventos if ev['area'] == area_selecionada]
    )

    inicios_8_semanas = [semana_atual - timedelta(weeks=i) for i in range(7, -1, -1)]
    mapa_semanas = {
        ini: {
            'inicio': ini,
            'label': ini.strftime('%d/%m'),
            'periodo_completo': f"{ini.strftime('%d/%m/%Y')} a {(ini + timedelta(days=6)).strftime('%d/%m/%Y')}",
            'respondidas': 0,
            'acertos': 0,
            'percentual': None,
            'tem_atividade': False,
        }
        for ini in inicios_8_semanas
    }

    for ev in eventos:
        ini_ev = inicio_semana_sp(ev['data'])
        if ini_ev in mapa_semanas:
            mapa_semanas[ini_ev]['respondidas'] += 1
            if ev['correta']:
                mapa_semanas[ini_ev]['acertos'] += 1

    semanas = []
    for ini in inicios_8_semanas:
        s = mapa_semanas[ini]
        if s['respondidas'] > 0:
            s['tem_atividade'] = True
            s['percentual'] = int(round((s['acertos'] / s['respondidas']) * 100))
        semanas.append(s)

    semanas_com_atividade = sum(1 for s in semanas if s['tem_atividade'])
    exibir_grafico = semanas_com_atividade >= 2

    # Comparação: últimas 4 semanas (índices 4..7) vs 4 semanas anteriores (índices 0..3)
    anteriores_4 = semanas[:4]
    ultimas_4 = semanas[4:]

    ant_resp = sum(s['respondidas'] for s in anteriores_4)
    ant_acertos = sum(s['acertos'] for s in anteriores_4)
    ult_resp = sum(s['respondidas'] for s in ultimas_4)
    ult_acertos = sum(s['acertos'] for s in ultimas_4)

    ant_pct = int(round((ant_acertos / ant_resp) * 100)) if ant_resp > 0 else None
    ult_pct = int(round((ult_acertos / ult_resp) * 100)) if ult_resp > 0 else None
    variacao_pontos = (ult_pct - ant_pct) if (ult_pct is not None and ant_pct is not None) else None

    area_label = "Geral" if area_selecionada == 'geral' else area_selecionada
    svg = _construir_geometria_svg(semanas, area_label, variacao_pontos)

    return {
        'areas_disponiveis': areas_disponiveis,
        'area_selecionada': area_selecionada,
        'semanas': semanas,
        'semanas_com_atividade': semanas_com_atividade,
        'exibir_grafico': exibir_grafico,
        'ultimas_4_pct': ult_pct,
        'anteriores_4_pct': ant_pct,
        'ultimas_4_resp': ult_resp,
        'anteriores_4_resp': ant_resp,
        'variacao_pontos': variacao_pontos,
        'svg': svg,
    }


def calcular_mudancas_4_semanas(
    usuario,
    origem: str = 'tudo',
    componente: str = 'todos',
    agora: datetime = None,
    minimo_respostas: int = 5
) -> dict:
    """Compara, por área, as últimas 4 semanas com as 4 semanas anteriores.

    Uma área só entra se tiver pelo menos `minimo_respostas` (5) objetivas respondidas em CADA período.
    """
    agora = agora or datetime.now(timezone.utc)
    semana_atual = inicio_semana_sp(agora)

    set_ultimas_4 = {semana_atual - timedelta(weeks=i) for i in range(0, 4)}
    set_anteriores_4 = {semana_atual - timedelta(weeks=i) for i in range(4, 8)}

    eventos = _extrair_eventos_resposta(usuario.id, origem=origem, componente=componente, area=None)
    stats_por_area = {}

    for ev in eventos:
        ini_ev = inicio_semana_sp(ev['data'])
        if ini_ev not in set_ultimas_4 and ini_ev not in set_anteriores_4:
            continue
        area = ev['area']
        if area not in stats_por_area:
            stats_por_area[area] = {
                'ult_resp': 0, 'ult_acertos': 0,
                'ant_resp': 0, 'ant_acertos': 0,
            }
        if ini_ev in set_ultimas_4:
            stats_por_area[area]['ult_resp'] += 1
            if ev['correta']:
                stats_por_area[area]['ult_acertos'] += 1
        else:
            stats_por_area[area]['ant_resp'] += 1
            if ev['correta']:
                stats_por_area[area]['ant_acertos'] += 1

    melhorou = []
    atencao = []
    elegiveis = 0

    for area, st in stats_por_area.items():
        if st['ult_resp'] < minimo_respostas or st['ant_resp'] < minimo_respostas:
            continue
        elegiveis += 1
        pct_antes = int(round((st['ant_acertos'] / st['ant_resp']) * 100))
        pct_agora = int(round((st['ult_acertos'] / st['ult_resp']) * 100))
        diff = pct_agora - pct_antes
        item = {
            'area': area,
            'pct_antes': pct_antes,
            'pct_agora': pct_agora,
            'diff': diff,
            'diff_abs': abs(diff),
        }
        if diff > 0:
            melhorou.append(item)
        elif diff < 0:
            atencao.append(item)

    melhorou.sort(key=lambda x: (-x['diff'], x['area']))
    atencao.sort(key=lambda x: (x['diff'], x['area']))

    return {
        'tem_dados': elegiveis > 0,
        'melhorou': melhorou[:3],
        'atencao': atencao[:3],
    }


def _formatar_tipo_simulado(sim: Simulado) -> str:
    """Formata o rótulo do tipo de simulado para exibição em tabelas."""
    if sim.tipo == 'completo':
        return f"Prova completa · ENADE {sim.edicao_ano}"
    qtd = len(sim.questoes_assoc)
    if sim.area and sim.area != 'todas':
        escope = sim.area
    elif sim.componente == 'formacao_geral':
        escope = "Formação Geral"
    elif sim.componente == 'especifico':
        escope = "Componente Específico"
    else:
        escope = "Misto"
    return f"Parcial · {escope} · {qtd} questões"


def obter_historico_simulados(
    usuario,
    tipo_filtro: str = 'todos',
    pagina: int = 1,
    por_pagina: int = 10,
    limite: int = None
) -> dict:
    """Retorna simulados finalizados do usuário com variação em relação ao anterior do MESMO tipo."""
    simulados_asc = (
        Simulado.query
        .filter(
            Simulado.usuario_id == usuario.id,
            Simulado.finalizado_em != None  # noqa: E711
        )
        .order_by(Simulado.finalizado_em.asc(), Simulado.id.asc())
        .all()
    )

    ultimo_pct_por_grupo = {}
    itens_cronologicos = []

    for sim in simulados_asc:
        respondidas = 0
        acertos = 0
        for resp in sim.respostas:
            q = resp.questao
            if q and q.tipo == 'objetiva' and not q.anulada and resp.alternativa_marcada:
                respondidas += 1
                if resp.alternativa_marcada == q.gabarito_oficial:
                    acertos += 1

        pct = int(round((acertos / respondidas) * 100)) if respondidas > 0 else 0
        if sim.tipo == 'completo':
            grupo = ('completo', None, None)
        else:
            grupo = ('parcial', sim.componente or 'especifico', sim.area or 'todas')

        prev_pct = ultimo_pct_por_grupo.get(grupo)
        variacao = (pct - prev_pct) if prev_pct is not None else None
        ultimo_pct_por_grupo[grupo] = pct

        if sim.finalizado_em and sim.iniciado_em:
            gasto_seg = int((sim.finalizado_em - sim.iniciado_em).total_seconds())
        else:
            gasto_seg = 0

        data_sp = to_sao_paulo(sim.finalizado_em)

        itens_cronologicos.append({
            'id': sim.id,
            'tipo': sim.tipo,
            'tipo_label': _formatar_tipo_simulado(sim),
            'data': data_sp.strftime('%d/%m/%Y'),
            'data_hora': data_sp.strftime('%d/%m/%Y %H:%M'),
            'percentual': pct,
            'respondidas': respondidas,
            'acertos': acertos,
            'variacao': variacao,
            'tempo_utilizado': formatar_tempo_legivel(gasto_seg),
            'finalizado_por': 'Entrega' if sim.finalizado_por == 'entrega' else 'Tempo esgotado',
            'url': f"/simulados/{sim.id}/resultado",
        })

    # Mais recente para mais antigo
    itens_desc = list(reversed(itens_cronologicos))

    if tipo_filtro in ('completo', 'parcial'):
        itens_filtrados = [it for it in itens_desc if it['tipo'] == tipo_filtro]
    else:
        itens_filtrados = itens_desc

    total_itens = len(itens_filtrados)

    if limite is not None:
        itens_pagina = itens_filtrados[:limite]
        total_paginas = 1
        pagina_atual = 1
    else:
        total_paginas = max(1, (total_itens + por_pagina - 1) // por_pagina)
        pagina_atual = max(1, min(pagina, total_paginas))
        inicio = (pagina_atual - 1) * por_pagina
        itens_pagina = itens_filtrados[inicio:inicio + por_pagina]

    return {
        'itens': itens_pagina,
        'total_itens': total_itens,
        'total_geral': len(itens_desc),
        'pagina': pagina_atual,
        'por_pagina': por_pagina,
        'total_paginas': total_paginas,
        'tem_anterior': pagina_atual > 1,
        'tem_proxima': pagina_atual < total_paginas,
    }


def obter_simulado_em_andamento(usuario) -> dict:
    """Verifica se há simulado em andamento; se expirado, finaliza-o. Retorna resumo ou None."""
    simulado_ativo = Simulado.query.filter_by(
        usuario_id=usuario.id,
        finalizado_em=None
    ).first()

    if not simulado_ativo:
        return None

    if simulado_ativo.is_expirado():
        simulado_ativo.finalizar(motivo='tempo')
        db.session.commit()
        return None

    restante_s = simulado_ativo.get_tempo_restante_segundos()
    restante_fmt = formatar_tempo_legivel(restante_s)
    tipo_txt = _formatar_tipo_simulado(simulado_ativo)

    return {
        'id': simulado_ativo.id,
        'tipo_label': tipo_txt,
        'tempo_restante': restante_fmt,
        'detalhes': f"{tipo_txt} · Tempo restante: {restante_fmt}",
        'url': f"/simulados/{simulado_ativo.id}",
    }


def obter_tendencia_inicio(usuario, agora: datetime = None):
    """Retorna resumo da tendência nas últimas 4 semanas vs 4 anteriores para o card do Início (T05).

    Retorna None se não houver dados em ambos os períodos.
    """
    evolucao = calcular_evolucao_semanal(usuario, origem='tudo', componente='todos', evolucao_area='geral', agora=agora)
    variacao = evolucao['variacao_pontos']
    if variacao is None:
        return None

    if variacao > 0:
        simbolo = "▲"
        texto = f"▲ +{variacao} pontos nas últimas 4 semanas"
        classe = "trend-up"
    elif variacao < 0:
        simbolo = "▼"
        texto = f"▼ {variacao} pontos nas últimas 4 semanas"
        classe = "trend-down"
    else:
        simbolo = "—"
        texto = "Estável (0 pontos) nas últimas 4 semanas"
        classe = "trend-flat"

    return {
        'variacao': variacao,
        'simbolo': simbolo,
        'texto': texto,
        'classe': classe,
    }
