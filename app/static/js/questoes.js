// Apoio ENADE — JS para a Tela de Banco de Questões (T06)
document.addEventListener('DOMContentLoaded', function () {
  const formFiltros = document.getElementById('form-filtros');
  const cursoSelect = document.getElementById('curso');

  // Ao alterar o curso no desktop, submete para atualizar as opções e lista
  if (cursoSelect && formFiltros) {
    cursoSelect.addEventListener('change', function () {
      if (window.innerWidth > 767) {
        formFiltros.submit();
      }
    });
  }

  // Painel de filtros no celular (RNF02)
  const btnAbrir = document.getElementById('btn-abrir-filtros');
  const btnFechar = document.getElementById('btn-fechar-filtros');
  const painel = document.getElementById('painel-filtros');

  if (btnAbrir && painel) {
    function getFocusable() {
      return Array.from(
        painel.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled])')
      ).filter(el => el.offsetParent !== null);
    }

    function abrirPainel() {
      painel.classList.add('is-open');
      document.body.classList.add('modal-open');
      btnAbrir.setAttribute('aria-expanded', 'true');
      const focusables = getFocusable();
      if (focusables.length) focusables[0].focus();
    }

    function fecharPainel(devolverFoco = true) {
      if (!painel.classList.contains('is-open')) return;
      painel.classList.remove('is-open');
      document.body.classList.remove('modal-open');
      btnAbrir.setAttribute('aria-expanded', 'false');
      if (devolverFoco) btnAbrir.focus();
    }

    btnAbrir.addEventListener('click', abrirPainel);
    if (btnFechar) {
      btnFechar.addEventListener('click', () => fecharPainel(true));
    }

    document.addEventListener('keydown', function (e) {
      if (!painel.classList.contains('is-open')) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        fecharPainel(true);
        return;
      }
      if (e.key === 'Tab') {
        const focusables = getFocusable();
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
  }
});
