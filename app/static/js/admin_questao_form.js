/**
 * Apoio ENADE - Formulário de Questão Admin (T14)
 * Validação RN02 em tempo real, alternância de tipo e preview de mídia.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('form-questao');
  if (!form) return;

  // --------------------------------------------------------------------------
  // 1. Áreas de Conhecimento por Componente
  // --------------------------------------------------------------------------
  const radioCompFG = document.getElementById('campo-componente-fg');
  const radioCompEsp = document.getElementById('campo-componente-esp');
  const dataListAreas = document.getElementById('lista-areas-sugestoes');

  const areasPorComponente = {
    formacao_geral: [
      'Interpretação de texto',
      'Sociodiversidade e Multiculturalismo',
      'Biodiversidade',
      'Globalização e Política',
      'Cidadania e Direitos Humanos',
      'Tecnologia e Sociedade'
    ],
    especifico: [
      'Algoritmos e Estrutura de Dados',
      'Arquitetura e Redes de Computadores',
      'Banco de Dados',
      'Engenharia de Software',
      'Inteligência Artificial',
      'Teoria da Computação',
      'Sistemas Operacionais',
      'Segurança da Informação',
      'Compiladores e Linguagens de Programação',
      'Interação Humano-Computador'
    ]
  };

  const inputCurso = document.getElementById('campo-curso_id');
  const labelCursoObrigatorio = document.getElementById('label-curso-obrigatorio');
  const ajudaCurso = document.getElementById('ajuda-curso');

  function atualizarComponenteCurso() {
    const isFG = radioCompFG && radioCompFG.checked;
    if (inputCurso) {
      if (isFG) {
        inputCurso.disabled = true;
        inputCurso.value = "";
        inputCurso.removeAttribute('required');
      } else {
        inputCurso.disabled = false;
        inputCurso.setAttribute('required', 'required');
      }
    }
    if (labelCursoObrigatorio) {
      labelCursoObrigatorio.style.display = isFG ? 'none' : 'inline';
    }
    if (ajudaCurso) {
      ajudaCurso.textContent = isFG ? 'Questões de Formação Geral valem para todos os cursos.' : 'Obrigatório para o Componente Específico.';
    }
  }

  function atualizarSugestoesAreas() {
    if (!dataListAreas) return;
    const comp = radioCompFG && radioCompFG.checked ? 'formacao_geral' : 'especifico';
    const lista = areasPorComponente[comp] || [];

    dataListAreas.innerHTML = '';
    lista.forEach(area => {
      const opt = document.createElement('option');
      opt.value = area;
      dataListAreas.appendChild(opt);
    });
  }

  if (radioCompFG) radioCompFG.addEventListener('change', () => { atualizarComponenteCurso(); atualizarSugestoesAreas(); atualizarChecklist(); });
  if (radioCompEsp) radioCompEsp.addEventListener('change', () => { atualizarComponenteCurso(); atualizarSugestoesAreas(); atualizarChecklist(); });
  atualizarComponenteCurso();
  atualizarSugestoesAreas();

  // --------------------------------------------------------------------------
  // 2. Alternância entre Questão Objetiva e Discursiva
  // --------------------------------------------------------------------------
  const radioObjetiva = document.getElementById('campo-tipo-objetiva');
  const radioDiscursiva = document.getElementById('campo-tipo-discursiva');
  const secaoObjetiva = document.getElementById('secao-objetiva');
  const secaoDiscursiva = document.getElementById('secao-discursiva');

  function atualizarVisibilidadeTipo() {
    if (!secaoObjetiva || !secaoDiscursiva) return;

    if (radioDiscursiva && radioDiscursiva.checked) {
      secaoObjetiva.style.display = 'none';
      secaoDiscursiva.style.display = 'flex';
    } else {
      secaoObjetiva.style.display = 'flex';
      secaoDiscursiva.style.display = 'none';
    }
  }

  if (radioObjetiva) radioObjetiva.addEventListener('change', () => { atualizarVisibilidadeTipo(); atualizarChecklist(); });
  if (radioDiscursiva) radioDiscursiva.addEventListener('change', () => { atualizarVisibilidadeTipo(); atualizarChecklist(); });
  atualizarVisibilidadeTipo();

  // --------------------------------------------------------------------------
  // 3. Pré-visualização de Imagem
  // --------------------------------------------------------------------------
  const inputImagem = document.getElementById('campo-imagem');
  const previewContainer = document.getElementById('imagem-preview-container');
  const previewImg = document.getElementById('imagem-preview-elemento');

  if (inputImagem && previewContainer && previewImg) {
    inputImagem.addEventListener('change', () => {
      const file = inputImagem.files[0];
      if (file) {
        if (file.size > 2 * 1024 * 1024) {
          alert('Atenção: A imagem selecionada ultrapassa o tamanho máximo permitido de 2MB.');
          inputImagem.value = '';
          previewContainer.style.display = 'none';
          return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
          previewImg.src = e.target.result;
          previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
      } else {
        previewContainer.style.display = 'none';
      }
    });
  }

  // --------------------------------------------------------------------------
  // 4. Checklist RN02 em Tempo Real
  // --------------------------------------------------------------------------
  const chkAno = document.getElementById('chk-ano');
  const chkCurso = document.getElementById('chk-curso');
  const chkNumero = document.getElementById('chk-numero');
  const chkCompArea = document.getElementById('chk-componente-area');
  const chkEnunciado = document.getElementById('chk-enunciado');
  const chkRespostas = document.getElementById('chk-respostas');

  function setItemStatus(el, valido) {
    if (!el) return;
    const statusSpan = el.querySelector('.chk-status');
    if (valido) {
      el.classList.add('valid');
      if (statusSpan) statusSpan.textContent = '✓';
    } else {
      el.classList.remove('valid');
      if (statusSpan) statusSpan.textContent = '○';
    }
  }

  function atualizarChecklist() {
    const inputAno = document.getElementById('campo-ano');
    const inputCurso = document.getElementById('campo-curso_id');
    const inputNum = document.getElementById('campo-numero');
    const inputArea = document.getElementById('campo-area');
    const inputEnunciado = document.getElementById('campo-enunciado');

    // 1. Ano
    const anoVal = inputAno ? parseInt(inputAno.value, 10) : 0;
    setItemStatus(chkAno, anoVal >= 1990 && anoVal <= 2100);

    // 2. Curso (RN02: obrigatório só para o Componente Específico)
    const isFG = radioCompFG && radioCompFG.checked;
    if (isFG) {
      setItemStatus(chkCurso, true);
    } else {
      setItemStatus(chkCurso, inputCurso && Boolean(inputCurso.value));
    }

    // 3. Número
    const numVal = inputNum ? parseInt(inputNum.value, 10) : 0;
    setItemStatus(chkNumero, numVal > 0);

    // 4. Componente e Área
    const temComp = (radioCompFG && radioCompFG.checked) || (radioCompEsp && radioCompEsp.checked);
    const temArea = inputArea && Boolean(inputArea.value.trim());
    setItemStatus(chkCompArea, temComp && temArea);

    // 5. Enunciado
    setItemStatus(chkEnunciado, inputEnunciado && Boolean(inputEnunciado.value.trim()));

    // 6. Respostas / Gabarito
    let respostasValidas = false;
    if (radioDiscursiva && radioDiscursiva.checked) {
      const inputPadrao = document.getElementById('campo-padrao_resposta');
      respostasValidas = Boolean(inputPadrao && inputPadrao.value.trim());
    } else {
      const gabaritoMarcado = document.querySelector('input[name="gabarito_oficial"]:checked');
      const alts = ['A', 'B', 'C', 'D', 'E'];
      let todasAltsPreenchidas = true;
      alts.forEach(letra => {
        const altInput = document.getElementById(`campo-alt_${letra}`);
        if (!altInput || !altInput.value.trim()) {
          todasAltsPreenchidas = false;
        }
      });
      respostasValidas = Boolean(gabaritoMarcado) && todasAltsPreenchidas;
    }
    setItemStatus(chkRespostas, respostasValidas);
  }

  // Ouve mudanças nos inputs do formulário
  form.addEventListener('input', atualizarChecklist);
  form.addEventListener('change', atualizarChecklist);

  // Executa checagem inicial
  atualizarChecklist();
});
