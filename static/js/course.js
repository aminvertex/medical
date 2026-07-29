document.getElementById('review-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  delete payload.csrfmiddlewaretoken;
  payload.rating = Number(payload.rating);
  const button = form.querySelector('button'); button.disabled = true;
  try {
    const data = await MAHD.apiFetch(`/api/v1/catalog/courses/${form.dataset.courseId}/reviews`, { method: 'POST', body: JSON.stringify(payload) });
    MAHD.toast(data.message); form.reset();
  } catch (error) { if (!MAHD.requireLogin(error)) MAHD.toast(error.message, 'error'); }
  finally { button.disabled = false; }
});
