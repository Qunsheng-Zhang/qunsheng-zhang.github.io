#!/usr/bin/env python3
"""Generate the public GitHub contribution feed for the homepage.

The workflow runs this script with GITHUB_TOKEN, then commits the JSON file if
its contents changed. The page fetches the file and renders a compact live list;
the curated thematic cards in opensource.html remain manually maintained.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER = "Qunsheng-Zhang"
API = "https://api.github.com"
OUT = Path(__file__).resolve().parent.parent / "data" / "github-contributions.json"
MAX_ITEMS = 20

# Repositories with a dedicated theme section on opensource.html. Add future
# control or quantitative repositories here; unknown repositories use "other".
THEME_BY_REPO = {
    "google-deepmind/formal-conjectures": "formal-proof",
    "morluto/jacobian": "verifiable-software",
}


def api_get(url: str, token: str | None) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-homepage",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    query = urllib.parse.quote(f"author:{USER} type:pr")
    base_url = f"{API}/search/issues?q={query}&sort=updated&order=desc&per_page=100"

    raw_items: list[dict] = []
    total_count = 0
    page = 1
    while True:
        data = api_get(f"{base_url}&page={page}", token)
        total_count = int(data.get("total_count", 0))
        page_items = data.get("items", [])
        raw_items.extend(page_items)
        if len(raw_items) >= min(total_count, 500) or len(page_items) < 100:
            break
        page += 1

    records: list[dict] = []
    for item in raw_items:
        pull_request = item.get("pull_request")
        if not pull_request:
            continue
        repository_url = item.get("repository_url", "")
        repo = repository_url.split("/repos/", 1)[-1]
        merged_at = pull_request.get("merged_at")
        state = item.get("state")
        if merged_at:
            status = "merged"
        elif state == "open":
            status = "open"
        else:
            status = "closed"
        records.append(
            {
                "number": item.get("number"),
                "title": item.get("title", ""),
                "repo": repo,
                "url": item.get("html_url", ""),
                "state": state,
                "status": status,
                "merged_at": merged_at,
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "labels": [label.get("name", "") for label in item.get("labels", [])],
                "theme": THEME_BY_REPO.get(repo, "other"),
                "own_repo": repo.split("/", 1)[0].lower() == USER.lower(),
            }
        )

    counts = {
        "merged": sum(record["status"] == "merged" for record in records),
        "open": sum(record["status"] == "open" for record in records),
        "closed": sum(record["status"] == "closed" for record in records),
    }
    records.sort(
        key=lambda record: (
            record.get("updated_at") or "",
            record["repo"],
            record["number"] or 0,
        ),
        reverse=True,
    )

    core = {
        "source": "github-search",
        "query": f"author:{USER} type:pr",
        "total_count": total_count,
        "counts": counts,
        "items": records[:MAX_ITEMS],
    }
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Preserve the timestamp when the contribution data itself has not changed,
    # so the daily workflow does not create an empty commit every day.
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None
        if previous and all(previous.get(key) == value for key, value in core.items()):
            generated_at = previous.get("generated_at", generated_at)

    payload = {"generated_at": generated_at, **core}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {OUT} with {len(payload['items'])} of {total_count} pull requests")


if __name__ == "__main__":
    main()
