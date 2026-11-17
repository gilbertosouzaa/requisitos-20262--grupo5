/**
 * Apoio ENADE - Gestão de Questões no Admin (T13)
 * Vanilla JavaScript puro sem frameworks.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --------------------------------------------------------------------------
  // 1. Controle dos menus Dropdown (...)
  // --------------------------------------------------------------------------
  const dropdownWrappers = document.querySelectorAll('.dropdown-wrapper');

  function fecharTodosDropdowns() {
    dropdownWrappers.forEach(w => {
      const menu = w.querySelector('.dropdown-menu');
      const btn = w.querySelector('.btn-dropdown-toggle');
      if (menu) menu.classList.remove('show');
      if (btn) btn.setAttribute('aria-expanded', 'false');
    });
  }

  dropdownWrappers.forEach(wrapper => {
    const btn = wrapper.querySelector('.btn-dropdown-toggle');
    const menu = wrapper.querySelector('.dropdown-menu');

    if (btn && menu) {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const estaAberto = menu.classList.contains('show');
        fecharTodosDropdowns();
        if (!estaAberto) {
          menu.classList.add('show');
          btn.setAttribute('aria-expanded', 'true');
        }
      });
    }
  });

  // Fecha dropdown ao clicar fora
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown-wrapper')) {
      fecharTodosDropdowns();
    }
  });

  // Fecha dropdown ao teclar Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      fecharTodosDropdowns();
      if (modalRemover && modalRemover.open) {
        modalRemover.close();
      }
    }
  });

  // --------------------------------------------------------------------------
  // 2. Modal Nativo <dialog> para Exclusão / Anulação de Questões
  // --------------------------------------------------------------------------
  const modalRemover = document.getElementById('dialog-remover');
  const conteudoModal = document.getElementById('dialog-remover-conteudo');
  const acoesModal = document.getElementById('dialog-remover-acoes');
  const btnFecharModal = document.getElementById('btn-fechar-dialog');
  const btnCancelarRemover = document.getElementById('btn-cancelar-remover');
  const formRemoverAcao = document.getElementById('form-remover-acao');
  const formAnularModal = document.getElementById('form-anular-modal');

  if (btnFecharModal && modalRemover) {
    btnFecharModal.addEventListener('click', () => modalRemover.close());
  }

  if (btnCancelarRemover && modalRemover) {
    btnCancelarRemover.addEventListener('click', () => modalRemover.close());
  }

  // Fecha se clicar no backdrop nativo do dialog
  if (modalRemover) {
    modalRemover.addEventListener('click', (e) => {
      const rect = modalRemover.getBoundingClientRect();
      const clicouFora = (
        e.clientX < rect.left ||
        e.clientX > rect.right ||
        e.clientY < rect.top ||
        e.clientY > rect.bottom
      );
      if (clicouFora) {
        modalRemover.close();
      }
    });
  }

  const botoesRemover = document.querySelectorAll('.btn-abrir-remover');

  botoesRemover.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      fecharTodosDropdowns();

      const qId = btn.getAttribute('data-id');
      const qNum = btn.getAttribute('data-numero');
      const qAno = btn.getAttribute('data-ano');
      const qAnulada = btn.getAttribute('data-anulada') === '1';

      if (!modalRemover || !conteudoModal || !acoesModal) return;

      conteudoModal.innerHTML = `<div style="text-align: center; padding: 12px; color: var(--color-text-muted);">Verificando se a questão possui respostas associadas...</div>`;
      acoesModal.innerHTML = `<button type="button" class="btn btn-secondary" onclick="document.getElementById('dialog-remover').close()">Cancelar</button>`;

      modalRemover.showModal();

      try {
        const resp = await fetch(`/admin/questoes/verificar-respostas/${qId}`);
        const data = await resp.json();

        if (data.tem_respostas) {
          // Bloqueio de exclusão conforme requisito: orienta anulação
          conteudoModal.innerHTML = `
            <div style="border: 2px solid #ea868f; background: #fff5f5; padding: 16px; border-radius: 8px;">
              <p style="margin: 0 0 10px; font-weight: 700; color: #c5221f;">
                Não é possível remover esta questão!
              </p>
              <p style="margin: 0; color: var(--color-text);">
                Esta questão já foi respondida por estudantes (total de ${data.total_respostas} resposta(s) registrada(s)).
                Marque como anulada em vez de remover.
              </p>
            </div>
          `;

          let btnAnularHtml = '';
          if (!qAnulada) {
            btnAnularHtml = `
              <button type="button" class="btn btn-primary" id="btn-confirmar-anulacao-modal">
                Marcar como anulada
              </button>
            `;
          }

          acoesModal.innerHTML = `
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('dialog-remover').close()">Fechar</button>
            ${btnAnularHtml}
          `;

          const btnConfAnul = document.getElementById('btn-confirmar-anulacao-modal');
          if (btnConfAnul) {
            btnConfAnul.addEventListener('click', () => {
              formAnularModal.action = `/admin/questoes/${qId}/anular`;
              formAnularModal.submit();
            });
          }

        } else {
          // Questão sem respostas: permite exclusão definitiva
          conteudoModal.innerHTML = `
            <p style="margin: 0;">
              Tem certeza que deseja remover a <strong>questão ${qNum}</strong> do <strong>ENADE ${qAno}</strong>?
            </p>
            <p style="margin: 8px 0 0; color: var(--color-text-muted); font-size: 0.875rem;">
              Esta ação não pode ser desfeita. Todos os dados associados serão apagados permanentemente.
            </p>
          `;

          acoesModal.innerHTML = `
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('dialog-remover').close()">Cancelar</button>
            <button type="button" class="btn btn-danger" id="btn-confirmar-exclusao" style="background-color: #c5221f; color: #ffffff; border-color: #c5221f;">
              Remover definitivamente
            </button>
          `;

          const btnConfExc = document.getElementById('btn-confirmar-exclusao');
          if (btnConfExc) {
            btnConfExc.addEventListener('click', () => {
              formRemoverAcao.action = `/admin/questoes/${qId}/remover`;
              formRemoverAcao.submit();
            });
          }
        }

      } catch (err) {
        conteudoModal.innerHTML = `
          <div class="alert-box alert-danger">
            Erro ao verificar histórico da questão. Tente novamente mais tarde.
          </div>
        `;
      }
    });
  });
});
