const state = {
  conferences: [],
  topics: [],
  activeTopics: new Set(),
  search: "",
  sortBy: "deadline",
  view: "list",
  calendarMonth: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
};

function scoreColor(score) {
  if (score >= 75) return "var(--good)";
  if (score >= 50) return "var(--mid)";
  return "var(--low)";
}

function nextDeadline(record) {
  const now = new Date();
  const upcoming = (record.deadlines || [])
    .filter((d) => d.when && new Date(d.when) >= now)
    .sort((a, b) => new Date(a.when) - new Date(b.when));
  return upcoming[0] || null;
}

function daysUntil(iso) {
  const ms = new Date(iso) - new Date();
  return Math.ceil(ms / (1000 * 60 * 60 * 24));
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function matchesFilters(record) {
  if (state.activeTopics.size > 0) {
    const recordTopics = new Set(record.topics || []);
    const hasTopic = [...state.activeTopics].some((t) => recordTopics.has(t));
    if (!hasTopic) return false;
  }
  if (state.search.trim()) {
    const q = state.search.trim().toLowerCase();
    const hay = `${record.title} ${record.full_name || ""}`.toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}

function render() {
  if (state.view === "calendar") {
    document.querySelector("#conf-table").hidden = true;
    document.querySelector("#calendar-view").hidden = false;
    renderCalendar();
    return;
  }
  document.querySelector("#conf-table").hidden = false;
  document.querySelector("#calendar-view").hidden = true;

  const tbody = document.querySelector("#conf-table tbody");
  tbody.innerHTML = "";

  let rows = state.conferences.filter(matchesFilters);

  rows.sort((a, b) => {
    if (state.sortBy === "score") {
      return (b.reputation?.score || 0) - (a.reputation?.score || 0);
    }
    const da = nextDeadline(a);
    const db = nextDeadline(b);
    if (!da && !db) return 0;
    if (!da) return 1;
    if (!db) return -1;
    return new Date(da.when) - new Date(db.when);
  });

  document.querySelector("#count").textContent = `${rows.length} conference${rows.length === 1 ? "" : "s"}`;

  for (const r of rows) {
    const tr = document.createElement("tr");
    const nd = nextDeadline(r);
    const score = r.reputation?.score ?? "–";
    const basisNote = r.basis === "manual" ? '<div class="basis-manual">manual score</div>' : "";

    tr.innerHTML = `
      <td>
        <a class="conf-link" href="${r.link || "#"}" target="_blank" rel="noopener">${r.title} ${r.year}</a>
        <div>${(r.topics || []).map((t) => `<span class="topic-tag">${t}</span>`).join("")}</div>
      </td>
      <td>${nd ? `${fmtDate(nd.when)} <div class="basis-manual">${daysUntil(nd.when)}d · ${nd.label || nd.type}</div>` : "–"}</td>
      <td>${r.place || "–"}</td>
      <td><span class="score-badge" style="background:${scoreColor(score)}">${score}</span>${basisNote}</td>
    `;
    tbody.appendChild(tr);
  }
}

function allDeadlinesForCalendar() {
  // Flatten every deadline (not just "next") for conferences matching the
  // current topic/search filters, so the calendar shows the full picture.
  const items = [];
  for (const r of state.conferences.filter(matchesFilters)) {
    for (const d of r.deadlines || []) {
      if (d.when) items.push({ record: r, deadline: d });
    }
  }
  return items;
}

function renderCalendar() {
  const grid = document.querySelector("#calendar-grid");
  const label = document.querySelector("#cal-month-label");
  const year = state.calendarMonth.getFullYear();
  const month = state.calendarMonth.getMonth();

  label.textContent = state.calendarMonth.toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });

  const items = allDeadlinesForCalendar();
  const byDay = new Map(); // "YYYY-MM-DD" -> [{record, deadline}]
  for (const item of items) {
    const d = new Date(item.deadline.when);
    const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    if (!byDay.has(key)) byDay.set(key, []);
    byDay.get(key).push(item);
  }

  const firstOfMonth = new Date(year, month, 1);
  const startOffset = firstOfMonth.getDay(); // 0 = Sunday
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = new Date();

  grid.innerHTML = "";
  for (const wd of ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]) {
    const h = document.createElement("div");
    h.className = "cal-weekday";
    h.textContent = wd;
    grid.appendChild(h);
  }

  for (let i = 0; i < startOffset; i++) {
    const blank = document.createElement("div");
    blank.className = "cal-cell cal-cell--outside";
    grid.appendChild(blank);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const cell = document.createElement("div");
    cell.className = "cal-cell";
    const isToday =
      today.getFullYear() === year && today.getMonth() === month && today.getDate() === day;
    if (isToday) cell.classList.add("cal-cell--today");

    const dayItems = (byDay.get(`${year}-${month}-${day}`) || []).sort(
      (a, b) => new Date(a.deadline.when) - new Date(b.deadline.when)
    );

    const chips = dayItems
      .map(({ record, deadline }) => {
        const score = record.reputation?.score ?? 0;
        const label = deadline.label || deadline.type;
        const title = `${record.title} ${record.year} — ${label}`;
        return `<a class="cal-event" style="background:${scoreColor(score)}" title="${title}" href="${record.link || "#"}" target="_blank" rel="noopener">${record.title} — ${label}</a>`;
      })
      .join("");

    cell.innerHTML = `<div class="cal-daynum">${day}</div><div class="cal-events">${chips}</div>`;
    grid.appendChild(cell);
  }
}

