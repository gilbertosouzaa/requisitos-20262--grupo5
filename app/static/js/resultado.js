/**
 * resultado.js
 * Lógica da tela T11: Resultado do Simulado
 */

document.addEventListener('DOMContentLoaded', () => {
  const filtroSelect = document.getElementById('filtro-tabela');
  const tabela = document.getElementById('tabela-correcao');
  const resumoLinhas = document.getElementById('resumo-linhas-visiveis');

  if (!filtroSelect || !tabela) return;

  function aplicarFiltro() {
    const valor = filtroSelect.value;
    const linhas = tabela.querySelectorAll('tbody tr.linha-questao');
    let visiveis = 0;

    linhas.forEach(linha => {
      const sit = linha.getAttribute('data-situacao');
      let mostrar = false;

      if (valor === 'todas') {
        mostrar = true;
      } else if (valor === 'erros') {
        mostrar = (sit === 'errou');
      } else if (valor === 'em_branco') {
        mostrar = (sit === 'em_branco');
      }

      if (mostrar) {
        linha.style.display = '';
        visiveis++;
      } else {
        linha.style.display = 'none';
      }
    });

    if (resumoLinhas) {
      resumoLinhas.textContent = `Mostrando ${visiveis} de ${linhas.length} questões`;
    }
  }

  filtroSelect.addEventListener('change', aplicarFiltro);
  aplicarFiltro();
});
