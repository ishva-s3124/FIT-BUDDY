document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
      const button = form.querySelector('button[type="submit"]');
      if (button && !form.dataset.noLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = 'Working…';
      }
    });
  });
});
