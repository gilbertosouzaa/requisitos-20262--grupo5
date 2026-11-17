// Apoio ENADE — JS para a Tela de Banco de Questões (T06)
document.addEventListener('DOMContentLoaded', function () {
  const formFiltros = document.getElementById('form-filtros');
  const cursoSelect = document.getElementById('curso');

  // Ao alterar o curso, submete para atualizar as opções e lista
  if (cursoSelect && formFiltros) {
    cursoSelect.addEventListener('change', function () {
      formFiltros.submit();
    });
  }
});
