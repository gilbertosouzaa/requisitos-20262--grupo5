/**
 * desempenho.js
 * Lógica do painel de desempenho (T12)
 */

document.addEventListener('DOMContentLoaded', () => {
  const formFiltros = document.getElementById('form-filtros-desempenho');
  const selectOrigem = document.getElementById('origem');
  const selectComp = document.getElementById('componente');

  if (!formFiltros || !selectOrigem || !selectComp) return;

  function onChangeFiltro() {
    formFiltros.submit();
  }

  selectOrigem.addEventListener('change', onChangeFiltro);
  selectComp.addEventListener('change', onChangeFiltro);
});
