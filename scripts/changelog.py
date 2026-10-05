"""Diff the previous conferences.json against the new one and append
structured change records -- this is what makes "deadlines changed, and the
change is recorded" true, independent of git history."""
import json

from common import CHANGELOG_JSONL, utcnow_iso


def _index_by_id(records: list[dict]) -> dict:
    return {r["id"]: r for r in records}


def _deadlines_by_type(record: dict) -> dict:
    return {d["type"]: d["when"] for d in record.get("deadlines") or []}


def diff_records(old_records: list[dict], new_records: list[dict]) -> list[dict]:
    old_by_id = _index_by_id(old_records)
    new_by_id = _index_by_id(new_records)
    changes = []

    for conf_id, new_rec in new_by_id.items():
        label = f"{new_rec['title']} {new_rec['year']}"
        old_rec = old_by_id.get(conf_id)

        if old_rec is None:
            changes.append({"event": "added", "conference_id": conf_id, "conference": label})
            continue

        old_deadlines = _deadlines_by_type(old_rec)
        new_deadlines = _deadlines_by_type(new_rec)
        for dtype, new_when in new_deadlines.items():
            old_when = old_deadlines.get(dtype)
            if old_when and old_when != new_when:
                changes.append(
                    {
                        "event": "deadline_changed",
                        "conference_id": conf_id,
                        "conference": label,
                        "deadline_type": dtype,
                        "old": old_when,
                        "new": new_when,
                    }
                )
            elif old_when is None:
                changes.append(
                    {
                        "event": "deadline_added",
                        "conference_id": conf_id,
                        "conference": label,
                        "deadline_type": dtype,
                        "new": new_when,
                    }
                )

        old_score = (old_rec.get("reputation") or {}).get("score")
        new_score = (new_rec.get("reputation") or {}).get("score")
        if old_score is not None and old_score != new_score:
            changes.append(
                {
                    "event": "score_changed",
                    "conference_id": conf_id,
                    "conference": label,
                    "old": old_score,
                    "new": new_score,
                }
            )

    for conf_id, old_rec in old_by_id.items():
        if conf_id not in new_by_id:
            changes.append(
                {
                    "event": "removed",
                    "conference_id": conf_id,
                    "conference": f"{old_rec['title']} {old_rec['year']}",
                }
            )

    return changes


def append_changelog(changes: list[dict], seed_page_flags: list[dict] | None = None) -> int:
    """Appends every change (plus any flagged-for-review seed pages) as its
    own JSON line, timestamped. Returns the number of lines written."""
    entries = []
    now = utcnow_iso()
    for change in changes:
        entries.append({"timestamp": now, **change})
    for flag in seed_page_flags or []:
        if flag.get("changed"):
            entries.append(
                {
                    "timestamp": now,
                    "event": "seed_page_changed",
                    "conference_id": flag["seed_id"],
                    "conference": flag["title"],
                    "url": flag["url"],
                    "note": "page text changed -- verify deadlines by hand in seed_conferences.yml",
                }
            )

    if entries:
        CHANGELOG_JSONL.parent.mkdir(parents=True, exist_ok=True)
        with open(CHANGELOG_JSONL, "a", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return len(entries)


def read_recent_changes(limit: int = 50) -> list[dict]:
    if not CHANGELOG_JSONL.exists():
        return []
    with open(CHANGELOG_JSONL, "r", encoding="utf-8") as fh:
        lines = [json.loads(line) for line in fh if line.strip()]
    return lines[-limit:][::-1]
