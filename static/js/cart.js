document.addEventListener('click', async event => {
  const button = event.target.closest('[data-remove-course]');
  if (!button) return;
  button.disabled = true;
  try {
    const data = await MAHD.apiFetch(`/api/v1/store/cart/items/${button.dataset.removeCourse}`, { method: 'DELETE' });
    document.querySelector(`[data-cart-course="${button.dataset.removeCourse}"]`)?.remove();
    document.getElementById('cart-badge').textContent = data.count;
    document.getElementById('summary-count').textContent = data.count;
    const formatted = `${Number(data.subtotal).toLocaleString('fa-IR')} تومان`;
    document.getElementById('summary-subtotal').textContent = formatted;
    document.getElementById('summary-total').textContent = formatted;
    MAHD.toast(data.message);
    if (!data.count) location.reload();
  } catch (error) { MAHD.toast(error.message, 'error'); button.disabled = false; }
});
