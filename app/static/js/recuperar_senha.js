// Apoio ENADE — JS para Recuperar Senha (T04)
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('form-recuperar');
  const emailInput = document.getElementById('email');

  if (emailInput) {
    emailInput.focus();
  }

  if (form) {
    form.addEventListener('submit', function (e) {
      if (!emailInput.value.trim()) {
        e.preventDefault();
        emailInput.classList.add('is-invalid');
        emailInput.focus();
      } else {
        emailInput.classList.remove('is-invalid');
      }
    });
  }
});
