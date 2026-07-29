document.querySelectorAll('[data-auth-tab]').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('[data-auth-tab]').forEach(item => item.classList.toggle('active', item === button));
    document.querySelectorAll('[data-auth-panel]').forEach(panel => panel.classList.toggle('active', panel.dataset.authPanel === button.dataset.authTab));
    document.getElementById('auth-error').hidden = true;
  });
});

function authPayload(form) { return Object.fromEntries(new FormData(form).entries()); }
function nextUrl() {
  const candidate = new URLSearchParams(location.search).get('next') || '/account/';
  return candidate.startsWith('/') && !candidate.startsWith('//') ? candidate : '/account/';
}

async function submitAuth(form, endpoint) {
  const errorBox = document.getElementById('auth-error');
  const button = form.querySelector('button[type="submit"]');
  errorBox.hidden = true; button.disabled = true;
  try {
    const data = await MAHD.apiFetch(endpoint, { method: 'POST', body: JSON.stringify(authPayload(form)) });
    MAHD.toast(data.message);
    location.href = nextUrl();
  } catch (error) {
    errorBox.textContent = error.message; errorBox.hidden = false;
  } finally { button.disabled = false; }
}

document.getElementById('login-form')?.addEventListener('submit', event => { event.preventDefault(); submitAuth(event.currentTarget, '/api/v1/auth/login'); });
document.getElementById('register-form')?.addEventListener('submit', event => { event.preventDefault(); submitAuth(event.currentTarget, '/api/v1/auth/register'); });
