"""Entry point: fetch -> merge -> score -> diff/changelog -> write outputs.
Run locally with `python scripts/pipeline.py`; CI runs the same thing via
.github/workflows/update.yml.
"""
import build_ics
import build_site_data
import scrape_seed
from changelog import append_changelog, diff_records
from common import CONFERENCES_JSON, load_json, save_json
from merge import build_merged_records


def run() -> None:
    old_records = load_json(CONFERENCES_JSON, default=[])

    print("fetching + merging...")
    new_records = build_merged_records()

    print("checking seed conference pages for changes...")
    seed_flags = scrape_seed.check_seed_pages()

    print("diffing against previous run...")
    changes = diff_records(old_records, new_records)
    n_logged = append_changelog(changes, seed_flags)

    save_json(CONFERENCES_JSON, new_records)
    build_site_data.build()
    build_ics.write_feeds(new_records)

    print(f"done. {len(new_records)} conference-year records tracked.")
    print(f"{n_logged} changelog entries written this run.")
    if changes:
        for c in changes[:20]:
            print(" -", c["event"], c.get("conference"), c.get("old"), "->", c.get("new"))


if __name__ == "__main__":
    run()
