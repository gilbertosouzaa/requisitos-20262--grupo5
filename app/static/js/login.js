// Apoio ENADE — JS para a tela de Login (T02)
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('form-login');
  const emailInput = document.getElementById('email');
  const senhaInput = document.getElementById('senha');
  const alertaErro = document.getElementById('login-alerta-erro');

  // Foco no primeiro campo com erro ou no email
  if (alertaErro) {
    alertaErro.focus();
  } else if (emailInput && !emailInput.value) {
    emailInput.focus();
  }

  // Validação simples pré-envio no cliente para feedback imediato
  if (form) {
    form.addEventListener('submit', function (e) {
      let valido = true;

      if (!emailInput.value.trim()) {
        valido = false;
        emailInput.classList.add('is-invalid');
      } else {
        emailInput.classList.remove('is-invalid');
      }

      if (!senhaInput.value) {
        valido = false;
        senhaInput.classList.add('is-invalid');
      } else {
        senhaInput.classList.remove('is-invalid');
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
