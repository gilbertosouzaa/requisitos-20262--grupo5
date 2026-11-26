/**
 * simulado.js
 * Lógica do Simulado em Andamento (T09) e Modal de Entrega (T10)
 * Requisitos: RF10, RF11, RF12, RF13, RN04, RN05, RN07, RNF07
 */

document.addEventListener('DOMContentLoaded', () => {
  const configEl = document.getElementById('simulado-config');
  if (!configEl) return;

  const simuladoId = configEl.getAttribute('data-simulado-id');
  let tempoRestante = parseInt(configEl.getAttribute('data-tempo-restante') || '0', 10);
  let totalQuestoes = parseInt(configEl.getAttribute('data-total-questoes') || '0', 10);
  let ordemAtual = parseInt(configEl.getAttribute('data-ordem-inicial') || '1', 10);
  const csrfToken = configEl.getAttribute('data-csrf-token') || '';
  const resultadoUrl = configEl.getAttribute('data-resultado-url') || `/simulados/${simuladoId}/resultado`;

  // Elementos do DOM
  const cronometroDisplay = document.getElementById('cronometro-display');
  const textoStatusSalvamento = document.getElementById('texto-status-salvamento');
  const textoStatusSalvamentoMapa = document.getElementById('status-salvamento-mapa');
  function atualizarTextoSalvamento(msg) {
    if (textoStatusSalvamento) textoStatusSalvamento.textContent = msg;
    if (textoStatusSalvamentoMapa) textoStatusSalvamentoMapa.textContent = msg;
  }
  const qOrdem = document.getElementById('q-ordem');
  const qOrdemCompact = document.getElementById('q-ordem-compact');
  const qSubtitulo = document.getElementById('q-subtitulo');
  const qEnunciado = document.getElementById('q-enunciado');
  const qImagemContainer = document.getElementById('q-imagem-container');
  const qImagemTexto = document.getElementById('q-imagem-texto');
  const containerObjetiva = document.getElementById('container-objetiva');
  const listaAlternativas = document.getElementById('lista-alternativas');
  const containerDiscursiva = document.getElementById('container-discursiva');
  const discursivaTexto = document.getElementById('discursiva-texto');
  const btnAnterior = document.getElementById('btn-anterior');
  const btnProxima = document.getElementById('btn-proxima');
  const btnLimpar = document.getElementById('btn-limpar');
  const mapaGrade = document.getElementById('mapa-grade');
  const mapaRespondidasCount = document.getElementById('mapa-respondidas-count');

  // Modal de Entrega (T10)
  const modalEntrega = document.getElementById('modal-entrega');
  const btnAbrirModal = document.getElementById('btn-abrir-modal-entrega');
  const btnModalVoltar = document.getElementById('btn-modal-voltar');
  const btnModalConfirmar = document.getElementById('btn-modal-confirmar');
  const modalRespondidas = document.getElementById('modal-respondidas');
  const modalTempoRestante = document.getElementById('modal-tempo-restante');
  const modalEmBrancoContainer = document.getElementById('modal-em-branco-container');
  const modalEmBrancoCount = document.getElementById('modal-em-branco-count');
  const modalEmBrancoGrade = document.getElementById('modal-em-branco-grade');

  // Estado em memória
  let questoes = [];
  let respostas = {}; // questao_id -> { alternativa_marcada, texto_resposta }
  let timerInterval = null;
  let debounceTimeout = null;
  const storageQueueKey = `simulado_offline_queue_${simuladoId}`;

  // Formatação de tempo h:mm:ss
  function formatarTempo(segundos) {
    if (segundos <= 0) return '0:00:00';
    const h = Math.floor(segundos / 3600);
    const m = Math.floor((segundos % 3600) / 60);
    const s = segundos % 60;
    const mm = m < 10 ? '0' + m : m;
    const ss = s < 10 ? '0' + s : s;
    return `${h}:${mm}:${ss}`;
  }

  function formatarTempoHorasMin(segundos) {
    if (segundos < 60) return 'menos de 1 min';
    if (segundos < 3600) return `${Math.floor(segundos / 60)} min`;
    const h = Math.floor(segundos / 3600);
    const m = Math.floor((segundos % 3600) / 60);
    return `${h}h${m < 10 ? '0' : ''}${m}`;
  }

  // Atualização visual do cronômetro
  function atualizarCronometro() {
    if (cronometroDisplay) {
      cronometroDisplay.textContent = formatarTempo(tempoRestante);
    }
  }

  // Início do cronômetro (RF10, RN05)
  function iniciarCronometro() {
    atualizarCronometro();
    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
      tempoRestante--;
      if (tempoRestante <= 0) {
        tempoRestante = 0;
        atualizarCronometro();
        clearInterval(timerInterval);
        finalizarSimulado('tempo');
      } else {
        atualizarCronometro();
      }
    }, 1000);
  }

  // Fila Offline (RNF07)
  function obterFilaOffline() {
    try {
      const raw = localStorage.getItem(storageQueueKey);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function salvarFilaOffline(fila) {
    try {
      localStorage.setItem(storageQueueKey, JSON.stringify(fila));
    } catch {}
  }

  function enfileirarOffline(questaoId, payload) {
    const fila = obterFilaOffline();
    // Substitui se já houver alteração pendente para a mesma questão
    const idx = fila.findIndex(item => item.questaoId === questaoId);
    if (idx >= 0) {
      fila[idx] = { questaoId, payload };
    } else {
      fila.push({ questaoId, payload });
    }
    salvarFilaOffline(fila);
  }

  async function processarFilaOffline() {
    const fila = obterFilaOffline();
    if (!fila.length) return;

    const novaFila = [];
    for (const item of fila) {
      try {
        const resp = await fetch(`/api/simulados/${simuladoId}/respostas/${item.questaoId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify(item.payload)
        });
        if (!resp.ok) {
          novaFila.push(item);
        }
      } catch {
        novaFila.push(item);
      }
    }
    salvarFilaOffline(novaFila);
  }

  // Disparo de salvamento de resposta (RNF07)
  async function salvarResposta(questaoId, payload) {
    atualizarTextoSalvamento('Salvando…');

    try {
      const resp = await fetch(`/api/simulados/${simuladoId}/respostas/${questaoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(payload)
      });

      if (resp.status === 409) {
        // Simulado finalizado (RN07)
        window.location.href = resultadoUrl;
        return;
      }

      const json = await resp.json();
      if (json.sucesso) {
        if (json.salvo_em) {
          atualizarTextoSalvamento(`Respostas salvas automaticamente às ${json.salvo_em}`);
        }
        if (typeof json.tempo_restante === 'number') {
          // Sincroniza cronômetro com o servidor
          tempoRestante = json.tempo_restante;
        }
        processarFilaOffline();
      }
    } catch (err) {
      enfileirarOffline(questaoId, payload);
      if (textoStatusSalvamento) {
        textoStatusSalvamento.textContent = 'Sem conexão — tentando de novo';
      }
    }
  }

  // Finalização do Simulado (RF12)
  async function finalizarSimulado(motivo = 'entrega') {
    if (btnModalConfirmar) {
      btnModalConfirmar.disabled = true;
      btnModalConfirmar.textContent = 'Finalizando…';
    }

    try {
      const resp = await fetch(`/api/simulados/${simuladoId}/finalizar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ motivo })
      });
      const data = await resp.json();
      localStorage.removeItem(storageQueueKey);
      window.location.href = data.redirect_url || resultadoUrl;
    } catch {
      // Fallback: submete formulário HTML tradicional
      const formFallback = document.getElementById('form-finalizar-simulado');
      if (formFallback) {
        formFallback.submit();
      } else {
        window.location.href = resultadoUrl;
      }
    }
  }

  // Carregar dados iniciais da API
  async function carregarDadosSimulado() {
    try {
      const res = await fetch(`/api/simulados/${simuladoId}`);
      const data = await res.json();

      if (data.finalizado) {
        window.location.href = data.redirect_url || resultadoUrl;
        return;
      }

      questoes = data.questoes || [];
      totalQuestoes = data.total_questoes || questoes.length;
      tempoRestante = data.tempo_restante || 0;
      respostas = data.respostas || {};

      iniciarCronometro();
      renderizarQuestaoAtual();
      atualizarMapaVisual();
    } catch (e) {
      // Se falhar o fetch inicial da API, inicia o cronômetro com o valor renderizado pelo Jinja
      iniciarCronometro();
    }
  }

  // Renderiza a questão ativa na tela
  function renderizarQuestaoAtual() {
    if (!questoes.length) return;

    const q = questoes.find(item => item.ordem === ordemAtual) || questoes[0];
    if (!q) return;

    ordemAtual = q.ordem;

    // Cabeçalho da questão
    if (qOrdem) qOrdem.textContent = q.ordem;
    if (qOrdemCompact) qOrdemCompact.textContent = `Questão ${q.ordem}/${totalQuestoes}`;
    if (qSubtitulo) {
      const compNome = q.componente === 'formacao_geral' ? 'Formação Geral' : 'Componente Específico';
      const tipoNome = q.tipo === 'objetiva' ? 'Objetiva' : 'Discursiva';
      qSubtitulo.textContent = `${compNome} · ${q.area} · ${tipoNome}`;
    }

    // Enunciado e imagem
    if (qEnunciado) qEnunciado.textContent = q.enunciado;
    if (qImagemContainer && qImagemTexto) {
      if (q.imagem_placeholder && q.imagem_placeholder.trim()) {
        qImagemTexto.textContent = q.imagem_placeholder;
        qImagemContainer.style.display = 'block';
      } else {
        qImagemContainer.style.display = 'none';
      }
    }

    // Resposta atual salva
    const respSalva = respostas[String(q.id)] || {};

    if (q.tipo === 'objetiva') {
      if (containerObjetiva) containerObjetiva.style.display = 'flex';
      if (containerDiscursiva) containerDiscursiva.style.display = 'none';

      // Renderiza alternativas
      if (listaAlternativas) {
        listaAlternativas.innerHTML = '';
        (q.alternativas || []).forEach(alt => {
          const isChecked = (respSalva.alternativa_marcada === alt.letra);
          const label = document.createElement('label');
          label.className = `alt-label ${isChecked ? 'selected' : ''}`;
          label.id = `label-alt-${alt.letra}`;
          label.style.display = 'flex';
          label.style.gap = '14px';
          label.style.alignItems = 'flex-start';
          label.style.minHeight = '52px';
          label.style.padding = '14px 16px';
          label.style.border = isChecked ? '1.5px solid var(--color-border)' : '1.5px solid #555555';
          label.style.borderRadius = '10px';
          label.style.cursor = 'pointer';
          label.style.backgroundColor = isChecked ? '#ececec' : '#ffffff';

          const radio = document.createElement('input');
          radio.type = 'radio';
          radio.name = 'alternativa';
          radio.value = alt.letra;
          radio.checked = isChecked;
          radio.style.width = '20px';
          radio.style.height = '20px';
          radio.style.margin = '2px 0 0';
          radio.style.flex = 'none';
          radio.style.cursor = 'pointer';

          radio.addEventListener('change', () => {
            onAlternativaSelecionada(q.id, alt.letra);
          });

          const letraB = document.createElement('b');
          letraB.style.flex = 'none';
          letraB.style.width = '22px';
          letraB.textContent = alt.letra;

          const textoSpan = document.createElement('span');
          textoSpan.style.flex = '1';
          textoSpan.textContent = alt.texto;

          label.appendChild(radio);
          label.appendChild(letraB);
          label.appendChild(textoSpan);
          listaAlternativas.appendChild(label);
        });
      }
    } else {
      // Discursiva
      if (containerObjetiva) containerObjetiva.style.display = 'none';
      if (containerDiscursiva) containerDiscursiva.style.display = 'flex';

      if (discursivaTexto) {
        discursivaTexto.value = respSalva.texto_resposta || '';
      }
    }

    // Botões de navegação
    if (btnAnterior) {
      btnAnterior.disabled = (ordemAtual <= 1);
      btnAnterior.style.opacity = (ordemAtual <= 1) ? '0.5' : '1';
    }
    if (btnProxima) {
      btnProxima.disabled = (ordemAtual >= totalQuestoes);
      btnProxima.style.opacity = (ordemAtual >= totalQuestoes) ? '0.5' : '1';
    }

    atualizarMapaVisual();
  }

  function onAlternativaSelecionada(questaoId, letra) {
    if (!respostas[String(questaoId)]) {
      respostas[String(questaoId)] = {};
    }
    respostas[String(questaoId)].alternativa_marcada = letra;

    // Atualiza classes visuais das alternativas
    const labels = listaAlternativas.querySelectorAll('label');
    labels.forEach(lbl => {
      const radio = lbl.querySelector('input[type="radio"]');
      if (radio && radio.value === letra) {
        lbl.classList.add('selected');
        lbl.style.border = '1.5px solid var(--color-border)';
        lbl.style.backgroundColor = '#ececec';
      } else {
        lbl.classList.remove('selected');
        lbl.style.border = '1.5px solid #555555';
        lbl.style.backgroundColor = '#ffffff';
      }
    });

    atualizarMapaVisual();
    salvarResposta(questaoId, { alternativa_marcada: letra });
  }

  function onTextoDiscursivoModificado() {
    const q = questoes.find(item => item.ordem === ordemAtual);
    if (!q) return;

    const texto = discursivaTexto ? discursivaTexto.value : '';
    if (!respostas[String(q.id)]) {
      respostas[String(q.id)] = {};
    }
    respostas[String(q.id)].texto_resposta = texto;

    atualizarMapaVisual();

    if (debounceTimeout) clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      salvarResposta(q.id, { texto_resposta: texto });
    }, 500);
  }

  function limparRespostaAtual() {
    const q = questoes.find(item => item.ordem === ordemAtual);
    if (!q) return;

    if (q.tipo === 'objetiva') {
      const radios = listaAlternativas.querySelectorAll('input[type="radio"]');
      radios.forEach(r => r.checked = false);
      const labels = listaAlternativas.querySelectorAll('label');
      labels.forEach(lbl => {
        lbl.classList.remove('selected');
        lbl.style.border = '1.5px solid #555555';
        lbl.style.backgroundColor = '#ffffff';
      });
      if (respostas[String(q.id)]) {
        respostas[String(q.id)].alternativa_marcada = null;
      }
      salvarResposta(q.id, { alternativa_marcada: null });
    } else {
      if (discursivaTexto) discursivaTexto.value = '';
      if (respostas[String(q.id)]) {
        respostas[String(q.id)].texto_resposta = null;
      }
      salvarResposta(q.id, { texto_resposta: null });
    }

    atualizarMapaVisual();
  }

  // Atualiza mapa de questões e contadores
  function atualizarMapaVisual() {
    let respondidasCount = 0;
    const emBrancoList = [];

    questoes.forEach(q => {
      const resp = respostas[String(q.id)];
      let respondida = false;
      if (resp) {
        if (q.tipo === 'objetiva' && resp.alternativa_marcada) {
          respondida = true;
        } else if (q.tipo === 'discursiva' && resp.texto_resposta && resp.texto_resposta.trim()) {
          respondida = true;
        }
      }

      if (respondida) {
        respondidasCount++;
      } else {
        emBrancoList.push(q.ordem);
      }

      const cell = document.getElementById(`cell-${q.ordem}`);
      if (cell) {
        cell.className = 'mapa-cell';
        if (respondida) cell.classList.add('answered');
        if (q.ordem === ordemAtual) cell.classList.add('current');
        cell.setAttribute('aria-label', `Questão ${q.ordem}${respondida ? ', respondida' : ', em branco'}${q.ordem === ordemAtual ? ', atual' : ''}`);
      }
    });

    if (mapaRespondidasCount) {
      mapaRespondidasCount.textContent = respondidasCount;
    }

    return { respondidasCount, emBrancoList };
  }

  // Navegação
  function irParaOrdem(novaOrdem) {
    if (novaOrdem < 1 || novaOrdem > totalQuestoes) return;
    ordemAtual = novaOrdem;
    renderizarQuestaoAtual();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Handlers dos botões
  if (btnAnterior) {
    btnAnterior.addEventListener('click', () => {
      if (ordemAtual > 1) irParaOrdem(ordemAtual - 1);
    });
  }

  if (btnProxima) {
    btnProxima.addEventListener('click', () => {
      if (ordemAtual < totalQuestoes) irParaOrdem(ordemAtual + 1);
    });
  }

  if (btnLimpar) {
    btnLimpar.addEventListener('click', limparRespostaAtual);
  }

  if (discursivaTexto) {
    discursivaTexto.addEventListener('input', onTextoDiscursivoModificado);
  }

  // Clique em células do mapa lateral
  const asideMapa = document.getElementById('aside-mapa');
  const mapaBackdrop = document.getElementById('mapa-backdrop');
  const btnAbrirMapa = document.getElementById('btn-abrir-mapa');
  const btnFecharMapa = document.getElementById('btn-fechar-mapa');
  const btnAbrirModalMapa = document.getElementById('btn-abrir-modal-entrega-mapa');

  function abrirMapaMobile() {
    if (!asideMapa) return;
    asideMapa.classList.add('is-open');
    if (mapaBackdrop) mapaBackdrop.classList.add('is-open');
    document.body.classList.add('modal-open');
    if (btnAbrirMapa) btnAbrirMapa.setAttribute('aria-expanded', 'true');
    const firstBtn = asideMapa.querySelector('button, a');
    if (firstBtn) firstBtn.focus();
  }

  function fecharMapaMobile(devolverFoco = true) {
    if (!asideMapa || !asideMapa.classList.contains('is-open')) return;
    asideMapa.classList.remove('is-open');
    if (mapaBackdrop) mapaBackdrop.classList.remove('is-open');
    document.body.classList.remove('modal-open');
    if (btnAbrirMapa) {
      btnAbrirMapa.setAttribute('aria-expanded', 'false');
      if (devolverFoco) btnAbrirMapa.focus();
    }
  }

  if (btnAbrirMapa) btnAbrirMapa.addEventListener('click', abrirMapaMobile);
  if (btnFecharMapa) btnFecharMapa.addEventListener('click', () => fecharMapaMobile(true));
  if (mapaBackdrop) mapaBackdrop.addEventListener('click', () => fecharMapaMobile(true));

  document.addEventListener('keydown', (e) => {
    if (!asideMapa || !asideMapa.classList.contains('is-open')) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      fecharMapaMobile(true);
      return;
    }
    if (e.key === 'Tab') {
      const focusables = Array.from(
        asideMapa.querySelectorAll('a[href], button:not([disabled])')
      ).filter(el => el.offsetParent !== null);
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });

  if (mapaGrade) {
    mapaGrade.addEventListener('click', (e) => {
      const cell = e.target.closest('.mapa-cell');
      if (cell) {
        const ordem = parseInt(cell.getAttribute('data-ordem'), 10);
        if (ordem) {
          irParaOrdem(ordem);
          fecharMapaMobile(false);
        }
      }
    });
  }

  if (btnAbrirModalMapa) {
    btnAbrirModalMapa.addEventListener('click', () => {
      fecharMapaMobile(false);
      abrirModalEntrega();
    });
  }

  // Modal de Entrega (T10)
  function abrirModalEntrega() {
    const { respondidasCount, emBrancoList } = atualizarMapaVisual();

    if (modalRespondidas) {
      modalRespondidas.textContent = `${respondidasCount} de ${totalQuestoes}`;
    }
    if (modalTempoRestante) {
      modalTempoRestante.textContent = formatarTempoHorasMin(tempoRestante);
    }
    if (modalEmBrancoCount) {
      modalEmBrancoCount.textContent = emBrancoList.length;
    }

    if (modalEmBrancoGrade) {
      modalEmBrancoGrade.innerHTML = '';
      if (emBrancoList.length === 0) {
        if (modalEmBrancoContainer) {
          modalEmBrancoContainer.style.display = 'none';
        }
      } else {
        if (modalEmBrancoContainer) {
          modalEmBrancoContainer.style.display = 'flex';
        }
        emBrancoList.forEach(num => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'btn btn-secondary';
          btn.style.minWidth = '48px';
          btn.style.minHeight = '38px';
          btn.style.padding = '0 10px';
          btn.style.fontSize = '0.875rem';
          btn.textContent = num;
          btn.addEventListener('click', () => {
            modalEntrega.close();
            irParaOrdem(num);
          });
          modalEmBrancoGrade.appendChild(btn);
        });
      }
    }

    if (modalEntrega && typeof modalEntrega.showModal === 'function') {
      modalEntrega.showModal();
    }
  }

  if (btnAbrirModal) {
    btnAbrirModal.addEventListener('click', abrirModalEntrega);
  }

  if (btnModalVoltar && modalEntrega) {
    btnModalVoltar.addEventListener('click', () => {
      modalEntrega.close();
    });
  }

  if (btnModalConfirmar) {
    btnModalConfirmar.addEventListener('click', () => {
      finalizarSimulado('entrega');
    });
  }

  // Tratar clique em botões de "ir para questão" já renderizados no HTML
  if (modalEntrega) {
    modalEntrega.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-goto-questao');
      if (btn) {
        const ordem = parseInt(btn.getAttribute('data-ordem'), 10);
        if (ordem) {
          modalEntrega.close();
          irParaOrdem(ordem);
        }
      }
    });
  }

  // Evento de rede (quando a conexão volta)
  window.addEventListener('online', () => {
    processarFilaOffline();
    if (textoStatusSalvamento) {
      textoStatusSalvamento.textContent = 'Conexão restabelecida. Salvando pendências…';
    }
  });

  // Inicialização
  carregarDadosSimulado();
});