function renderChips() {
  const el = document.querySelector("#topic-chips");
  el.innerHTML = "";
  for (const topic of state.topics) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = topic;
    chip.addEventListener("click", () => {
      if (state.activeTopics.has(topic)) {
        state.activeTopics.delete(topic);
        chip.classList.remove("active");
      } else {
        state.activeTopics.add(topic);
        chip.classList.add("active");
      }
      render();
    });
    el.appendChild(chip);
  }
}

async function renderChangelog() {
  const res = await fetch("changelog.json");
  const entries = await res.json();
  const el = document.querySelector("#changelog-list");
  if (!entries.length) {
    el.innerHTML = '<p class="basis-manual">No changes recorded yet.</p>';
    return;
  }
  el.innerHTML = entries
    .slice(0, 40)
    .map((e) => {
      let detail = "";
      if (e.event === "deadline_changed") detail = `${e.deadline_type} moved ${e.old} → ${e.new}`;
      else if (e.event === "deadline_added") detail = `${e.deadline_type} deadline added: ${e.new}`;
      else if (e.event === "added") detail = "newly tracked";
      else if (e.event === "removed") detail = "no longer tracked";
      else if (e.event === "score_changed") detail = `score ${e.old} → ${e.new}`;
      else if (e.event === "seed_page_changed") detail = `source page changed — verify: ${e.url}`;
      return `<div class="change-item"><span class="ts">${new Date(e.timestamp).toLocaleString()}</span>${e.conference || ""} — ${detail}</div>`;
    })
    .join("");
}

function buildSubscribePanel(httpsUrl, name) {
  const webcalUrl = httpsUrl.replace(/^https?:/, "webcal:");
  const googleUrl = "https://calendar.google.com/calendar/render?cid=" + encodeURIComponent(webcalUrl);
  const outlookUrl =
    "https://outlook.live.com/calendar/0/addfromweb?url=" +
    encodeURIComponent(httpsUrl) +
    "&name=" +
    encodeURIComponent(name);

  const panel = document.createElement("div");
  panel.innerHTML = `
    <a class="dropdown-link" href="${googleUrl}" target="_blank" rel="noopener">Add to Google Calendar</a>
    <a class="dropdown-link" href="${outlookUrl}" target="_blank" rel="noopener">Add to Outlook.com</a>
    <a class="dropdown-link" href="${webcalUrl}">Open in default calendar app</a>
    <button type="button" class="dropdown-link copy-link">Copy link (Apple Calendar / other)</button>
  `;
  panel.querySelector(".copy-link").addEventListener("click", async (e) => {
    await navigator.clipboard.writeText(httpsUrl).catch(() => {});
    e.target.textContent = "Copied!";
    setTimeout(() => (e.target.textContent = "Copy link (Apple Calendar / other)"), 1500);
  });
  return panel;
}

function wireSubscribeLinks() {
  const base = window.location.href.replace(/[^/]*$/, "");
  const feeds = {
    watchlist: { url: base + "calendar-watchlist.ics", name: "ConferenceWatcher — My Watchlist" },
    all: { url: base + "calendar-all.ics", name: "ConferenceWatcher — All Tracked Deadlines" },
  };
  document.querySelectorAll(".dropdown-panel").forEach((panel) => {
    const feed = feeds[panel.dataset.feed];
    panel.appendChild(buildSubscribePanel(feed.url, feed.name));
  });
}

function wireViewToggle() {
  document.querySelectorAll(".view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".view-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.view = btn.dataset.view;
      render();
    });
  });
  document.querySelector("#cal-prev").addEventListener("click", () => {
    state.calendarMonth = new Date(state.calendarMonth.getFullYear(), state.calendarMonth.getMonth() - 1, 1);
    render();
  });
  document.querySelector("#cal-next").addEventListener("click", () => {
    state.calendarMonth = new Date(state.calendarMonth.getFullYear(), state.calendarMonth.getMonth() + 1, 1);
    render();
  });
  document.querySelector("#cal-today").addEventListener("click", () => {
    const now = new Date();
    state.calendarMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    render();
  });
}

async function init() {
  wireSubscribeLinks();

  const [conferences, topics] = await Promise.all([
    fetch("conferences.json").then((r) => r.json()),
    fetch("topics.json").then((r) => r.json()),
  ]);
  state.conferences = conferences;
  state.topics = topics;

  renderChips();
  render();
  renderChangelog();
  wireViewToggle();

  document.querySelector("#search").addEventListener("input", (e) => {
    state.search = e.target.value;
    render();
  });
  document.querySelector("#sort-by").addEventListener("change", (e) => {
    state.sortBy = e.target.value;
    render();
  });
}

init();
