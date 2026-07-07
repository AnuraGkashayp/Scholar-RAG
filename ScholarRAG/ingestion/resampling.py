import json
import math
from pathlib import Path
from collections import defaultdict



ENRICHED_FILE = Path("ingestion/papers_enriched.json")
OUTPUT_FILE   = Path("ingestion/papers_final.json")

PWC_TARGET = 12_000

PWC_AREA_QUOTAS = {
    "general":       3720,
    "vision":        3120,
    "language":      2400,
    "video":          960,
    "audio":          720,
    "other":          600,
    "miscellaneous":  480,
}

def quality_score(p: dict) -> float:
    citations  = p.get("citations", 0) or 0
    stars      = p.get("max_stars", 0) or 0
    num_repos  = p.get("num_repos", 0) or 0
    is_off     = p.get("is_official", False)
    has_code   = p.get("has_code", False)

    score  = math.log(citations + 1) * 2.0
    score += math.log(stars + 1)     * 1.5
    score += math.log(num_repos + 1) * 0.5
    score += 2.0 if is_off  else 0.0
    score += 1.0 if has_code else 0.0
    return score


def sample_pwc(papers: list) -> list:
    print(f"  PWC pool: {len(papers):,} papers")

    by_area: dict[str, list] = defaultdict(list)
    for p in papers:
        area = p.get("category", "miscellaneous")
        if area not in PWC_AREA_QUOTAS:
            area = "miscellaneous"
        by_area[area].append(p)

    selected = []
    for area, quota in PWC_AREA_QUOTAS.items():
        pool   = by_area.get(area, [])
        ranked = sorted(pool, key=quality_score, reverse=True)
        chosen = ranked[:quota]
        selected.extend(chosen)
        print(f"    {area:<16} pool={len(pool):>6,}  selected={len(chosen):>5,}")

    print(f"  PWC selected: {len(selected):,}\n")
    return selected


def main():
    print(f"Loading {ENRICHED_FILE} ...")
    with open(ENRICHED_FILE, encoding="utf-8") as f:
        all_papers: list = json.load(f)
    print(f"  {len(all_papers):,} total papers loaded\n")

    pwc_papers = [p for p in all_papers if p.get("source") == "pwc"]
    oa_papers  = [p for p in all_papers if p.get("source") == "openalex"]
    print(f"  PWC: {len(pwc_papers):,}  |  OpenAlex: {len(oa_papers):,}\n")

    print("[Sampling] Selecting best PWC papers ...")
    pwc_final = sample_pwc(pwc_papers)

    final = pwc_final + oa_papers

    code_c = sum(1 for p in final if p.get("has_code"))
    cit_c  = sum(1 for p in final if p.get("citations", 0) > 0)
    avg_score_pwc = (
        sum(quality_score(p) for p in pwc_final) / len(pwc_final)
        if pwc_final else 0
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"DONE — {len(final):,} papers → {OUTPUT_FILE}")
    print(f"  PWC (sampled)   : {len(pwc_final):,}")
    print(f"  OpenAlex (all)  : {len(oa_papers):,}")
    print(f"  With GitHub     : {code_c:,}")
    print(f"  With citations  : {cit_c:,}")
    print(f"  Avg PWC score   : {avg_score_pwc:.3f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
