import json
import sys
import time
import ijson
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / "backend" / ".env")

ENRICHED_FILE = Path("ingestion/papers_enriched.json")
TMP_FILE      = Path("ingestion/papers_enriched.tmp.json")
STARS_CACHE   = Path("ingestion/github_stars.json")
CIT_CACHE     = Path("ingestion/citations_cache.json")

S2_BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
S2_FIELDS    = "citationCount"
S2_SLEEP     = 10
BATCH_SIZE   = 500

test = "--test" in sys.argv


def fetch_new_citations(cit_cache: dict) -> dict:
    s2_key     = os.getenv("S2_API_KEY", "")
    s2_headers = {"x-api-key": s2_key} if s2_key else {}
    print(f"[Citations] S2 key: {'SET' if s2_key else 'MISSING'}")

    # Collect papers without citations
    keys_needed = []
    print("[Citations] Scanning papers_enriched.json for uncited papers ...")
    with open(ENRICHED_FILE, "rb") as f:
        for p in ijson.items(f, "item"):
            if p.get("source") == "openalex":
                continue
            if p.get("citations", 0) > 0:
                continue
            doi      = (p.get("doi") or "").strip()
            arxiv_id = (p.get("arxiv_id") or "").strip()
            key = f"DOI:{doi}" if doi else (f"arXiv:{arxiv_id}" if arxiv_id else None)
            if key and key not in cit_cache:
                keys_needed.append(key)

    if test:
        keys_needed = keys_needed[:1000]

    total    = len(keys_needed)
    enriched = 0
    print(f"[Citations] {len(cit_cache):,} cached | {total:,} to fetch")

    for i in range(0, total, BATCH_SIZE):
        batch = keys_needed[i:i + BATCH_SIZE]
        while True:
            time.sleep(S2_SLEEP)
            try:
                r = requests.post(
                    S2_BATCH_URL,
                    headers={**s2_headers, "Content-Type": "application/json"},
                    params={"fields": S2_FIELDS},
                    json={"ids": batch},
                    timeout=30,
                )
            except Exception as e:
                print(f"[Citations] request error: {e}")
                break
            if r.status_code == 429:
                print(f"[Citations] rate limited — sleeping 60s")
                time.sleep(60)
                continue
            if r.status_code != 200:
                print(f"[Citations] S2 error {r.status_code}: {r.text[:200]}")
                break
            for j, item in enumerate(r.json()):
                if not item or "citationCount" not in item:
                    continue
                cit_cache[batch[j]] = item["citationCount"]
                enriched += 1
            break

        if (i // BATCH_SIZE + 1) % 10 == 0:
            print(f"  {i + len(batch):,}/{total:,} processed | {enriched:,} enriched", flush=True)

    with open(CIT_CACHE, "w", encoding="utf-8") as f:
        json.dump(cit_cache, f)
    print(f"[Citations] done — {enriched:,}/{total:,} enriched, cache saved")
    return cit_cache


def apply_all(stars_cache: dict, cit_cache: dict):
    print("Applying stars + citations to papers_enriched.json ...")
    updated_stars = 0
    updated_cit   = 0
    total         = 0

    with open(ENRICHED_FILE, "rb") as fin, open(TMP_FILE, "w", encoding="utf-8") as fout:
        fout.write("[")
        first = True
        for p in ijson.items(fin, "item"):
            # Apply stars
            repos = p.get("github_repos") or []
            if repos:
                p["repo_stars"] = [stars_cache.get(url, 0) for url in repos]
                p["max_stars"]  = max(p["repo_stars"], default=0)
                if p["max_stars"] > 0:
                    updated_stars += 1

            # Apply citations
            if p.get("citations", 0) == 0 and p.get("source") != "openalex":
                doi      = (p.get("doi") or "").strip()
                arxiv_id = (p.get("arxiv_id") or "").strip()
                key = f"DOI:{doi}" if doi else (f"arXiv:{arxiv_id}" if arxiv_id else None)
                if key and key in cit_cache:
                    p["citations"] = cit_cache[key]
                    updated_cit += 1

            if not first:
                fout.write(",\n")
            fout.write(json.dumps(p, ensure_ascii=False))
            first = False
            total += 1
            if total % 100_000 == 0:
                print(f"  {total:,} processed | stars={updated_stars:,} citations={updated_cit:,}", flush=True)
        fout.write("\n]")

    TMP_FILE.replace(ENRICHED_FILE)
    print(f"Done — {total:,} papers")
    print(f"  Stars updated   : {updated_stars:,}")
    print(f"  Citations added : {updated_cit:,}")


def main():
    stars_cache = {}
    if STARS_CACHE.exists():
        with open(STARS_CACHE, encoding="utf-8") as f:
            stars_cache = json.load(f)
        print(f"[Stars] {len(stars_cache):,} cached repo star counts")

    cit_cache = {}
    if CIT_CACHE.exists():
        with open(CIT_CACHE, encoding="utf-8") as f:
            cit_cache = json.load(f)
        print(f"[Citations] {len(cit_cache):,} cached citation counts")

    cit_cache = fetch_new_citations(cit_cache)
    apply_all(stars_cache, cit_cache)


if __name__ == "__main__":
    main()
