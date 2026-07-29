// منوی موبایل همبرگری
document.addEventListener('DOMContentLoaded', () => {
  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  const closeBtn = document.querySelector('.close-btn');

  if (!hamburger || !mobileMenu || !closeBtn) return;

  // باز کردن منو
  hamburger.addEventListener('click', () => {
    mobileMenu.style.display = 'flex';
  });

  // بستن منو
  closeBtn.addEventListener('click', () => {
    mobileMenu.style.display = 'none';
  });

  // بستن منو با کلیک خارج از آن (اختیاری)
  mobileMenu.addEventListener('click', (e) => {
    if (e.target === mobileMenu) {
      mobileMenu.style.display = 'none';
    }
  });
});