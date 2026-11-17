// Apoio ENADE — JS para a tela de Cadastro (T03)
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('form-cadastro');
  const nomeInput = document.getElementById('nome');
  const emailInput = document.getElementById('email');
  const senhaInput = document.getElementById('senha');
  const cursoSelect = document.getElementById('curso_id');
  const termosCheck = document.getElementById('termos');
  const senhaErro = document.getElementById('senha-cliente-erro');
  const termosErro = document.getElementById('termos-cliente-erro');

  // Foco inicial
  if (emailInput && emailInput.classList.contains('is-invalid')) {
    emailInput.focus();
  } else if (nomeInput && !nomeInput.value) {
    nomeInput.focus();
  }

  // Feedback em tempo real no campo de senha
  if (senhaInput) {
    senhaInput.addEventListener('input', function () {
      if (this.value.length > 0 && this.value.length < 8) {
        senhaErro.textContent = 'A senha precisa ter no mínimo 8 caracteres.';
        senhaErro.style.display = 'flex';
        this.classList.add('is-invalid');
      } else {
        senhaErro.textContent = '';
        senhaErro.style.display = 'none';
        this.classList.remove('is-invalid');
      }
    });
  }

  // Validação no envio
  if (form) {
    form.addEventListener('submit', function (e) {
      let valido = true;

      // Nome
      if (!nomeInput.value.trim()) {
        valido = false;
        nomeInput.classList.add('is-invalid');
      } else {
        nomeInput.classList.remove('is-invalid');
      }

      // E-mail
      if (!emailInput.value.trim()) {
        valido = false;
        emailInput.classList.add('is-invalid');
      }

      // Senha
      if (!senhaInput.value || senhaInput.value.length < 8) {
        valido = false;
        senhaInput.classList.add('is-invalid');
        senhaErro.textContent = 'A senha precisa ter no mínimo 8 caracteres.';
        senhaErro.style.display = 'flex';
      }

      // Curso
      if (!cursoSelect.value) {
        valido = false;
        cursoSelect.classList.add('is-invalid');
      } else {
        cursoSelect.classList.remove('is-invalid');
      }

      // Termos
      if (!termosCheck.checked) {
        valido = false;
        termosErro.textContent = 'Você deve aceitar a Política de Privacidade e os Termos de Uso.';
        termosErro.style.display = 'flex';
      } else {
        termosErro.textContent = '';
        termosErro.style.display = 'none';
      }

      if (!valido) {
        e.preventDefault();
        const primeiroInvalido = form.querySelector('.is-invalid, #termos:not(:checked)');
        if (primeiroInvalido) {
          primeiroInvalido.focus();
        }
      }
    });
  }
});
