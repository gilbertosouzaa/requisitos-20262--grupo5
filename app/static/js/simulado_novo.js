/**
 * simulado_novo.js
 * Lógica da tela T08: Montar simulado
 */

document.addEventListener('DOMContentLoaded', () => {
  const radioCompleto = document.getElementById('tipo-completo');
  const radioParcial = document.getElementById('tipo-parcial');
  const cardCompleto = document.getElementById('card-completo');
  const cardParcial = document.getElementById('card-parcial');
  const selectEdicao = document.getElementById('edicao');
  const textoAvisoAnuladas = document.getElementById('texto-aviso-anuladas');
  const displayQtdCompleto = document.getElementById('display-qtd-completo');
  const selectComp = document.getElementById('comp');
  const selectArea = document.getElementById('area');
  const inputQtd = document.getElementById('qtd');
  const tempoCalculado = document.getElementById('tempo-calculado');
  const resumoSimulado = document.getElementById('resumo-simulado');

  function formatarMinutos(totalMin) {
    const horas = Math.floor(totalMin / 60);
    const mins = totalMin % 60;
    if (horas > 0) {
      return `${horas}h${mins < 10 ? '0' : ''}${mins}`;
    }
    return `${mins}min`;
  }

  function atualizarEstadoCards() {
    if (radioCompleto.checked) {
      cardCompleto.classList.add('selected');
      cardParcial.classList.remove('selected');
    } else {
      cardParcial.classList.add('selected');
      cardCompleto.classList.remove('selected');
    }
    atualizarResumo();
  }

  function atualizarEdicao() {
    if (!selectEdicao) return;
    const opt = selectEdicao.options[selectEdicao.selectedIndex];
    if (!opt) return;

    const anuladas = parseInt(opt.getAttribute('data-anuladas') || '0', 10);
    const validas = parseInt(opt.getAttribute('data-validas') || '40', 10);

    if (displayQtdCompleto) {
      displayQtdCompleto.textContent = validas;
    }

    if (textoAvisoAnuladas) {
      if (anuladas > 0) {
        textoAvisoAnuladas.innerHTML = `Esta edição tem <strong>${anuladas} questões anuladas</strong> pelo INEP, que não fazem parte do simulado. O tempo continua 4h00.`;
      } else {
        textoAvisoAnuladas.textContent = 'Esta edição não possui questões anuladas. O tempo de prova é de 4h00.';
      }
    }

    atualizarResumo();
  }

  function atualizarTempoParcial() {
    if (!inputQtd) return;
    let qtd = parseInt(inputQtd.value, 10);
    if (isNaN(qtd) || qtd < 5) qtd = 5;
    if (qtd > 40) qtd = 40;

    const minutos = qtd * 6; // 6 minutos por questão (RN06)
    if (tempoCalculado) {
      tempoCalculado.textContent = formatarMinutos(minutos);
    }

    atualizarResumo();
  }

  function atualizarResumo() {
    if (!resumoSimulado) return;

    if (radioCompleto && radioCompleto.checked) {
      const opt = selectEdicao ? selectEdicao.options[selectEdicao.selectedIndex] : null;
      const ano = opt ? opt.value : '2023';
      const validas = opt ? (opt.getAttribute('data-validas') || '40') : '40';
      resumoSimulado.textContent = `Prova completa · ENADE ${ano} · ${validas} questões · 4h00`;
    } else {
      let qtd = inputQtd ? parseInt(inputQtd.value, 10) : 10;
      if (isNaN(qtd) || qtd < 5) qtd = 5;
      if (qtd > 40) qtd = 40;
      const tempoStr = formatarMinutos(qtd * 6);

      const compText = selectComp ? selectComp.options[selectComp.selectedIndex].text : 'Específico';
      const areaText = selectArea ? selectArea.options[selectArea.selectedIndex].text : 'Todas';

      let detalhe = compText;
      if (areaText !== 'Todas') {
        detalhe += ` (${areaText})`;
      }

      resumoSimulado.textContent = `Simulado parcial · ${detalhe} · ${qtd} questões · ${tempoStr}`;
    }
  }

  // Event Listeners
  if (radioCompleto) radioCompleto.addEventListener('change', atualizarEstadoCards);
  if (radioParcial) radioParcial.addEventListener('change', atualizarEstadoCards);
  if (cardCompleto) cardCompleto.addEventListener('click', (e) => {
    if (e.target.tagName !== 'SELECT' && e.target.tagName !== 'OPTION') {
      radioCompleto.checked = true;
      atualizarEstadoCards();
    }
  });
  if (cardParcial) cardParcial.addEventListener('click', (e) => {
    if (e.target.tagName !== 'SELECT' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'OPTION') {
      radioParcial.checked = true;
      atualizarEstadoCards();
    }
  });

  if (selectEdicao) selectEdicao.addEventListener('change', atualizarEdicao);
  if (inputQtd) {
    inputQtd.addEventListener('input', atualizarTempoParcial);
    inputQtd.addEventListener('change', atualizarTempoParcial);
  }
  if (selectComp) selectComp.addEventListener('change', atualizarResumo);
  if (selectArea) selectArea.addEventListener('change', atualizarResumo);

  // Inicialização
  atualizarEdicao();
  atualizarTempoParcial();
  atualizarEstadoCards();
});
