const API = "";

function getToken() {
  return localStorage.getItem("ef_token");
}

function setSession(data) {
  localStorage.setItem("ef_token", data.access_token);
  localStorage.setItem("ef_user", JSON.stringify({
    email: data.email,
    full_name: data.full_name,
    plan: data.plan,
  }));
}

function getUser() {
  try { return JSON.parse(localStorage.getItem("ef_user") || "{}"); }
  catch { return {}; }
}

function logout() {
  localStorage.removeItem("ef_token");
  localStorage.removeItem("ef_user");
  window.location.href = "/";
}

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API}${path}`, { ...opts, headers });
  const data = await res.json().catch(() => ({}));

  if (res.status === 401) {
    logout();
    throw new Error("Session expired");
  }
  if (!res.ok) throw new Error(data.detail || data.message || `Error ${res.status}`);
  return data;
}

function toast(msg, isError = false) {
  const el = document.createElement("div");
  el.className = "toast";
  el.style.borderColor = isError ? "var(--danger)" : "var(--accent2)";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}