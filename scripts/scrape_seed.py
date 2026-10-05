"""Change-detector (not an auto-extractor) for seed conference pages.

IISE/MARCON/etc. pages aren't structured enough to reliably parse a specific
date out of automatically -- getting that wrong is worse than not doing it.
Instead we fetch each seed conference's page, strip it to plain text, and
diff a hash against the last run. A change just gets flagged for you to go
look at and update data/seed_conferences.yml by hand; it never overwrites a
deadline on its own.
"""
import hashlib
import re
import sys

import requests

from common import DATA_DIR, load_json, save_json
from seed import load_seed_conferences_raw

HASH_STATE_PATH = DATA_DIR / "seed_page_hashes.json"
HEADERS = {"User-Agent": "ConferenceWatcher/1.0 (+https://github.com/)"}


def _page_text(html: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def check_seed_pages() -> list[dict]:
    """Returns a list of {seed_id, title, url, changed} for every seed
    conference that has a scrape.url configured."""
    prev_hashes = load_json(HASH_STATE_PATH, default={})
    new_hashes = dict(prev_hashes)
    results = []

    for conf in load_seed_conferences_raw():
        url = (conf.get("scrape") or {}).get("url")
        if not url:
            continue
        seed_id = conf["id"]
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"warning: could not fetch {url} for {seed_id}: {exc}", file=sys.stderr)
            continue

        digest = hashlib.sha256(_page_text(resp.text).encode("utf-8")).hexdigest()
        changed = seed_id in prev_hashes and prev_hashes[seed_id] != digest
        new_hashes[seed_id] = digest
        results.append(
            {"seed_id": seed_id, "title": conf["title"], "url": url, "changed": changed}
        )

    save_json(HASH_STATE_PATH, new_hashes)
    return results


if __name__ == "__main__":
    for r in check_seed_pages():
        flag = "CHANGED - review page" if r["changed"] else "unchanged"
        print(f"{r['title']} ({r['seed_id']}): {flag} -- {r['url']}")
