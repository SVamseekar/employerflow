let authMode = "login";
let empPage = 1;
let shortlistData = [];
let selectedShortlistId = null;
let activeView = "dashboard";

const PAGE_META = {
  dashboard: { eyebrow: "Overview", title: "Dashboard" },
  directory: { eyebrow: "Discovery", title: "Employer directory" },
  profile: { eyebrow: "Your data", title: "Profile" },
  shortlist: { eyebrow: "Pipeline", title: "Shortlist & outreach" },
  crm: { eyebrow: "Tracking", title: "Application CRM" },
  billing: { eyebrow: "Account", title: "Billing" },
};

function setPageMeta(name) {
  const meta = PAGE_META[name] || PAGE_META.dashboard;
  const eyebrow = document.getElementById("page-eyebrow");
  const title = document.getElementById("page-title");
  const actions = document.getElementById("topbar-actions");
  if (eyebrow) eyebrow.textContent = meta.eyebrow;
  if (title) title.textContent = meta.title;
  if (actions) {
    if (name === "shortlist") {
      actions.innerHTML = `<button class="btn btn-primary btn-sm" id="btn-generate-shortlist" onclick="generateShortlist(this)">Generate shortlist</button>`;
    } else if (name === "profile") {
      actions.innerHTML = `<button class="btn btn-primary btn-sm" id="btn-save-profile-top" onclick="saveProfile(this)">Save changes</button>`;
    } else {
      actions.innerHTML = "";
    }
  }
}

function updatePlanPill(plan) {
  const el = document.getElementById("user-plan");
  if (!el) return;
  el.textContent = plan || "free";
  el.className = "plan-pill" + (plan === "premium" ? " premium" : plan === "pro" ? " pro" : "");
}

function companyAvatar(name) {
  const parts = String(name || "?").trim().split(/\s+/);
  const initials = parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : String(name || "?").slice(0, 2).toUpperCase();
  return `<span class="avatar">${esc(initials)}</span>`;
}

function visaPill(status) {
  const s = String(status || "unknown").toLowerCase();
  let cls = "visa-unknown";
  if (s === "yes") cls = "visa-yes";
  else if (s === "possible") cls = "visa-possible";
  else if (s === "no") cls = "visa-no";
  const label = s === "yes" ? "Confirmed" : s === "possible" ? "Possible" : status || "Unknown";
  return `<span class="visa-pill ${cls}">${esc(label)}</span>`;
}

function scoreBadge(score) {
  if (score == null) return '<span class="status-pill">Pro+</span>';
  const n = Number(score);
  const cls = n >= 60 ? "score-high" : n >= 35 ? "score-mid" : "score-low";
  return `<span class="score-badge ${cls}">${n}</span>`;
}

function showAuthTab(mode) {
  authMode = mode;
  document.getElementById("tab-login").classList.toggle("active", mode === "login");
  document.getElementById("tab-register").classList.toggle("active", mode === "register");
  document.getElementById("name-field").style.display = mode === "register" ? "block" : "none";
  document.getElementById("auth-submit").textContent = mode === "register" ? "Create account" : "Sign in";
  const h2 = document.querySelector(".auth-card h2");
  const sub = document.querySelector(".auth-card .subtitle");
  if (h2) h2.textContent = mode === "register" ? "Create your account" : "Welcome back";
  if (sub) sub.textContent = mode === "register" ? "Start discovering visa-friendly employers" : "Sign in to continue your search";
  document.getElementById("auth-error").classList.add("hidden");
}

async function handleAuth(e) {
  e.preventDefault();
  const btn = document.getElementById("auth-submit");
  const errEl = document.getElementById("auth-error");
  errEl.classList.add("hidden");

  await withButton(btn, authMode === "register" ? "Creating account…" : "Signing in…", async () => {
    try {
      const path = authMode === "register" ? "/api/auth/register" : "/api/auth/login";
      const body = authMode === "register"
        ? { email: document.getElementById("email").value, password: document.getElementById("password").value, full_name: document.getElementById("full-name").value }
        : { email: document.getElementById("email").value, password: document.getElementById("password").value };
      const data = await api(path, { method: "POST", body: JSON.stringify(body) });
      setSession(data);
      toast(authMode === "register" ? "Account created — welcome!" : "Signed in");
      await initApp();
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
      toast(err.message, true);
    }
  });
}

