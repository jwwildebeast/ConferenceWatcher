const state = {
  conferences: [],
  topics: [],
  activeTopics: new Set(),
  search: "",
  sortBy: "deadline",
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

function wireSubscribeLinks() {
  const base = window.location.href.replace(/[^/]*$/, "");
  const webcalBase = base.replace(/^https?:/, "webcal:");
  document.querySelector("#sub-watchlist").href = webcalBase + "calendar-watchlist.ics";
  document.querySelector("#sub-all").href = webcalBase + "calendar-all.ics";
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
