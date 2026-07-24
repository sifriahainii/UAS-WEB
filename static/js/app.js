(() => {
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-nav]');
  if (toggle && nav) toggle.addEventListener('click', () => nav.classList.toggle('open'));
  document.querySelectorAll('[data-alert-close]').forEach(btn => btn.addEventListener('click', () => btn.closest('[data-alert]')?.remove()));
  document.querySelectorAll('[data-password-toggle]').forEach(btn => btn.addEventListener('click', () => {
    const input = btn.parentElement.querySelector('input');
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    btn.textContent = input.type === 'password' ? '◉' : '◎';
  }));
  setTimeout(() => document.querySelectorAll('[data-alert]').forEach(el => el.remove()), 6000);
})();