function switchView(name) {
  activeView = name;
  setPageMeta(name);
  document.querySelectorAll(".view").forEach(v => v.classList.add("hidden"));
  document.getElementById(`view-${name}`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach(n => {
    n.classList.toggle("active", n.dataset.view === name);
    n.classList.remove("is-loading");
  });

  if (name === "dashboard") loadDashboard();
  if (name === "directory") loadEmployers();
  if (name === "profile") loadProfile();
  if (name === "shortlist") loadShortlist();
  if (name === "crm") loadCRM();
  if (name === "billing") loadBilling();
}

async function initApp() {
  document.getElementById("auth-screen").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  const user = getUser();
  document.getElementById("user-email").textContent = user.email || "";
  updatePlanPill(user.plan || "free");

  setViewLoading("view-dashboard", true);
  document.getElementById("dash-stats").innerHTML = skeletonStats();
  try {
    const me = await api("/api/auth/me");
    const u = getUser();
    u.plan = me.plan;
    localStorage.setItem("ef_user", JSON.stringify(u));
    updatePlanPill(me.plan);
  } finally {
    setViewLoading("view-dashboard", false);
  }

  if (location.hash === "#register") showAuthTab("register");
  if (new URLSearchParams(location.search).get("billing") === "success") {
    toast("Payment successful — your plan is updating.");
  }
  switchView("dashboard");
}

async function loadDashboard() {
  setViewLoading("view-dashboard", true);
  document.getElementById("dash-stats").innerHTML = skeletonStats();
  try {
    const stats = await api("/api/employers/stats");
    const plan = getUser().plan || "free";
    document.getElementById("dash-stats").innerHTML = `
      <div class="stat-card">
        <div class="label">Total employers</div>
        <div class="value">${stats.total.toLocaleString()}</div>
      </div>
      <div class="stat-card accent-teal">
        <div class="label">Visa confirmed</div>
        <div class="value">${stats.visa_confirmed.toLocaleString()}</div>
      </div>
      <div class="stat-card accent-signal">
        <div class="label">Remote-friendly</div>
        <div class="value">${stats.remote.toLocaleString()}</div>
      </div>
      <div class="stat-card">
        <div class="label">Your plan</div>
        <div class="value text-plan">${esc(plan)}</div>
      </div>`;
  } catch (err) {
    document.getElementById("dash-stats").innerHTML =
      `<div class="stat-card" style="grid-column:1/-1;color:var(--danger)">${esc(err.message)}</div>`;
    toast(err.message, true);
  } finally {
    setViewLoading("view-dashboard", false);
  }
}

async function loadEmployers(btn) {
  const tbody = document.getElementById("emp-tbody");
  const pageInfo = document.getElementById("emp-page-info");
  setViewLoading("view-directory", true);
  if (btn) setButtonLoading(btn, true, "Loading…");
  tbody.innerHTML = loadingTableRow(5, "Loading employers…");
  pageInfo.textContent = "Loading…";

  const search = document.getElementById("emp-search").value;
  const region = document.getElementById("emp-region").value;
  const visa = document.getElementById("emp-visa").value;
  const params = new URLSearchParams({ page: empPage, limit: 50 });
  if (search) params.set("search", search);
  if (region) params.set("region", region);
  if (visa) params.set("visa", visa);

  try {
    const res = await api(`/api/employers?${params}`);
    if (!res.data.length) {
      tbody.innerHTML = `<tr><td colspan="5">
        <div class="empty-state" style="padding:32px">
          <div class="empty-icon">🔍</div>
          <h3>No employers found</h3>
          <p>Try clearing filters or broadening your search.</p>
        </div></td></tr>`;
    } else {
      tbody.innerHTML = res.data.map(e => `
        <tr>
          <td>
            <div class="company-cell">
              ${companyAvatar(e.company)}
              <div>
                <div class="company-name">${esc(e.company)}</div>
                <div class="company-sub">${esc(e.region || "")}</div>
              </div>
            </div>
          </td>
          <td>${esc(e.sector)}</td>
          <td>${esc(e.country)}</td>
          <td>${visaPill(e.visa_sponsorship)}</td>
          <td>${scoreBadge(e.score)}</td>
        </tr>`).join("");
    }
    pageInfo.textContent = `Page ${res.page} · ${res.total.toLocaleString()} results · ${res.plan}${!res.scoring_enabled ? " · upgrade for scores" : ""}`;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--danger);padding:16px">${esc(err.message)}</td></tr>`;
    pageInfo.textContent = "Failed to load";
    toast(err.message, true);
  } finally {
    setViewLoading("view-directory", false);
    if (btn) setButtonLoading(btn, false);
  }
}

