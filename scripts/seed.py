"""Load the curated seed conference list (IE/OR/simulation venues not covered
by any CS/AI aggregator) into the same per-year record shape used elsewhere.
"""
from common import SEED_YAML, load_yaml, normalize_tag, parse_when


def load_seed_records() -> list[dict]:
    conferences = load_yaml(SEED_YAML) or []
    records = []
    for conf in conferences:
        base_tags = [normalize_tag(t) for t in conf.get("tags", [])]
        for inst in conf.get("instances") or []:
            deadlines = []
            for d in inst.get("deadlines") or []:
                when = parse_when(
                    d["when"].replace("T", " ") if "when" in d else None,
                    d.get("timezone"),
                )
                if when:
                    deadlines.append(
                        {
                            "type": d.get("type", "deadline"),
                            "label": d.get("label"),
                            "when": when,
                            "timezone_source": d.get("timezone"),
                        }
                    )
            deadlines.sort(key=lambda d: d["when"])
            records.append(
                {
                    "id": f"{conf['id']}-{inst['year']}",
                    "title": conf["title"],
                    "full_name": conf.get("full_name"),
                    "year": inst["year"],
                    "link": conf.get("link"),
                    "place": inst.get("place"),
                    "date": {
                        "start": str(inst.get("date", {}).get("start") or "") or None,
                        "end": str(inst.get("date", {}).get("end") or "") or None,
                    },
                    "deadlines": deadlines,
                    "tags": base_tags,
                    "sources": ["seed"],
                    "basis": "manual",
                    "seed_id": conf["id"],
                    "sponsor": conf.get("sponsor"),
                    "years_running": conf.get("years_running"),
                    "manual_base_score": conf.get("manual_base_score"),
                    "score_rationale": conf.get("score_rationale"),
                    "scrape_url": (conf.get("scrape") or {}).get("url"),
                }
            )
    return records


def load_seed_conferences_raw() -> list[dict]:
    """The unflattened seed list, keyed by conference (not by year) --
    used by scrape_seed.py which checks one URL per conference, not per year."""
    return load_yaml(SEED_YAML) or []


if __name__ == "__main__":
    recs = load_seed_records()
    print(f"loaded {len(recs)} seed conference-year records")
