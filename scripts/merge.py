"""Combine the aggregator feed and the curated seed list into one dataset."""
from common import is_concluded
from fetch_aggregators import fetch_all
from score import apply_scores
from seed import load_seed_records
from topics import load_topic_map, topics_for_record


def build_merged_records(aggregator_records: list[dict] | None = None) -> list[dict]:
    aggregator_records = (
        aggregator_records if aggregator_records is not None else fetch_all()
    )
    seed_records = load_seed_records()
    records = aggregator_records + seed_records

    # Drop editions that have already concluded -- otherwise every past year
    # an aggregator file has ever listed sticks around forever, cluttering
    # the list view and showing up as "expired" entries on the calendar.
    records = [r for r in records if not is_concluded(r)]

    apply_scores(records)

    topic_map = load_topic_map()
    for record in records:
        record["topics"] = topics_for_record(record, topic_map)

    def sort_key(r: dict):
        upcoming = [d["when"] for d in r.get("deadlines") or [] if d.get("when")]
        return min(upcoming) if upcoming else "9999"

    records.sort(key=sort_key)
    return records


if __name__ == "__main__":
    recs = build_merged_records()
    print(f"merged {len(recs)} total conference-year records")
