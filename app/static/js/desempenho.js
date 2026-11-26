/**
 * desempenho.js
 * Lógica do painel de desempenho (T12)
 */

document.addEventListener('DOMContentLoaded', () => {
  const formFiltros = document.getElementById('form-filtros-desempenho');
  const selectOrigem = document.getElementById('origem');
  const selectComp = document.getElementById('componente');

  if (formFiltros && selectOrigem && selectComp) {
    const onChangeFiltro = () => formFiltros.submit();
    selectOrigem.addEventListener('change', onChangeFiltro);
    selectComp.addEventListener('change', onChangeFiltro);
  }

  // Troca de área no gráfico de evolução sem recarregar a página
  const formEvolucao = document.getElementById('form-evolucao-area');
  const selectEvolucaoArea = document.getElementById('evolucao_area');
  const containerEvolucao = document.getElementById('evolucao-conteudo');
  const btnAtualizar = document.getElementById('btn-atualizar-evolucao');

  if (formEvolucao && selectEvolucaoArea && containerEvolucao) {
    if (btnAtualizar) {
      btnAtualizar.style.display = 'none';
    }

    async function atualizarEvolucao() {
      const origemVal = selectOrigem ? selectOrigem.value : 'tudo';
      const compVal = selectComp ? selectComp.value : 'todos';
      const areaVal = selectEvolucaoArea.value;

      const params = new URLSearchParams({
        origem: origemVal,
        componente: compVal,
        evolucao_area: areaVal
      });

      try {
        containerEvolucao.setAttribute('aria-busy', 'true');
        const resp = await fetch(`/api/desempenho/evolucao?${params.toString()}`, {
          headers: { 'X-Requested-With': 'fetch' }
        });
        if (!resp.ok) {
          formEvolucao.submit();
          return;
        }
        const html = await resp.text();
        containerEvolucao.innerHTML = html;

        const novaUrl = `${window.location.pathname}?${params.toString()}${window.location.hash}`;
        window.history.replaceState({}, '', novaUrl);
      } catch (err) {
        formEvolucao.submit();
      } finally {
        containerEvolucao.removeAttribute('aria-busy');
      }
    }

    selectEvolucaoArea.addEventListener('change', atualizarEvolucao);
    formEvolucao.addEventListener('submit', (e) => {
      e.preventDefault();
      atualizarEvolucao();
    });
  }
});
