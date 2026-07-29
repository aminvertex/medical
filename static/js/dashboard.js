document.addEventListener('click', async event => {
  const saveUser = event.target.closest('[data-save-user]');
  if (saveUser) {
    const id = saveUser.dataset.saveUser; const role = document.querySelector(`[data-user-role="${id}"]`).value;
    try { const data = await MAHD.apiFetch(`/api/v1/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify({ role }) }); MAHD.toast(data.message); }
    catch (error) { MAHD.toast(error.message, 'error'); }
  }
  const toggleUser = event.target.closest('[data-toggle-user]');
  if (toggleUser) {
    const id = toggleUser.dataset.toggleUser; const active = toggleUser.dataset.active === 'true';
    try { const data = await MAHD.apiFetch(`/api/v1/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify({ is_active: !active }) }); MAHD.toast(data.message); location.reload(); }
    catch (error) { MAHD.toast(error.message, 'error'); }
  }
  const toggleCourse = event.target.closest('[data-toggle-course]');
  if (toggleCourse) {
    const id = toggleCourse.dataset.toggleCourse; const active = toggleCourse.dataset.active === 'true';
    try { const data = await MAHD.apiFetch(`/api/v1/admin/courses/${id}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: !active }) }); MAHD.toast(data.message); location.reload(); }
    catch (error) { MAHD.toast(error.message, 'error'); }
  }
});

document.querySelectorAll('[data-message-status]').forEach(select => {
  select.addEventListener('change', async () => {
    try { const data = await MAHD.apiFetch(`/api/v1/admin/messages/${select.dataset.messageStatus}`, { method: 'PATCH', body: JSON.stringify({ status: select.value }) }); MAHD.toast(data.message); }
    catch (error) { MAHD.toast(error.message, 'error'); }
  });
});
