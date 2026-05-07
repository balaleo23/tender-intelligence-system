"""
Retrieval evaluation script — run BEFORE and AFTER optimisations to measure improvement.

Usage:
    # Capture baseline (before changes)
    python scripts/eval_retrieval.py --out scripts/eval_baseline.json

    # Capture post-optimisation results
    python scripts/eval_retrieval.py --out scripts/eval_after.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO POPULATE THE GOLDEN DATASET (do this once):

  Step 1 — Start infrastructure
           docker-compose up -d postgres qdrant ollama

  Step 2 — Scrape some real data
           python scripts/run_scraper.py
           (solve CAPTCHAs manually in the browser window)

  Step 3 — Ingest into Postgres + Qdrant
           curl -X POST http://localhost:8000/ingest
           OR: Streamlit → Ingest page → Run Ingestion

  Step 4 — Find real tender UIDs
           docker exec -it tender_postgres psql -U tender_user -d tender_db
           SELECT tender_uid, title FROM tenders LIMIT 20;

  Step 5 — Match UIDs to your GOLDEN questions below
           Replace None with a real tender_uid that you expect
           to appear in the top-k results for that question.

  Step 6 — Run baseline eval
           python scripts/eval_retrieval.py --out scripts/eval_baseline.json

  Step 7 — Tune chunk sizes
           python scripts/tune_chunks.py

  Step 8 — Update config.py with the best chunk_size + overlap from tune results
           Then re-ingest and re-run eval to confirm improvement.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOLDEN DATASET — fill in real tender_uid values from your scraped data:
  Run this query in psql to find real UIDs:
      SELECT tender_uid, title FROM tenders LIMIT 20;
  Then replace the placeholder UIDs below with ones that actually exist in Qdrant.

Metrics reported:
  - latency_ms   : total time for embed_query() + qdrant.query_points()
  - top_score    : cosine similarity of the best matching chunk
  - hit_rate     : 1.0 if expected_uid appears anywhere in top-k results, else 0.0
  - mrr          : 1/rank of the first result whose tender_uid matches expected_uid
                   (0.0 if not found in top-k)
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Make sure project root is on the path when running as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient

from ingestion_engine.config import settings
from ingestion_engine.services.embedding_service import EmbeddingService

# ── Golden dataset ─────────────────────────────────────────────────────────────
# Replace expected_uid with real tender_uid values from your database.
# Leave expected_uid as None for queries where you just want to measure latency
# and top score without checking Hit Rate / MRR.
GOLDEN = [
    {
        "question": "road construction tenders in Tamil Nadu",
        "expected_uid": None,  # e.g. "2024_PWD_001"
    },
    {
        "question": "IT infrastructure procurement tenders",
        "expected_uid": None,
    },
    {
        "question": "water supply and sanitation project tenders",
        "expected_uid": None,
    },
    {
        "question": "building construction tenders closing this month",
        "expected_uid": None,
    },
    {
        "question": "electrical works tenders from public works department",
        "expected_uid": None,
    },
]

TOP_K = settings.top_k


def evaluate(client: QdrantClient, embedder: EmbeddingService) -> list[dict]:
    results = []

    for item in GOLDEN:
        question = item["question"]
        expected_uid = item["expected_uid"]

        # ── Time the full retrieval (embed + search) ───────────────────────────
        t0 = time.perf_counter()

        query_vector = embedder.embed_query(question)
        hits = client.query_points(
            collection_name=settings.collection_name,
            query=query_vector,
            limit=TOP_K,
        ).points

        latency_ms = (time.perf_counter() - t0) * 1000

        # ── Compute metrics ────────────────────────────────────────────────────
        top_score = hits[0].score if hits else 0.0

        hit_rate = 0.0
        mrr = 0.0

        if expected_uid and hits:
            for rank, hit in enumerate(hits, start=1):
                if hit.payload.get("tender_uid") == expected_uid:
                    hit_rate = 1.0
                    mrr = 1.0 / rank
                    break

        retrieved_uids = [h.payload.get("tender_uid") for h in hits]

        result = {
            "question": question,
            "expected_uid": expected_uid,
            "latency_ms": round(latency_ms, 1),
            "top_score": round(top_score, 4),
            "hit_rate": hit_rate,
            "mrr": round(mrr, 4),
            "retrieved_uids": retrieved_uids,
        }
        results.append(result)

        status = "HIT" if hit_rate == 1.0 else ("N/A" if not expected_uid else "MISS")
        print(
            f"  [{status:4s}]  {latency_ms:6.0f}ms  score={top_score:.3f}  "
            f"mrr={mrr:.3f}  | {question[:55]}"
        )

    return results


def summary(results: list[dict]) -> dict:
    with_uid = [r for r in results if r["expected_uid"] is not None]
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    avg_hit_rate = sum(r["hit_rate"] for r in with_uid) / len(with_uid) if with_uid else None
    avg_mrr = sum(r["mrr"] for r in with_uid) / len(with_uid) if with_uid else None

    return {
        "total_queries": len(results),
        "queries_with_uid": len(with_uid),
        "avg_latency_ms": round(avg_latency, 1),
        "avg_hit_rate": round(avg_hit_rate, 4) if avg_hit_rate is not None else None,
        "avg_mrr": round(avg_mrr, 4) if avg_mrr is not None else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality and latency")
    parser.add_argument("--out", default="scripts/eval_results.json", help="Output JSON file path")
    args = parser.parse_args()

    print(f"\nConnecting to Qdrant at {settings.qdrant_host}:{settings.qdrant_port} ...")
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    collections = [c.name for c in client.get_collections().collections]
    if settings.collection_name not in collections:
        print(f"ERROR: collection '{settings.collection_name}' not found in Qdrant.")
        print(f"Available: {collections}")
        sys.exit(1)

    print("Loading embedding model ...")
    embedder = EmbeddingService()

    print(f"\nRunning {len(GOLDEN)} queries (top_k={TOP_K}) ...\n")
    results = evaluate(client, embedder)

    stats = summary(results)
    print(f"\n{'─'*60}")
    print(f"  Queries       : {stats['total_queries']}  ({stats['queries_with_uid']} with expected UID)")
    print(f"  Avg latency   : {stats['avg_latency_ms']} ms")
    if stats["avg_hit_rate"] is not None:
        print(f"  Hit Rate @{TOP_K}  : {stats['avg_hit_rate']:.1%}")
        print(f"  Avg MRR       : {stats['avg_mrr']:.4f}")
    else:
        print("  Hit Rate / MRR: N/A — fill in expected_uid values in GOLDEN dataset")
    print(f"{'─'*60}\n")

    output = {"summary": stats, "per_query": results}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
