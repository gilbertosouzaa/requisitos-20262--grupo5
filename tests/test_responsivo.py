import os
import threading
import pytest
from werkzeug.serving import make_server

sync_api = pytest.importorskip("playwright.sync_api")

from config import TestConfig
from app import create_app
from app.extensions import db
from app.models import Questao, RespostaEstudo, Simulado, SimuladoQuestao, SimuladoResposta, Usuario
from app.seed import seed_database, seed_historico_usuario


class LiveServerConfig(TestConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:?cache=shared"
    WTF_CSRF_ENABLED = True


@pytest.fixture(scope="module")
def live_server():
    import tempfile
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    class TempDBConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        WTF_CSRF_ENABLED = True

    app = create_app(TempDBConfig)
    with app.app_context():
        db.create_all()
        seed_database()
        seed_historico_usuario("ana@teste.com")

        # Cria também um simulado em andamento para testar /simulados/<id>
        ana = Usuario.query.filter_by(email="ana@teste.com").first()
        q1 = Questao.query.filter_by(tipo="objetiva", anulada=False).first()
        qs = Questao.query.filter_by(tipo="objetiva", anulada=False).limit(10).all()
        sim_ativo = Simulado(
            usuario_id=ana.id,
            tipo="parcial",
            componente="ambos",
            area="todas",
            duracao_segundos=3600,
        )
        db.session.add(sim_ativo)
        db.session.flush()
        for idx, q in enumerate(qs, start=1):
            db.session.add(SimuladoQuestao(simulado_id=sim_ativo.id, questao_id=q.id, ordem=idx))
        db.session.commit()

        sim_ativo_id = sim_ativo.id
        sim_finalizado = Simulado.query.filter(
            Simulado.usuario_id == ana.id,
            Simulado.finalizado_em != None  # noqa: E711
        ).first()
        sim_finalizado_id = sim_finalizado.id
        questao_id = q1.id
        resp_estudo = RespostaEstudo.query.filter_by(usuario_id=ana.id).first()
        questao_respondida_id = resp_estudo.questao_id

    server = make_server("127.0.0.1", 0, app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "questao_id": questao_id,
        "questao_respondida_id": questao_respondida_id,
        "sim_ativo_id": sim_ativo_id,
        "sim_finalizado_id": sim_finalizado_id,
    }

    server.shutdown()
    try:
        os.remove(db_path)
    except OSError:
        pass


LARGURAS = [360, 390, 768, 1280]


@pytest.mark.responsivo
@pytest.mark.parametrize("largura", LARGURAS)
def test_layout_responsivo_sem_rolagem_e_alvos_44px(live_server, largura):
    """Verifica sem rolagem horizontal, alvos >= 44x44px e salva screenshots por largura."""
    base_url = live_server["base_url"]
    rotas_publicas = [
        ("landing", "/"),
        ("entrar", "/entrar"),
        ("cadastro", "/cadastro"),
        ("questoes", "/questoes"),
        ("questao", f"/questoes/{live_server['questao_id']}"),
    ]
    rotas_autenticadas = [
        ("inicio", "/inicio"),
        ("questao_respondida", f"/questoes/{live_server['questao_respondida_id']}"),
        ("simulado_novo", "/simulados/novo"),
        ("simulado_ativo", f"/simulados/{live_server['sim_ativo_id']}"),
        ("resultado", f"/simulados/{live_server['sim_finalizado_id']}/resultado"),
        ("desempenho", "/desempenho"),
        ("historico", "/simulados/historico"),
    ]

    shots_dir = os.path.join("tests", "screenshots", str(largura))
    os.makedirs(shots_dir, exist_ok=True)

    with sync_api.sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": largura, "height": 844})
        page = context.new_page()

        def verificar_pagina(nome, path):
            page.goto(f"{base_url}{path}", wait_until="networkidle")
            page.screenshot(path=os.path.join(shots_dir, f"{nome}.png"), full_page=True)

            # 1. Sem rolagem horizontal
            metrics = page.evaluate("""() => ({
                scrollWidth: document.documentElement.scrollWidth,
                innerWidth: window.innerWidth
            })""")
            assert metrics["scrollWidth"] <= metrics["innerWidth"], (
                f"[{largura}px] Rolagem horizontal em {path}: "
                f"scrollWidth={metrics['scrollWidth']} > innerWidth={metrics['innerWidth']}"
            )

            # 2. Botões e links visíveis dentro de <main> e <header> com pelo menos 44x44px
            falhas_alvo = page.evaluate("""() => {
                const els = document.querySelectorAll('header a, header button, main a.btn, main button, main .nav-link');
                const falhas = [];
                for (const el of els) {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || rect.width === 0 || rect.height === 0) {
                        continue;
                    }
                    if (rect.height < 44 || rect.width < 44) {
                        falhas.push({
                            tag: el.tagName,
                            id: el.id || '',
                            text: (el.innerText || '').trim().slice(0, 30),
                            w: Math.round(rect.width),
                            h: Math.round(rect.height)
                        });
                    }
                }
                return falhas;
            }""")
            assert not falhas_alvo, (
                f"[{largura}px] Alvos menores que 44x44px em {path}: {falhas_alvo}"
            )

            # 3. (b) Em 360px, altura do <header> é no máximo 72px
            if largura == 360:
                header_h = page.evaluate("""() => {
                    const h = document.querySelector('header');
                    return h ? h.getBoundingClientRect().height : 0;
                }""")
                assert header_h <= 72, (
                    f"[360px] Header muito alto em {path}: {header_h}px > 72px"
                )

            # 4. (c) Em /questoes a 360px, distância vertical entre #busca e #ordem <= 24px
            if largura == 360 and nome == "questoes":
                gap_busca_ordem = page.evaluate("""() => {
                    const b = document.getElementById('busca').getBoundingClientRect();
                    const o = document.getElementById('ordem').getBoundingClientRect();
                    return o.top - b.bottom;
                }""")
                assert gap_busca_ordem <= 24, (
                    f"[360px] Vão excessivo entre #busca e #ordem em /questoes: {gap_busca_ordem}px > 24px"
                )

            # 5. (a) Na rota de questão JÁ respondida, 'Confirmar resposta' não está visível
            if nome == "questao_respondida":
                assert not page.locator("#btn-confirmar").is_visible(), (
                    f"[{largura}px] Botão 'Confirmar resposta' visível em questão já respondida ({path})"
                )
                assert not page.locator("#acoes-responder").is_visible(), (
                    f"[{largura}px] Barra #acoes-responder visível em questão já respondida ({path})"
                )

        for nome, path in rotas_publicas:
            verificar_pagina(nome, path)

        # Login com Ana
        page.goto(f"{base_url}/entrar", wait_until="networkidle")
        page.fill('input[name="email"]', "ana@teste.com")
        page.fill('input[name="senha"]', "12345678")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        for nome, path in rotas_autenticadas:
            verificar_pagina(nome, path)

        browser.close()
