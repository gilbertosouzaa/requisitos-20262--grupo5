// Apoio ENADE — JS para a Tela de Início (T05)
document.addEventListener('DOMContentLoaded', function () {
  // Animação suave para as barras de progresso
  const progressBars = document.querySelectorAll('.progress-bar-fill');
  progressBars.forEach(function (bar) {
    const targetWidth = bar.style.width;
    bar.style.width = '0%';
    requestAnimationFrame(function () {
      bar.style.width = targetWidth;
    });
  });
});
