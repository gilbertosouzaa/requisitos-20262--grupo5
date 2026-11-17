/**
 * Apoio ENADE - Editor de Comentário Admin (T15)
 * Atualização em tempo real da pré-visualização do estudante.
 */

document.addEventListener('DOMContentLoaded', () => {
  const inputCorreta = document.getElementById('campo-comentario_correta');
  const inputFonte = document.getElementById('campo-comentario_fonte');
  const inputsErros = document.querySelectorAll('.campo-comentario-erro');
  const radiosStatus = document.querySelectorAll('input[name="comentario_status"]');
  const pillStatus = document.getElementById('pill-status-atual');

  // Elementos da prévia
  const previaCorretaTexto = document.getElementById('previa-correta-texto');
  const previaFonteTexto = document.getElementById('previa-fonte-texto');
  const previaFonteWrapper = document.getElementById('previa-fonte-wrapper');

  // 1. Atualiza comentário da correta
  if (inputCorreta && previaCorretaTexto) {
    inputCorreta.addEventListener('input', () => {
      previaCorretaTexto.textContent = inputCorreta.value.trim() || '(redija a explicação da resposta correta...)';
    });
  }

  // 2. Atualiza justificativas de erro das outras alternativas
  inputsErros.forEach(input => {
    const letra = input.getAttribute('data-letra');
    const itemPrevia = document.getElementById(`previa-erro-alt-${letra}`);
    const textoPrevia = document.getElementById(`previa-erro-texto-${letra}`);

    if (input && itemPrevia && textoPrevia) {
      input.addEventListener('input', () => {
        const val = input.value.trim();
        if (val) {
          textoPrevia.textContent = val;
          itemPrevia.style.display = 'block';
        } else {
          textoPrevia.textContent = '';
          itemPrevia.style.display = 'none';
        }
      });
    }
  });

  // 3. Atualiza fonte / referência
  if (inputFonte && previaFonteTexto && previaFonteWrapper) {
    inputFonte.addEventListener('input', () => {
      const val = inputFonte.value.trim();
      if (val) {
        previaFonteTexto.textContent = val;
        previaFonteWrapper.style.display = 'block';
      } else {
        previaFonteTexto.textContent = '';
        previaFonteWrapper.style.display = 'none';
      }
    });
  }

  // 4. Atualiza pill de status
  radiosStatus.forEach(radio => {
    radio.addEventListener('change', () => {
      if (!pillStatus) return;
      if (radio.checked) {
        if (radio.value === 'publicado') {
          pillStatus.textContent = 'Status: Publicado';
          pillStatus.className = 'pill-status pill-publicado';
        } else {
          pillStatus.textContent = 'Status: Rascunho';
          pillStatus.className = 'pill-status pill-rascunho';
        }
      }
    });
  });
});
