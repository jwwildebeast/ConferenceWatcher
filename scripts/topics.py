"""Expand a record's tags/seed_id into the plain-English topics it matches,
using data/topic_map.yml so the acronym soup never has to be user-facing.
"""
from common import TOPIC_MAP_YAML, load_yaml


def load_topic_map() -> dict:
    return load_yaml(TOPIC_MAP_YAML) or {}


def topics_for_record(record: dict, topic_map: dict | None = None) -> list[str]:
    topic_map = topic_map if topic_map is not None else load_topic_map()
    record_tags = set(record.get("tags") or [])
    seed_id = record.get("seed_id")
    matched = []
    for topic, rule in topic_map.items():
        rule_tags = set(rule.get("tags") or [])
        rule_seed_ids = set(rule.get("seed_ids") or [])
        if (rule_tags & record_tags) or (seed_id and seed_id in rule_seed_ids):
            matched.append(topic)
    return matched


def expand_topics_to_filter(selected_topics: list[str], topic_map: dict | None = None) -> tuple[set, set]:
    """User-facing topics -> (tag set, seed_id set) to filter records by."""
    topic_map = topic_map if topic_map is not None else load_topic_map()
    tags, seed_ids = set(), set()
    for topic in selected_topics:
        rule = topic_map.get(topic, {})
        tags.update(rule.get("tags") or [])
        seed_ids.update(rule.get("seed_ids") or [])
    return tags, seed_ids
