"""Shared helpers for the ConferenceWatcher pipeline."""
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml
from dateutil import tz as dateutil_tz

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"

CONFERENCES_JSON = DATA_DIR / "conferences.json"
CHANGELOG_JSONL = DATA_DIR / "changelog.jsonl"
SEED_YAML = DATA_DIR / "seed_conferences.yml"
TOPIC_MAP_YAML = DATA_DIR / "topic_map.yml"
WATCHLIST_YAML = REPO_ROOT / "watchlist.yml"

# Fixed-offset / named aliases seen in deadline data that dateutil doesn't
# resolve on its own.
_TZ_ALIASES = {
    "AOE": timezone(timedelta(hours=-12)),   # Anywhere on Earth
    "UTC-12": timezone(timedelta(hours=-12)),
    "UTC-11": timezone(timedelta(hours=-11)),
    "GMT": timezone.utc,
    "UTC": timezone.utc,
}


def normalize_tag(tag: str) -> str:
    return re.sub(r"[\s_]+", "-", tag.strip().lower())


def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=False, ensure_ascii=False)
        fh.write("\n")


def resolve_tzinfo(tz_name: str | None):
    """Best-effort tz string -> tzinfo. Falls back to UTC when unknown."""
    if not tz_name:
        return timezone.utc
    key = tz_name.strip().upper()
    if key in _TZ_ALIASES:
        return _TZ_ALIASES[key]
    tzi = dateutil_tz.gettz(tz_name)
    return tzi if tzi is not None else timezone.utc


def parse_when(date_str: str, tz_name: str | None) -> str | None:
    """Parse a naive 'YYYY-MM-DD HH:MM:SS' + tz string into an ISO-8601 UTC string."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            naive = datetime.strptime(date_str.strip(), fmt)
            break
        except ValueError:
            continue
    else:
        return None
    aware = naive.replace(tzinfo=resolve_tzinfo(tz_name))
    return aware.astimezone(timezone.utc).isoformat()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
