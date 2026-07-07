import os
import json
import time
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, VectorParams, PointStruct)

_final    = Path("ingestion/papers_final.json")
_enriched = Path("ingestion/papers_enriched.json")
_base     = Path("ingestion/papers.json")
PAPERS_FILE   = _final if _final.exists() else (_enriched if _enriched.exists() else _base)
QDRANT_PATH   = "./qdrant_local"
QDRANT_HOST   = os.environ.get("QDRANT_HOST")
QDRANT_SVC_PORT = int(os.environ.get("QDRANT_SVC_PORT", "6333"))
COLLECTION    = "papers"
MODEL_NAME    = "all-MiniLM-L6-v2"
VECTOR_DIM    = 384
PWC_LIMIT     = 20_000
OA_LIMIT      = 20_000
DEVICE        = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE    = 256 if DEVICE == "cuda" else 64

print(f"Loading papers from {PAPERS_FILE} ...")
with open(PAPERS_FILE, "r", encoding="utf-8") as f:
    all_papers = json.load(f)

pwc_with_code    = [p for p in all_papers if p.get("source") == "pwc" and p.get("has_code")]
pwc_without_code = [p for p in all_papers if p.get("source") == "pwc" and not p.get("has_code")]
oa_papers        = [p for p in all_papers if p.get("source") == "openalex"]

pwc_selected = (pwc_with_code + pwc_without_code)[:PWC_LIMIT]
oa_selected  = oa_papers[:OA_LIMIT]
papers       = pwc_selected + oa_selected

print(f"   PWC papers   : {len(pwc_selected):,} ({sum(1 for p in pwc_selected if p.get('has_code')):,} with code)")
print(f"   OpenAlex     : {len(oa_selected):,}")
print(f"   Total        : {len(papers):,}\n")

print(f"Loading embedding model '{MODEL_NAME}' on {DEVICE.upper()} ...")
model = SentenceTransformer(MODEL_NAME, device=DEVICE)

if QDRANT_HOST:
    print(f"Connecting to Qdrant server at {QDRANT_HOST}:{QDRANT_SVC_PORT} ...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_SVC_PORT)
else:
    print(f"Opening local Qdrant storage at '{QDRANT_PATH}' ...")
    client = QdrantClient(path=QDRANT_PATH)

existing = [c.name for c in client.get_collections().collections]
if COLLECTION in existing:
    print(f"   Collection '{COLLECTION}' already exists — skipping creation.")
else:
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )
    print(f"   Created collection '{COLLECTION}' ({VECTOR_DIM}-dim, cosine)\n")

print(f"Embedding and uploading in batches of {BATCH_SIZE} ...\n")

total    = len(papers)
uploaded = 0
skipped  = 0
start    = time.time()

for batch_start in range(0, total, BATCH_SIZE):
    batch = papers[batch_start : batch_start + BATCH_SIZE]
    texts = [
        (p.get("title", "") + ". " + p.get("summary", "")).strip(". ")
        if p.get("summary")
        else p.get("title", "")
        for p in batch
    ]

    valid_indices = [i for i, t in enumerate(texts) if t.strip()]
    if not valid_indices:
        skipped += len(batch)
        continue

    valid_batch = [batch[i] for i in valid_indices]
    valid_texts = [texts[i] for i in valid_indices]
    vectors = model.encode(valid_texts, show_progress_bar=False).tolist()
    points = [
        PointStruct(
            id=batch_start + valid_indices[j],
            vector=vectors[j],
            payload={
                "arxiv_id":        paper.get("id", ""),
                "title":           paper.get("title", ""),
                "authors":         paper.get("authors", []),
                "summary":         paper.get("summary", ""),
                "published":       paper.get("published", ""),
                "pdf_url":         paper.get("pdf_url", ""),
                "category":        paper.get("category", ""),
                "citations":       paper.get("citations", 0),
                "github_repos":    paper.get("github_repos", []),
                "has_code":        paper.get("has_code", False),
                "journal":         paper.get("journal", ""),
                "doi":             paper.get("doi", ""),
                "fields_of_study": paper.get("fields_of_study", []),
            },
        )
        for j, paper in enumerate(valid_batch)
    ]
    client.upsert(collection_name=COLLECTION, points=points)

    uploaded += len(points)
    skipped  += len(batch) - len(valid_indices)

    elapsed = time.time() - start
    done    = batch_start + len(batch)
    pct     = done / total * 100
    print(f"   [{pct:5.1f}%]  {done}/{total} processed | {uploaded} uploaded | {elapsed:.1f}s elapsed")

elapsed = time.time() - start
print(f"\nDone in {elapsed:.1f}s")
print(f"   Uploaded : {uploaded} papers")
print(f"   Skipped  : {skipped} (no text)")
