document.addEventListener('DOMContentLoaded', () => {
  const radios = document.querySelectorAll('input[name="perfil"]');
  const grupoAreas = document.getElementById('grupo-areas');

  function atualizarVisibilidade() {
    const selecionado = document.querySelector('input[name="perfil"]:checked');
    if (!selecionado || !grupoAreas) return;
    grupoAreas.style.display = selecionado.value === 'professor' ? 'block' : 'none';
  }

  radios.forEach((r) => r.addEventListener('change', atualizarVisibilidade));
  atualizarVisibilidade();
});
