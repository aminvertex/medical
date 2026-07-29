document.getElementById('checkout-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const errorBox = document.getElementById('checkout-error');
  const button = form.querySelector('button[type="submit"]');
  const payload = Object.fromEntries(new FormData(form).entries());
  delete payload.csrfmiddlewaretoken;
  errorBox.hidden = true; button.disabled = true; button.textContent = 'در حال ثبت سفارش...';
  try {
    const order = await MAHD.apiFetch('/api/v1/store/checkout', { method: 'POST', body: JSON.stringify(payload) });
    button.textContent = 'در حال پرداخت آزمایشی...';
    const payment = await MAHD.apiFetch(`/api/v1/store/orders/${order.order_number}/pay`, { method: 'POST', body: '{}' });
    location.href = payment.redirect_url;
  } catch (error) {
    errorBox.textContent = error.message; errorBox.hidden = false;
    button.disabled = false; button.textContent = 'ثبت سفارش و پرداخت آزمایشی';
  }
});
