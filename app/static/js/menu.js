/**
 * menu.js
 * Menu responsivo acessível para o cabeçalho (RNF02 / RNF09)
 */
document.documentElement.classList.add('has-js');

document.addEventListener('DOMContentLoaded', () => {
  const btnMenu = document.getElementById('btn-menu-mobile');
  const painelMenu = document.getElementById('menu-navegacao-painel');
  if (!btnMenu || !painelMenu) return;

  function abrirMenu() {
    painelMenu.classList.add('is-open');
    btnMenu.setAttribute('aria-expanded', 'true');
    btnMenu.setAttribute('aria-label', 'Fechar menu');
    const primeiroLink = painelMenu.querySelector('a, button');
    if (primeiroLink) primeiroLink.focus();
  }

  function fecharMenu(devolverFoco = true) {
    if (!painelMenu.classList.contains('is-open')) return;
    painelMenu.classList.remove('is-open');
    btnMenu.setAttribute('aria-expanded', 'false');
    btnMenu.setAttribute('aria-label', 'Abrir menu');
    if (devolverFoco) btnMenu.focus();
  }

  btnMenu.addEventListener('click', () => {
    const aberto = painelMenu.classList.contains('is-open');
    if (aberto) {
      fecharMenu(true);
    } else {
      abrirMenu();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && painelMenu.classList.contains('is-open')) {
      e.preventDefault();
      fecharMenu(true);
    }
  });

  document.addEventListener('click', (e) => {
    if (
      painelMenu.classList.contains('is-open') &&
      !painelMenu.contains(e.target) &&
      !btnMenu.contains(e.target)
    ) {
      fecharMenu(false);
    }
  });
});