async function loadProfile() {
  setViewLoading("view-profile", true);
  try {
    const p = await api("/api/auth/profile");
    document.getElementById("p-headline").value = p.headline || "";
    document.getElementById("p-location").value = p.location || "";
    document.getElementById("p-visa").value = p.visa_status || "";
    document.getElementById("p-linkedin").value = p.linkedin || "";
    document.getElementById("p-cert").value = p.certification || "";
    document.getElementById("p-stack").value = p.stack_highlight || "";
    document.getElementById("p-summary").value = p.summary || "";
    document.getElementById("p-roles").value = (p.role_targets || []).join(", ");
    const skills = Array.isArray(p.skills) ? p.skills : Object.values(p.skills || {}).flat();
    document.getElementById("p-skills").value = skills.join(", ");
    document.getElementById("p-projects").value = JSON.stringify(p.projects || [], null, 2);
  } catch (err) {
    toast(err.message, true);
  } finally {
    setViewLoading("view-profile", false);
  }
}

async function saveProfile(btn) {
  const skillsRaw = document.getElementById("p-skills").value;
  const skills = skillsRaw.split(",").map(s => s.trim()).filter(Boolean);
  let projects = [];
  try { projects = JSON.parse(document.getElementById("p-projects").value || "[]"); }
  catch { toast("Invalid projects JSON", true); return; }

  await withButton(btn, "Saving…", async () => {
    await api("/api/auth/profile", {
      method: "PUT",
      body: JSON.stringify({
        headline: document.getElementById("p-headline").value,
        location: document.getElementById("p-location").value,
        visa_status: document.getElementById("p-visa").value,
        linkedin: document.getElementById("p-linkedin").value,
        certification: document.getElementById("p-cert").value,
        stack_highlight: document.getElementById("p-stack").value,
        summary: document.getElementById("p-summary").value,
        skills,
        projects,
        languages: { English: "fluent" },
        role_targets: document.getElementById("p-roles").value.split(",").map(s => s.trim()).filter(Boolean),
        relocation_targets: [],
      }),
    });
    toast("Profile saved");
  });
}

async function generateShortlist(btn) {
  await withButton(btn, "Generating…", async () => {
    try {
      const res = await api("/api/shortlist/generate", { method: "POST" });
      toast(`Generated ${res.generated} companies`);
      selectedShortlistId = null;
      await loadShortlist();
    } catch (err) {
      toast(err.message, true);
      if (err.message.includes("402") || err.message.includes("pro plan")) switchView("billing");
      throw err;
    }
  });
}

function renderShortlistQueue(items) {
  const list = document.getElementById("sl-queue");
  const count = document.getElementById("sl-count");
  if (!list) return;

  if (count) {
    const total = shortlistData.length;
    count.textContent = items.length === total
      ? `${total} companies`
      : `${items.length} of ${total}`;
  }

  if (!items.length) {
    list.innerHTML = `<li class="queue-empty">No matches for this filter</li>`;
    return;
  }

  list.innerHTML = items.map(item => `
    <li>
      <button type="button" class="queue-item${item.id === selectedShortlistId ? " active" : ""}"
        data-id="${item.id}" onclick="selectShortlist(${item.id})" role="option"
        aria-selected="${item.id === selectedShortlistId}">
        <span class="q-score">${item.score}</span>
        <span class="q-info">
          <span class="q-name">${esc(item.employer.company)}</span>
          <span class="q-loc">${esc(item.employer.country)}${item.employer.sector ? " · " + esc(item.employer.sector) : ""}</span>
        </span>
      </button>
    </li>`).join("");
}

function filterShortlistQueue() {
  const q = (document.getElementById("sl-filter")?.value || "").toLowerCase().trim();
  const filtered = !q ? shortlistData : shortlistData.filter(item => {
    const blob = `${item.employer.company} ${item.employer.country} ${item.employer.sector} ${item.match_notes}`.toLowerCase();
    return blob.includes(q);
  });
  renderShortlistQueue(filtered);
}

