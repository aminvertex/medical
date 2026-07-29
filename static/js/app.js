(function () {
  function getCookie(name) {
    const item = document.cookie.split('; ').find(row => row.startsWith(name + '='));
    return item ? decodeURIComponent(item.split('=').slice(1).join('=')) : '';
  }

  async function apiFetch(url, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    const method = (options.method || 'GET').toUpperCase();
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers['X-CSRFToken'] = getCookie('csrftoken');
    const response = await fetch(url, { credentials: 'same-origin', ...options, headers });
    let data = {};
    try { data = await response.json(); } catch (_) {}
    if (!response.ok) {
      const error = new Error(data.detail || data.message || 'خطایی رخ داد.');
      error.status = response.status;
      error.data = data;
      throw error;
    }
    return data;
  }

  function toast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => el.remove(), 3800);
  }

  function requireLogin(error) {
    if (error && error.status === 401) {
      const next = encodeURIComponent(location.pathname + location.search);
      location.href = `/auth/?next=${next}`;
      return true;
    }
    return false;
  }

  window.MAHD = { apiFetch, toast, requireLogin, getCookie };

  const toggle = document.querySelector('[data-mobile-toggle]');
  const nav = document.querySelector('[data-mobile-nav]');
  toggle?.addEventListener('click', () => nav?.classList.toggle('open'));

  document.addEventListener('click', async (event) => {
    const addButton = event.target.closest('[data-add-course]');
    if (addButton) {
      addButton.disabled = true;
      try {
        const data = await apiFetch('/api/v1/store/cart/items', { method: 'POST', body: JSON.stringify({ course_id: Number(addButton.dataset.addCourse) }) });
        document.getElementById('cart-badge').textContent = data.count;
        toast(data.message);
      } catch (error) {
        if (!requireLogin(error)) toast(error.message, 'error');
      } finally { addButton.disabled = false; }
    }

    const payButton = event.target.closest('[data-pay-order]');
    if (payButton) {
      payButton.disabled = true;
      try {
        const data = await apiFetch(`/api/v1/store/orders/${payButton.dataset.payOrder}/pay`, { method: 'POST', body: '{}' });
        toast(data.message);
        location.href = data.redirect_url;
      } catch (error) {
        if (!requireLogin(error)) toast(error.message, 'error');
        payButton.disabled = false;
      }
    }

    const favoriteButton = event.target.closest('[data-favorite-course]');
    if (favoriteButton) {
      favoriteButton.disabled = true;
      try {
        const data = await apiFetch(`/api/v1/catalog/courses/${favoriteButton.dataset.favoriteCourse}/favorite`, { method: 'POST', body: '{}' });
        favoriteButton.classList.toggle('active', data.is_favorite);
        favoriteButton.classList.toggle('is-favorite', data.is_favorite);
        toast(data.message);
      } catch (error) {
        if (!requireLogin(error)) toast(error.message, 'error');
      } finally { favoriteButton.disabled = false; }
    }
  });

  document.getElementById('newsletter-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const data = await apiFetch('/api/v1/core/newsletter', { method: 'POST', body: JSON.stringify({ email: form.email.value }) });
      toast(data.message);
      form.reset();
    } catch (error) { toast(error.message, 'error'); }
    finally { button.disabled = false; }
  });
})();
