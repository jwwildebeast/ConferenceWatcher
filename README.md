# ConferenceWatcher

Automatically tracks conference submission deadlines across industrial &
systems engineering, computer science, and AI — scored by reputation,
refreshed on a schedule, with every change recorded. Published as a static
site with subscribable `.ics` calendar feeds.

## How it works

- **Data sources**
  - [`huggingface/ai-deadlines`](https://github.com/huggingface/ai-deadlines) — actively-maintained, community-curated CS/AI conference deadlines, with CORE/CCF rank and h-index already attached per conference.
  - `data/seed_conferences.yml` — hand-curated industrial/systems engineering & OR conferences (IISE, MARCON, INFORMS, WSC, POMS, IEEE CASE) that no aggregator covers. Their deadlines are entered by hand; `scrape_seed.py` just flags when a conference's page text has changed so you know to go check it.
- **Topic tracking**: `data/topic_map.yml` maps plain-English topics (from `topics_domains_fields.txt`) to the underlying tag vocabulary, so you track "machine learning" or "industrial and systems engineering" instead of memorizing acronyms. You can also track specific conferences by name directly in `watchlist.yml`.
- **Reputation score (0-100)**: computed from CORE/CCF rank + h-index for aggregator conferences; a transparent manually-curated base score (+ small years-running bonus) for seed conferences. Every score keeps a `signals` breakdown in `data/conferences.json` — never a black box.
- **Change tracking**: every pipeline run diffs the new dataset against the previous one and appends structured entries to `data/changelog.jsonl` (deadline moved, conference added/removed, score changed). Git history is a second, full audit trail on top of that.
- **Automation**: `.github/workflows/update.yml` runs the pipeline daily (and on manual trigger), commits any changes, and — once GitHub Pages is enabled — that push republishes the site automatically.

## Repo layout

```
data/conferences.json        canonical merged + scored dataset (source of truth)
data/seed_conferences.yml    curated IE/OR/simulation conferences + manual scores
data/topic_map.yml           topic -> tag/seed_id mapping
data/changelog.jsonl         append-only structured change log
watchlist.yml                your topics + specific conferences to track
scripts/pipeline.py          run the whole thing: fetch -> merge -> score -> diff -> write
docs/                        GitHub Pages site root (index.html, calendar-*.ics, conferences.json)
```

## Running locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/pipeline.py
python -m http.server 8000 --directory docs   # then open http://localhost:8000
```

## Adjusting what you track

- **Add/remove a topic or widen one**: edit `data/topic_map.yml`.
- **Add a conference not covered by the aggregator**: add an entry to `data/seed_conferences.yml`, including your own `manual_base_score` and a one-line `score_rationale`.
- **Change your personal calendar feed**: edit `watchlist.yml` (topics and/or conference name substrings) — `docs/calendar-watchlist.ics` picks it up on the next pipeline run.

## One-time setup to publish

1. Create a GitHub repo and push this project to it.
2. In the repo's Settings → Pages, set the source to the `main` branch, `/docs` folder.
3. Your site will be at `https://<user>.github.io/<repo>/`, and the feeds are subscribable via `webcal://<user>.github.io/<repo>/calendar-watchlist.ics` (Google Calendar: "Other calendars" → "From URL"; Outlook: "Add calendar" → "Subscribe from web").
