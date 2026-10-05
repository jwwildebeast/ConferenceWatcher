"""Copy the canonical dataset (+ recent changelog) into docs/ so the static
site's client-side JS can fetch it directly (no backend, same-origin)."""
import shutil

from changelog import read_recent_changes
from common import CONFERENCES_JSON, DOCS_DIR, save_json
from topics import load_topic_map


def build() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CONFERENCES_JSON, DOCS_DIR / "conferences.json")
    save_json(DOCS_DIR / "changelog.json", read_recent_changes(limit=200))
    save_json(DOCS_DIR / "topics.json", sorted(load_topic_map().keys()))


if __name__ == "__main__":
    build()
    print(f"copied {CONFERENCES_JSON} -> {DOCS_DIR / 'conferences.json'}")
    print(f"wrote {DOCS_DIR / 'changelog.json'}")
