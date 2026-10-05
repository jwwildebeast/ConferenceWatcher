"""Generate subscribable .ics feeds -- one VEVENT per deadline (not per
conference), so a calendar app shows "NeurIPS 2025 -- Paper Deadline" etc.
directly on the day it's due.
"""
from datetime import datetime, timedelta, timezone

from icalendar import Calendar, Event

from common import DOCS_DIR, WATCHLIST_YAML, load_json, load_yaml, CONFERENCES_JSON

DEADLINE_LABELS = {
    "abstract": "Abstract Deadline",
    "paper": "Paper Deadline",
    "notification": "Notification",
    "camera_ready": "Camera-Ready Deadline",
    "supplementary": "Supplementary Material Deadline",
    "rebuttal_start": "Author Feedback Window Opens",
    "rebuttal_end": "Author Feedback Window Closes",
    "deadline": "Deadline",
}

MIN_SCORE_ALL_FEED = 0  # keep everything; the site/UI is where real filtering happens
PAST_DEADLINE_GRACE = timedelta(days=2)  # keep a just-passed deadline briefly, drop older ones


def _deadline_summary(record: dict, deadline: dict) -> str:
    label = deadline.get("label") or DEADLINE_LABELS.get(deadline["type"], deadline["type"].title())
    return f"{record['title']} {record['year']} — {label}"


def _add_event(cal: Calendar, record: dict, deadline: dict) -> None:
    event = Event()
    when = datetime.fromisoformat(deadline["when"])
    event.add("uid", f"{record['id']}-{deadline['type']}@conferencewatcher")
    event.add("summary", _deadline_summary(record, deadline))
    event.add("dtstart", when)
    event.add("dtend", when)
    event.add("dtstamp", when)
    score = (record.get("reputation") or {}).get("score")
    desc_lines = []
    if record.get("link"):
        desc_lines.append(f"Conference site: {record['link']}")
    if score is not None:
        desc_lines.append(f"Reputation score: {score}/100")
    if record.get("topics"):
        desc_lines.append("Topics: " + ", ".join(record["topics"]))
    event.add("description", "\n".join(desc_lines))
    if record.get("place"):
        event.add("location", record["place"])
    cal.add_component(event)


def build_calendar(records: list[dict], calendar_name: str) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//ConferenceWatcher//conferencewatcher//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", calendar_name)
    cal.add("x-wr-timezone", "UTC")
    cutoff = datetime.now(timezone.utc) - PAST_DEADLINE_GRACE
    for record in records:
        for deadline in record.get("deadlines") or []:
            if not deadline.get("when"):
                continue
            if datetime.fromisoformat(deadline["when"]) < cutoff:
                continue
            _add_event(cal, record, deadline)
    return cal


def matches_watchlist(record: dict, watchlist: dict) -> bool:
    wl_topics = {t.lower() for t in watchlist.get("topics") or []}
    wl_conferences = {c.lower() for c in watchlist.get("conferences") or []}
    record_topics = {t.lower() for t in record.get("topics") or []}
    if record_topics & wl_topics:
        return True
    title = (record.get("title") or "").lower()
    full_name = (record.get("full_name") or "").lower()
    return any(c in title or c in full_name or title in c for c in wl_conferences)


def write_feeds(records: list[dict] | None = None) -> None:
    records = records if records is not None else load_json(CONFERENCES_JSON, default=[])
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    all_records = [
        r for r in records if (r.get("reputation") or {}).get("score", 0) >= MIN_SCORE_ALL_FEED
    ]
    all_cal = build_calendar(all_records, "ConferenceWatcher -- All Tracked Deadlines")
    (DOCS_DIR / "calendar-all.ics").write_bytes(all_cal.to_ical())

    watchlist = load_yaml(WATCHLIST_YAML) or {}
    watch_records = [r for r in records if matches_watchlist(r, watchlist)]
    watch_cal = build_calendar(watch_records, "ConferenceWatcher -- My Watchlist")
    (DOCS_DIR / "calendar-watchlist.ics").write_bytes(watch_cal.to_ical())

    print(f"wrote calendar-all.ics ({len(all_records)} conferences)")
    print(f"wrote calendar-watchlist.ics ({len(watch_records)} conferences)")


if __name__ == "__main__":
    write_feeds()
