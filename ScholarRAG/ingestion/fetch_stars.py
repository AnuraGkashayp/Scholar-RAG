import json
import sys
import time
import requests
import ijson
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / "backend" / ".env")

GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
ENRICHED_FILE  = Path("ingestion/papers_enriched.json")
TMP_FILE       = Path("ingestion/papers_enriched.tmp.json")
STARS_CACHE    = Path("ingestion/github_stars.json")
GRAPHQL_URL    = "https://api.github.com/graphql"
BATCH_SIZE     = 100


def parse_repo(url: str) -> tuple[str, str] | tuple[None, None]:
    url   = url.rstrip("/")
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None


def fetch_stars_batch(repos: list[tuple[str, str, str]]) -> dict[str, int]:
    aliases = []
    for i, (owner, name, _) in enumerate(repos):
        aliases.append(
            f'r{i}: repository(owner: "{owner}", name: "{name}") {{ stargazerCount }}'
        )
    query   = "{ " + " ".join(aliases) + " }"
    headers = {
        "Authorization": f"bearer {GITHUB_TOKEN}",
        "Content-Type":  "application/json",
    }
    try:
        r = requests.post(GRAPHQL_URL, json={"query": query}, headers=headers, timeout=30)
        if r.status_code == 200:
            data   = r.json().get("data") or {}
            result = {}
            for i, (_, _, url) in enumerate(repos):
                node = data.get(f"r{i}")
                if node:
                    result[url] = node.get("stargazerCount", 0)
            return result
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 60))
            print(f"  Rate limited — sleeping {wait}s")
            time.sleep(wait)
    except Exception as e:
        print(f"  Error: {e}")
    return {}


def apply_cache(stars_cache: dict):
    print("Applying cached star counts to papers ...")
    updated = 0
    total_p = 0
    with open(ENRICHED_FILE, "rb") as fin, open(TMP_FILE, "w", encoding="utf-8") as fout:
        fout.write("[")
        first = True
        for p in ijson.items(fin, "item"):
            repos = p.get("github_repos") or []
            if repos:
                p["repo_stars"] = [stars_cache.get(url, 0) for url in repos]
                p["max_stars"]  = max(p["repo_stars"], default=0)
                updated += 1
            if not first:
                fout.write(",\n")
            fout.write(json.dumps(p, ensure_ascii=False))
            first = False
            total_p += 1
            if total_p % 100_000 == 0:
                print(f"  {total_p:,} processed | {updated:,} updated", flush=True)
        fout.write("\n]")
    TMP_FILE.replace(ENRICHED_FILE)
    print(f"  Updated {updated:,} papers with repo_stars + max_stars → {ENRICHED_FILE}")


def main():
    apply_only = "--cache" in sys.argv

    if not apply_only and not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN not set in .env")
        return

    stars_cache: dict = {}
    if STARS_CACHE.exists():
        with open(STARS_CACHE, encoding="utf-8") as f:
            stars_cache = json.load(f)
        print(f"  {len(stars_cache):,} star counts already cached")

    if apply_only:
        apply_cache(stars_cache)
        return

    # Pass 1: stream to collect unique uncached repo URLs
    print(f"Pass 1: collecting repo URLs from {ENRICHED_FILE} ...")
    unique_repos: dict[str, tuple[str, str, str]] = {}
    with open(ENRICHED_FILE, "rb") as f:
        for p in ijson.items(f, "item"):
            for url in (p.get("github_repos") or []):
                if "github.com" not in url or url in stars_cache:
                    continue
                owner, name = parse_repo(url)
                if owner and name:
                    unique_repos[url] = (owner, name, url)
    print(f"  {len(unique_repos):,} repos to fetch (uncached)\n")

    # Fetch star counts
    repo_list = list(unique_repos.values())
    total     = len(repo_list)
    fetched   = 0

    for i in range(0, total, BATCH_SIZE):
        batch  = repo_list[i:i + BATCH_SIZE]
        result = fetch_stars_batch(batch)
        stars_cache.update(result)
        fetched += len(result)

        if (i // BATCH_SIZE) % 50 == 0:
            print(f"  ... {min(i + BATCH_SIZE, total):,}/{total:,} | {fetched:,} fetched", flush=True)
            with open(STARS_CACHE, "w", encoding="utf-8") as f:
                json.dump(stars_cache, f)

        time.sleep(0.72)

    with open(STARS_CACHE, "w", encoding="utf-8") as f:
        json.dump(stars_cache, f)
    print(f"  Stars fetched: {fetched:,} repos cached\n")

    # Pass 2: stream to apply max_stars and write to tmp file
    print("Pass 2: applying star counts to papers ...")
    updated = 0
    total_p = 0
    with open(ENRICHED_FILE, "rb") as fin, open(TMP_FILE, "w", encoding="utf-8") as fout:
        fout.write("[")
        first = True
        for p in ijson.items(fin, "item"):
            repos = p.get("github_repos") or []
            if repos:
                p["repo_stars"] = [stars_cache.get(url, 0) for url in repos]
                p["max_stars"]  = max(p["repo_stars"], default=0)
                updated += 1
            if not first:
                fout.write(",\n")
            fout.write(json.dumps(p, ensure_ascii=False))
            first = False
            total_p += 1
            if total_p % 50_000 == 0:
                print(f"  {total_p:,} papers processed | {updated:,} updated", flush=True)
        fout.write("\n]")

    TMP_FILE.replace(ENRICHED_FILE)
    print(f"  Updated {updated:,} papers with max_stars")
    print(f"  Saved → {ENRICHED_FILE}")
    print("Done.")


if __name__ == "__main__":
    main()
