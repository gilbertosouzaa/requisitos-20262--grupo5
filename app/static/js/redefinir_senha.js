// Apoio ENADE — JS para Redefinir Senha (T04)
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('form-redefinir');
  const novaSenhaInput = document.getElementById('nova_senha');
  const confirmaSenhaInput = document.getElementById('confirma_senha');
  const confirmaErro = document.getElementById('confirma-cliente-erro');

  if (novaSenhaInput) {
    novaSenhaInput.focus();
  }

  if (form) {
    form.addEventListener('submit', function (e) {
      let valido = true;

      if (!novaSenhaInput.value || novaSenhaInput.value.length < 8) {
        valido = false;
        novaSenhaInput.classList.add('is-invalid');
      } else {
        novaSenhaInput.classList.remove('is-invalid');
      }

      if (novaSenhaInput.value !== confirmaSenhaInput.value) {
        valido = false;
        confirmaSenhaInput.classList.add('is-invalid');
        confirmaErro.textContent = 'As senhas digitadas não coincidem.';
        confirmaErro.style.display = 'flex';
      } else {
        confirmaSenhaInput.classList.remove('is-invalid');
        confirmaErro.textContent = '';
        confirmaErro.style.display = 'none';
      }

      if (!valido) {
        e.preventDefault();
        const primeiroInvalido = form.querySelector('.is-invalid');
        if (primeiroInvalido) {
          primeiroInvalido.focus();
        }
      }
    });
  }
});
