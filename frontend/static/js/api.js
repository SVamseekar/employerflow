const API = "";
let _pendingRequests = 0;

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

function setGlobalLoading(active) {
  const bar = document.getElementById("global-loader");
  if (bar) bar.classList.toggle("active", active);
}

function setButtonLoading(btn, loading, label) {
  if (!btn) return;
  if (loading) {
    if (!btn.dataset.prevHtml) btn.dataset.prevHtml = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add("is-loading");
    btn.innerHTML = `<span class="spinner"></span><span>${label || "Working…"}</span>`;
  } else {
    btn.disabled = false;
    btn.classList.remove("is-loading");
    if (btn.dataset.prevHtml) {
      btn.innerHTML = btn.dataset.prevHtml;
      delete btn.dataset.prevHtml;
    }
  }
}

async function withButton(btn, label, fn) {
  setButtonLoading(btn, true, label);
  try {
    return await fn();
  } finally {
    setButtonLoading(btn, false);
  }
}

function setViewLoading(viewId, loading) {
  const view = document.getElementById(viewId);
  if (view) view.classList.toggle("is-loading", loading);
  if (!loading) {
    document.querySelectorAll(".nav-item.is-loading").forEach(n => n.classList.remove("is-loading"));
  }
}

function loadingTableRow(colspan, text = "Loading…") {
  return `<tr class="loading-row"><td colspan="${colspan}">
    <div class="loading-placeholder"><span class="spinner"></span>${text}</div>
  </td></tr>`;
}

function skeletonStats() {
  return Array(4).fill(0).map(() => `
    <div class="stat-card">
      <div class="skeleton-line" style="width:60%;margin-bottom:10px"></div>
      <div class="skeleton-line" style="width:40%;height:22px"></div>
    </div>`).join("");
}

async function api(path, opts = {}, retries = 0) {
  _pendingRequests++;
  setGlobalLoading(true);
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const res = await fetch(`${API}${path}`, { ...opts, headers });
    const data = await res.json().catch(() => ({}));

    if (res.status === 401) {
      logout();
      throw new Error("Session expired");
    }
    if (!res.ok) {
      const retryable = [404, 502, 503, 504].includes(res.status);
      if (retryable && retries < 2) {
        await new Promise(r => setTimeout(r, 4000));
        return api(path, opts, retries + 1);
      }
      const detail = data.detail || data.message || `Error ${res.status}`;
      if (res.status === 404) {
        throw new Error("Service is waking up — please try again in a few seconds.");
      }
      throw new Error(detail);
    }
    return data;
  } finally {
    _pendingRequests = Math.max(0, _pendingRequests - 1);
    if (_pendingRequests === 0) setGlobalLoading(false);
  }
}

function toast(msg, isError = false) {
  document.querySelectorAll(".toast").forEach(t => t.remove());
  const el = document.createElement("div");
  el.className = "toast";
  el.style.borderColor = isError ? "var(--danger)" : "var(--accent2)";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => {
    el.classList.add("is-leaving");
    setTimeout(() => el.remove(), 200);
  }, 3500);
}