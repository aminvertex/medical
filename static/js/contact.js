document.getElementById('contact-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  delete payload.csrfmiddlewaretoken;
  const button = form.querySelector('button'); const errorBox = document.getElementById('contact-error');
  button.disabled = true; errorBox.hidden = true;
  try {
    const data = await MAHD.apiFetch('/api/v1/core/contact', { method: 'POST', body: JSON.stringify(payload) });
    MAHD.toast(data.message); form.reset();
  } catch (error) { errorBox.textContent = error.message; errorBox.hidden = false; }
  finally { button.disabled = false; }
});
