document.addEventListener('DOMContentLoaded', () => {
  const formPerfil = document.getElementById('form-perfil');
  const secaoAreas = document.getElementById('secao-areas-professor');
  const radiosPerfil = document.querySelectorAll('#form-perfil input[name="perfil"]');

  const dialogAdmin = document.getElementById('dialog-promover-admin');
  const btnCancelarAdmin = document.getElementById('btn-cancelar-admin');
  const btnConfirmarAdmin = document.getElementById('btn-confirmar-admin');

  const btnAbrirDesativar = document.getElementById('btn-abrir-desativar');
  const dialogDesativar = document.getElementById('dialog-desativar-conta');
  const btnCancelarDesativar = document.getElementById('btn-cancelar-desativar');

  let confirmacaoAdminAceita = false;

  radiosPerfil.forEach((radio) => {
    radio.addEventListener('change', () => {
      if (secaoAreas) {
        secaoAreas.style.display = radio.value === 'professor' ? 'block' : 'none';
      }
    });
  });

  if (formPerfil && dialogAdmin) {
    formPerfil.addEventListener('submit', (e) => {
      const selecionado = document.querySelector('#form-perfil input[name="perfil"]:checked');
      const perfilAtual = formPerfil.dataset.perfilAtual;
      if (selecionado && selecionado.value === 'admin' && perfilAtual !== 'admin' && !confirmacaoAdminAceita) {
        e.preventDefault();
        dialogAdmin.showModal();
      }
    });

    if (btnCancelarAdmin) {
      btnCancelarAdmin.addEventListener('click', () => dialogAdmin.close());
    }
    if (btnConfirmarAdmin) {
      btnConfirmarAdmin.addEventListener('click', () => {
        confirmacaoAdminAceita = true;
        dialogAdmin.close();
        formPerfil.submit();
      });
    }
  }

  if (btnAbrirDesativar && dialogDesativar) {
    btnAbrirDesativar.addEventListener('click', () => dialogDesativar.showModal());
  }
  if (btnCancelarDesativar && dialogDesativar) {
    btnCancelarDesativar.addEventListener('click', () => dialogDesativar.close());
  }
});
