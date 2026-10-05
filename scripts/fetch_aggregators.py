"""Pull conference/deadline data from the huggingface/ai-deadlines aggregator.

That repo is an actively-maintained, community-curated dataset (one YAML file
per conference, one entry per year) covering CS/AI venues, each already
carrying a CORE/CCF/THCPL ranking string and a Google Scholar h-index. We
treat it as a read-only upstream source: never edited here, just normalized
into our own schema.
"""
import sys
import time

import requests
import yaml

from common import normalize_tag, parse_when

TREE_API = "https://api.github.com/repos/huggingface/ai-deadlines/git/trees/main?recursive=1"
RAW_BASE = "https://raw.githubusercontent.com/huggingface/ai-deadlines/main/"
DATA_PREFIX = "src/data/conferences/"
SOURCE_NAME = "ai-deadlines"

HEADERS = {"User-Agent": "ConferenceWatcher/1.0 (+https://github.com/)"}


def list_conference_files() -> list[str]:
    resp = requests.get(TREE_API, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    tree = resp.json().get("tree", [])
    return [
        t["path"]
        for t in tree
        if t["path"].startswith(DATA_PREFIX) and t["path"].endswith(".yml")
    ]


def fetch_raw_yaml(path: str):
    resp = requests.get(RAW_BASE + path, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return yaml.safe_load(resp.text) or []


def _parse_rankings(rankings_raw: str | None) -> dict:
    """'CCF: A, CORE: A*, THCPL: A' -> {'ccf': 'A', 'core': 'A*', 'thcpl': 'A'}"""
    out = {}
    if not rankings_raw:
        return out
    for part in rankings_raw.split(","):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip().lower()] = v.strip()
    return out


def _normalize_deadlines(entry: dict) -> list[dict]:
    deadlines = []
    for d in entry.get("deadlines") or []:
        when = parse_when(d.get("date"), d.get("timezone"))
        if when is None:
            continue
        deadlines.append(
            {
                "type": d.get("type") or "deadline",
                "label": d.get("label"),
                "when": when,
                "timezone_source": d.get("timezone"),
            }
        )
    # Legacy flat-field fallback, in case any file still uses the older shape.
    if not deadlines:
        for field, dtype in (("abstract_deadline", "abstract"), ("deadline", "paper")):
            when = parse_when(entry.get(field), entry.get("timezone"))
            if when:
                deadlines.append(
                    {"type": dtype, "label": None, "when": when, "timezone_source": entry.get("timezone")}
                )
    deadlines.sort(key=lambda d: d["when"])
    return deadlines


def normalize_entry(entry: dict) -> dict | None:
    year = entry.get("year")
    title = entry.get("title")
    if not title or not year:
        return None
    place = entry.get("place") or ", ".join(
        p for p in (entry.get("city"), entry.get("country")) if p
    ) or entry.get("venue")

    return {
        "id": entry.get("id") or f"{normalize_tag(title)}{year}",
        "title": title,
        "full_name": entry.get("full_name"),
        "year": year,
        "link": entry.get("link"),
        "place": place,
        "date": {
            "start": str(entry.get("start")) if entry.get("start") else None,
            "end": str(entry.get("end")) if entry.get("end") else None,
        },
        "deadlines": _normalize_deadlines(entry),
        "tags": sorted({normalize_tag(t) for t in (entry.get("tags") or [])}),
        "sources": [SOURCE_NAME],
        "basis": "computed",
        "rankings": _parse_rankings(entry.get("rankings")),
        "hindex": entry.get("hindex"),
        "note": entry.get("note"),
    }


def fetch_all(sleep_between: float = 0.0) -> list[dict]:
    records = []
    for path in list_conference_files():
        try:
            raw_entries = fetch_raw_yaml(path)
        except (requests.RequestException, yaml.YAMLError) as exc:
            print(f"warning: failed to fetch/parse {path}: {exc}", file=sys.stderr)
            continue
        for entry in raw_entries:
            norm = normalize_entry(entry)
            if norm:
                records.append(norm)
        if sleep_between:
            time.sleep(sleep_between)
    return records


if __name__ == "__main__":
    recs = fetch_all()
    print(f"fetched {len(recs)} conference-year records from {SOURCE_NAME}")