async function loadShortlist() {
  setViewLoading("view-shortlist", true);
  const queue = document.getElementById("sl-queue");
  if (queue) queue.innerHTML = `<li class="queue-empty">Loading…</li>`;

  try {
    shortlistData = await api("/api/shortlist");
  } catch (err) {
    document.getElementById("shortlist-empty").classList.remove("hidden");
    document.getElementById("shortlist-detail").classList.add("hidden");
    toast(err.message, true);
    return;
  } finally {
    setViewLoading("view-shortlist", false);
  }

  if (!shortlistData.length) {
    document.getElementById("shortlist-empty").classList.remove("hidden");
    document.getElementById("shortlist-detail").classList.add("hidden");
    return;
  }

  document.getElementById("shortlist-empty").classList.add("hidden");
  document.getElementById("shortlist-detail").classList.remove("hidden");

  const filterEl = document.getElementById("sl-filter");
  if (filterEl) filterEl.value = "";
  renderShortlistQueue(shortlistData);

  const stillSelected = shortlistData.some(s => s.id === selectedShortlistId);
  if (!stillSelected) selectedShortlistId = null;
  if (!selectedShortlistId) await selectShortlist(shortlistData[0].id);
  else await selectShortlist(selectedShortlistId);
}

async function selectShortlist(id) {
  selectedShortlistId = id;
  document.querySelectorAll(".queue-item").forEach(el => {
    const on = Number(el.dataset.id) === id;
    el.classList.toggle("active", on);
    el.setAttribute("aria-selected", on);
  });

  const summary = shortlistData.find(s => s.id === id);
  if (!summary) return;

  const notesEl = document.getElementById("sl-notes");
  document.getElementById("sl-company").textContent = summary.employer.company;
  document.getElementById("sl-meta").textContent =
    [summary.employer.sector, summary.employer.country].filter(Boolean).join(" · ");
  if (notesEl) {
    if (summary.match_notes) {
      notesEl.textContent = summary.match_notes;
      notesEl.classList.remove("hidden");
    } else {
      notesEl.textContent = "";
      notesEl.classList.add("hidden");
    }
  }

  document.getElementById("sl-to").value = summary.to_email || "";
  document.getElementById("sl-job").value = summary.job_url || "";
  document.getElementById("sl-draft").value = "";
  document.getElementById("sl-draft").placeholder = "Loading…";

  try {
    const item = await api(`/api/shortlist/${id}`);
    document.getElementById("sl-to").value = item.to_email || "";
    document.getElementById("sl-job").value = item.job_url || "";
    document.getElementById("sl-draft").value = item.email_draft || "";
    document.getElementById("sl-draft").placeholder = "";
    const idx = shortlistData.findIndex(s => s.id === id);
    if (idx >= 0) shortlistData[idx] = { ...shortlistData[idx], ...item };
  } catch (err) {
    document.getElementById("sl-draft").placeholder = "Could not load draft";
    toast(err.message, true);
  }
}

async function saveShortlistItem(btn) {
  if (!selectedShortlistId) return;
  await withButton(btn, "Saving…", async () => {
    await api(`/api/shortlist/${selectedShortlistId}`, {
      method: "PUT",
      body: JSON.stringify({
        to_email: document.getElementById("sl-to").value,
        job_url: document.getElementById("sl-job").value,
        email_draft: document.getElementById("sl-draft").value,
      }),
    });
    const idx = shortlistData.findIndex(s => s.id === selectedShortlistId);
    if (idx >= 0) {
      shortlistData[idx].to_email = document.getElementById("sl-to").value;
      shortlistData[idx].job_url = document.getElementById("sl-job").value;
    }
    toast("Draft saved");
  });
}

