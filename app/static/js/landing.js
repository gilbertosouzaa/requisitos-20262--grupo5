// Apoio ENADE — JS para a Landing Page (T01)
document.addEventListener('DOMContentLoaded', function () {
  // Rolagem suave para a âncora #como-funciona
  const comoFuncionaLink = document.querySelector('a[href*="#como-funciona"]');
  if (comoFuncionaLink) {
    comoFuncionaLink.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href').split('#')[1];
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth' });
        targetEl.setAttribute('tabindex', '-1');
        targetEl.focus();
      }
    });
  }
});
