// Apoio ENADE — JS para a Tela de Questão em Modo Estudo (T07a e T07b)
document.addEventListener('DOMContentLoaded', function () {
  const artigoQuestao = document.getElementById('artigo-questao');
  if (!artigoQuestao) return;

  const questaoId = artigoQuestao.getAttribute('data-questao-id');
  const tipoQuestao = artigoQuestao.getAttribute('data-tipo');
  const autenticado = artigoQuestao.getAttribute('data-autenticado') === 'true';

  const formResponder = document.getElementById('form-responder');
  const btnConfirmar = document.getElementById('btn-confirmar');
  const btnConfirmarDisc = document.getElementById('btn-confirmar-disc');
  const radiosAlternativas = document.querySelectorAll('input[name="alternativa"]');
  const containerFaixa = document.getElementById('container-faixa-resultado');
  const wrapperEnunciado = document.getElementById('wrapper-enunciado');
  const acoesResponder = document.getElementById('acoes-responder');
  const acoesResponderDisc = document.getElementById('acoes-responder-disc');
  const blocoGabarito = document.getElementById('bloco-gabarito-comentado');
  const textareaResposta = document.getElementById('texto_resposta');

  // Obtém o token CSRF da meta tag ou input hidden
  function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.getAttribute('content')) {
      return metaTag.getAttribute('content');
    }
    const inputToken = document.querySelector('input[name="csrf_token"]');
    return inputToken ? inputToken.value : '';
  }

  // Interatividade de seleção de alternativas
  radiosAlternativas.forEach(function (radio) {
    radio.addEventListener('change', function () {
      // Remove a classe 'selected' de todos os labels
      document.querySelectorAll('.alt-choice').forEach(function (label) {
        label.classList.remove('selected');
      });

      // Adiciona 'selected' ao label selecionado
      const label = radio.closest('.alt-choice');
      if (label) {
        label.classList.add('selected');
      }

      // Habilita o botão Confirmar resposta se usuário autenticado
      if (btnConfirmar && autenticado) {
        btnConfirmar.disabled = false;
      }
    });
  });

  // Validação no cliente para textarea de discursiva
  if (textareaResposta && btnConfirmarDisc && autenticado) {
    textareaResposta.addEventListener('input', function () {
      btnConfirmarDisc.disabled = (this.value.trim().length === 0);
    });
  }

  // Submissão assíncrona (Fetch) da resposta
  if (formResponder) {
    formResponder.addEventListener('submit', function (e) {
      // Se não autenticado, deixa o link de login tratar ou redireciona
      if (!autenticado) {
        return;
      }

      e.preventDefault();

      let alternativaSelecionada = null;
      if (tipoQuestao === 'objetiva') {
        const checkedRadio = document.querySelector('input[name="alternativa"]:checked');
        if (!checkedRadio) {
          alert('Por favor, selecione uma alternativa.');
          return;
        }
        alternativaSelecionada = checkedRadio.value;
      } else {
        if (!textareaResposta || !textareaResposta.value.trim()) {
          alert('Por favor, digite sua resposta antes de enviar.');
          return;
        }
      }

      // Desabilita botão durante o envio
      const btnAtivo = tipoQuestao === 'objetiva' ? btnConfirmar : btnConfirmarDisc;
      const textoOriginal = btnAtivo.textContent;
      btnAtivo.disabled = true;
      btnAtivo.textContent = 'Enviando…';

      const payload = {
        alternativa: alternativaSelecionada,
        texto_resposta: textareaResposta ? textareaResposta.value.trim() : ''
      };

      fetch(`/api/questoes/${questaoId}/responder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
      })
      .then(function (res) {
        if (res.status === 401) {
          return res.json().then(function (data) {
            window.location.href = data.login_url || '/entrar';
          });
        }
        return res.json();
      })
      .then(function (data) {
        if (!data || !data.sucesso) {
          btnAtivo.disabled = false;
          btnAtivo.textContent = textoOriginal;
          alert((data && data.erro) || 'Ocorreu um erro ao enviar sua resposta.');
          return;
        }

        // Sucesso: Transforma a tela em T07b Correção sem recarregar
        renderizarCorrecao(data);
      })
      .catch(function (err) {
        console.error('Erro na requisição:', err);
        btnAtivo.disabled = false;
        btnAtivo.textContent = textoOriginal;
        alert('Erro de conexão ao enviar a resposta. Tente novamente.');
      });
    });
  }

  function renderizarCorrecao(data) {
    // 1. Renderiza a faixa de resultado
    let faixaHtml = '';
    if (data.tipo === 'objetiva') {
      if (data.acertou) {
        faixaHtml = `
          <div class="result-banner" role="status" tabindex="-1">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M20 6L9 17l-5-5"></path>
            </svg>
            <div>
              <strong style="font-size: 1.15rem;">Você acertou!</strong>
              <div class="text-muted" style="font-size: 0.9rem;">Alternativa correta: <strong>${data.gabarito_oficial}</strong></div>
            </div>
          </div>
        `;
      } else {
        faixaHtml = `
          <div class="result-banner" role="status" tabindex="-1">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
            <div>
              <strong style="font-size: 1.15rem;">Você errou.</strong>
              <span style="font-size: 0.95rem; margin-left: 6px;">
                Sua resposta: <strong>${data.alternativa_marcada || '—'}</strong> · Alternativa correta: <strong>${data.gabarito_oficial}</strong>
              </span>
            </div>
          </div>
        `;
      }
    } else {
      faixaHtml = `
        <div class="result-banner" role="status" tabindex="-1">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          <div>
            <strong style="font-size: 1.1rem;">Resposta enviada!</strong>
            <div class="text-muted" style="font-size: 0.9rem;">Compare sua resposta com o padrão oficial divulgado pelo INEP para fazer sua autoavaliação.</div>
          </div>
        </div>
      `;
    }

    containerFaixa.innerHTML = faixaHtml;
    containerFaixa.style.display = 'block';

    // 2. Recolhe o enunciado em <details>
    const enunciadoDireto = document.getElementById('enunciado-direto');
    if (enunciadoDireto) {
      const conteudoEnunciado = enunciadoDireto.innerHTML;
      wrapperEnunciado.innerHTML = `
        <details class="details-box" id="details-enunciado">
          <summary>Ver enunciado</summary>
          <div style="margin-top: 14px; font-size: 1.05rem; line-height: 1.6;">
            ${conteudoEnunciado}
          </div>
        </details>
      `;
    }

    // 3. Atualiza estado das alternativas (se objetiva)
    if (data.tipo === 'objetiva') {
      radiosAlternativas.forEach(function (radio) {
        radio.disabled = true;
        const label = radio.closest('.alt-choice');
        const letra = radio.value;
        label.classList.add('disabled');
        label.classList.remove('selected');

        if (letra === data.gabarito_oficial) {
          label.classList.add('correct-alt');
          if (!label.querySelector('.alt-marker')) {
            const marker = document.createElement('span');
            marker.className = 'alt-marker';
            marker.style.color = '#116327';
            marker.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"></path></svg> Correta';
            label.appendChild(marker);
          }
        } else if (letra === data.alternativa_marcada && !data.acertou) {
          label.classList.add('user-wrong-alt');
          if (!label.querySelector('.alt-marker')) {
            const marker = document.createElement('span');
            marker.className = 'alt-marker';
            marker.style.color = '#900000';
            marker.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> Sua resposta';
            label.appendChild(marker);
          }
        } else {
          label.classList.add('other-alt');
        }
      });
    } else if (textareaResposta) {
      textareaResposta.disabled = true;
    }

    // 4. Oculta os botões de ação anteriores
    if (acoesResponder) acoesResponder.style.display = 'none';
    if (acoesResponderDisc) acoesResponderDisc.style.display = 'none';

    // 5. Constrói o bloco de gabarito comentado
    let gabaritoHtml = '';
    if (data.tipo === 'discursiva') {
      gabaritoHtml = `
        <section class="gabarito-card" style="background-color: #fafafa;">
          <h2 style="font-size: 1.25rem; margin: 0;">Padrão de resposta esperado (INEP)</h2>
          <div style="font-size: 0.95rem; line-height: 1.6; white-space: pre-line;">${data.padrao_resposta || ''}</div>
        </section>
      `;
    } else {
      if (data.comentario_em_elaboracao) {
        gabaritoHtml = `
          <section class="gabarito-card">
            <h2 style="font-size: 1.25rem; margin: 0;">Gabarito comentado</h2>
            <div class="alert-box" style="margin: 0;">
              <svg class="alert-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <div>
                Comentário em elaboração. Enquanto isso, veja a <a href="${data.discussao_url}">discussão desta questão</a>.
              </div>
            </div>
          </section>
        `;
      } else {
        let errosHtml = '';
        if (data.comentarios_erro) {
          for (let l in data.comentarios_erro) {
            if (l !== data.gabarito_oficial && data.comentarios_erro[l]) {
              errosHtml += `<span style="font-size: 0.95rem; line-height: 1.45;"><strong>${l}</strong> — ${data.comentarios_erro[l]}</span>`;
            }
          }
        }

        gabaritoHtml = `
          <section class="gabarito-card">
            <h2 style="font-size: 1.25rem; margin: 0;">Gabarito comentado</h2>
            <div>
              <p style="margin: 0; line-height: 1.5;">
                <strong>Por que a ${data.gabarito_oficial} está correta:</strong> ${data.comentario_correta || ''}
              </p>
            </div>
            ${errosHtml ? `<div style="display: flex; flex-direction: column; gap: 6px; margin-top: 8px;"><strong>Por que as outras estão erradas:</strong>${errosHtml}</div>` : ''}
          </section>
        `;
      }
    }

    // Adiciona os botões de próxima questão / voltar
    const btnProximaHtml = document.getElementById('btn-proxima')
      ? document.getElementById('btn-proxima').outerHTML
      : '';
    const btnVoltarHtml = document.getElementById('btn-voltar-banco')
      ? document.getElementById('btn-voltar-banco').outerHTML
      : `<a class="btn btn-secondary" href="/questoes">Voltar ao banco</a>`;

    blocoGabarito.innerHTML = `
      ${gabaritoHtml}
      <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 4px;">
        ${btnProximaHtml}
        ${btnVoltarHtml}
      </div>
    `;
    blocoGabarito.style.display = 'flex';

    // Foco na faixa de resultado para WCAG AA
    const faixaEl = containerFaixa.querySelector('.result-banner');
    if (faixaEl) {
      faixaEl.focus();
    }
  }
});