async function loadCRM() {
  const plan = getUser().plan;
  if (plan !== "premium") {
    document.getElementById("crm-locked").classList.remove("hidden");
    document.getElementById("crm-content").classList.add("hidden");
    return;
  }
  document.getElementById("crm-locked").classList.add("hidden");
  document.getElementById("crm-content").classList.remove("hidden");

  setViewLoading("view-crm", true);
  document.getElementById("crm-tbody").innerHTML = loadingTableRow(5, "Loading applications…");
  try {
    const apps = await api("/api/applications");
    if (!apps.length) {
      document.getElementById("crm-tbody").innerHTML = `<tr><td colspan="5">
        <div class="empty-state" style="padding:28px">
          <p style="color:var(--mist)">No applications tracked yet. Add your first one above.</p>
        </div></td></tr>`;
    } else {
      document.getElementById("crm-tbody").innerHTML = apps.map(a => `
        <tr>
          <td><div class="company-cell">${companyAvatar(a.company)}<span class="company-name">${esc(a.company)}</span></div></td>
          <td>${esc(a.role)}</td>
          <td><span class="status-pill">${esc(a.status)}</span></td>
          <td style="font-family:var(--mono);font-size:12px">${esc(a.follow_up_date) || "—"}</td>
          <td style="font-size:12px;color:var(--mist)">${esc(a.notes)}</td>
        </tr>`).join("");
    }
  } catch (err) {
    document.getElementById("crm-tbody").innerHTML =
      `<tr><td colspan="5" style="color:var(--danger);padding:16px">${esc(err.message)}</td></tr>`;
    toast(err.message, true);
  } finally {
    setViewLoading("view-crm", false);
  }
}

async function addApplication(btn) {
  await withButton(btn, "Adding…", async () => {
    await api("/api/applications", {
      method: "POST",
      body: JSON.stringify({
        company: document.getElementById("crm-company").value,
        role: document.getElementById("crm-role").value,
        status: document.getElementById("crm-status").value,
        follow_up_date: document.getElementById("crm-followup").value,
        notes: document.getElementById("crm-notes").value,
      }),
    });
    toast("Application added");
    document.getElementById("crm-company").value = "";
    document.getElementById("crm-role").value = "";
    document.getElementById("crm-notes").value = "";
    await loadCRM();
  });
}

async function loadBilling() {
  setViewLoading("view-billing", true);
  document.getElementById("billing-plans").innerHTML =
    `<div class="price-card"><div class="skeleton-line" style="width:40%;margin-bottom:12px"></div>
     <div class="skeleton-line" style="width:60%;height:28px;margin-bottom:16px"></div>
     <div class="skeleton-line" style="width:80%"></div></div>`.repeat(3);
  try {
    const { plans } = await api("/api/billing/plans");
    const current = getUser().plan;
    document.getElementById("billing-plans").innerHTML = plans.map(p => `
      <div class="price-card ${p.id === "pro" ? "featured" : ""}">
        <h3>${p.name} ${p.id === current ? '<span style="font-size:11px;color:var(--teal);font-weight:600"> · current</span>' : ""}</h3>
        <div class="price">$${p.price} <span>/ month</span></div>
        <ul>${p.features.map(f => `<li>${f}</li>`).join("")}</ul>
        ${p.id !== "free" && p.id !== current
          ? `<button class="btn btn-primary" style="width:100%" onclick="checkout('${p.id}', this)">Subscribe</button>`
          : p.id === "free"
            ? `<span style="color:var(--mist);font-size:13px">Default plan</span>`
            : `<span style="color:var(--teal);font-size:13px;font-weight:600">Active on your account</span>`}
      </div>`).join("");
  } catch (err) {
    document.getElementById("billing-plans").innerHTML = `<p style="color:var(--danger)">${esc(err.message)}</p>`;
    toast(err.message, true);
  } finally {
    setViewLoading("view-billing", false);
  }
}

async function checkout(plan, btn) {
  await withButton(btn, "Redirecting…", async () => {
    try {
      const { checkout_url } = await api("/api/billing/checkout", {
        method: "POST", body: JSON.stringify({ plan }),
      });
      window.location.href = checkout_url;
    } catch (err) {
      toast(err.message, true);
      throw err;
    }
  });
}

async function openPortal(btn) {
  await withButton(btn, "Opening…", async () => {
    try {
      const { portal_url } = await api("/api/billing/portal", { method: "POST" });
      window.location.href = portal_url;
    } catch (err) {
      toast(err.message, true);
      throw err;
    }
  });
}

function esc(s) {
  return String(s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("is-loading"));
    if (btn.dataset.view !== activeView) btn.classList.add("is-loading");
  });
});

if (location.hash === "#register") showAuthTab("register");
if (getToken()) initApp().catch(() => logout());
else showAuthTab(location.hash === "#register" ? "register" : "login");