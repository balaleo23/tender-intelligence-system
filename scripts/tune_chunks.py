"""
Chunk size tuning script — find the best chunk_size + overlap for your data.

Runs the GOLDEN eval dataset across a grid of (chunk_size, overlap) combinations
and reports hit_rate, MRR, and latency for each. Use this AFTER filling in real
expected_uid values in scripts/eval_retrieval.py.

Usage:
    python scripts/tune_chunks.py

Output:
    - Comparison table printed to console
    - scripts/tune_results.json saved with full per-config metrics

Prerequisites:
    - Qdrant running (docker-compose up qdrant)
    - Tenders already ingested (POST /ingest)
    - GOLDEN dataset in eval_retrieval.py has real expected_uid values

How it works:
    For each (chunk_size, overlap) combo:
      1. Creates a TEMP Qdrant collection (does NOT touch your main 'tenders' collection)
      2. Re-chunks + re-embeds documents from the existing Qdrant payloads
      3. Runs GOLDEN queries against the temp collection
      4. Records metrics and deletes the temp collection
    Your production data is never modified.
"""

import json
import sys
import time
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ingestion_engine.config import settings
from ingestion_engine.services.chunking_service import WordChunker, SentenceChunker
from ingestion_engine.services.embedding_service import EmbeddingService

# ── Import GOLDEN dataset from eval_retrieval.py ──────────────────────────────
from scripts.eval_retrieval import GOLDEN

# ── Tuning grid ───────────────────────────────────────────────────────────────
CHUNK_SIZES = [400, 600, 800, 1000]
OVERLAPS = [50, 100, 150]
STRATEGIES = ["word", "sentence"]   # WordChunker vs SentenceChunker
TOP_K = settings.top_k
TEMP_COLLECTION = "tenders_tune_temp"


def fetch_all_texts(client: QdrantClient) -> list[dict]:
    """Pull all text payloads from the main Qdrant collection."""
    all_points = []
    offset = None

    while True:
        result, offset = client.scroll(
            collection_name=settings.collection_name,
            scroll_filter=None,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        all_points.extend(result)
        if offset is None:
            break

    # Deduplicate by (document, tender_uid) — we only need unique text chunks
    seen = set()
    unique = []
    for p in all_points:
        key = (p.payload.get("document"), p.payload.get("tender_uid"))
        if key not in seen:
            seen.add(key)
            unique.append(p.payload)

    return unique


def build_temp_collection(
    client: QdrantClient,
    embedder: EmbeddingService,
    payloads: list[dict],
    chunk_size: int,
    overlap: int,
    strategy: str,
) -> int:
    """Re-chunk payloads and upsert into TEMP_COLLECTION. Returns point count."""
    chunker = (
        WordChunker(size=chunk_size, overlap=overlap)
        if strategy == "word"
        else SentenceChunker(size=chunk_size, overlap=overlap)
    )

    if TEMP_COLLECTION in [c.name for c in client.get_collections().collections]:
        client.delete_collection(TEMP_COLLECTION)

    client.create_collection(
        collection_name=TEMP_COLLECTION,
        vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
    )

    points = []
    for i, payload in enumerate(payloads):
        text = payload.get("text", "")
        if not text.strip():
            continue
        chunks = chunker.chunk(text)
        for j, chunk in enumerate(chunks):
            vector = embedder.embed_documents([chunk])[0]
            points.append(PointStruct(
                id=len(points),
                vector=vector,
                payload={**payload, "text": chunk, "chunk_index": j},
            ))

    if points:
        client.upsert(collection_name=TEMP_COLLECTION, points=points)

    return len(points)


def run_eval(client: QdrantClient, embedder: EmbeddingService) -> list[dict]:
    """Run GOLDEN queries against TEMP_COLLECTION and return per-query metrics."""
    results = []
    for item in GOLDEN:
        question = item["question"]
        expected_uid = item["expected_uid"]

        t0 = time.perf_counter()
        query_vector = embedder.embed_query(question)
        hits = client.query_points(
            collection_name=TEMP_COLLECTION,
            query=query_vector,
            limit=TOP_K,
        ).points
        latency_ms = (time.perf_counter() - t0) * 1000

        top_score = hits[0].score if hits else 0.0
        hit_rate, mrr = 0.0, 0.0

        if expected_uid and hits:
            for rank, hit in enumerate(hits, start=1):
                if hit.payload.get("tender_uid") == expected_uid:
                    hit_rate = 1.0
                    mrr = 1.0 / rank
                    break

        results.append({
            "question": question,
            "latency_ms": round(latency_ms, 1),
            "top_score": round(top_score, 4),
            "hit_rate": hit_rate,
            "mrr": round(mrr, 4),
        })
    return results


def summarise(results: list[dict]) -> dict:
    with_uid = [r for r in results if r.get("hit_rate") is not None]
    return {
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / len(results), 1),
        "avg_hit_rate": round(sum(r["hit_rate"] for r in with_uid) / len(with_uid), 4) if with_uid else None,
        "avg_mrr": round(sum(r["mrr"] for r in with_uid) / len(with_uid), 4) if with_uid else None,
    }


def main():
    print(f"\nConnecting to Qdrant at {settings.qdrant_host}:{settings.qdrant_port} ...")
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    print("Loading embedding model ...")
    embedder = EmbeddingService()

    print("Fetching existing payloads from Qdrant ...")
    payloads = fetch_all_texts(client)
    print(f"  {len(payloads)} unique document segments found\n")

    all_results = []
    grid = list(product(STRATEGIES, CHUNK_SIZES, OVERLAPS))
    print(f"Running {len(grid)} configurations × {len(GOLDEN)} queries ...\n")
    print(f"{'Strategy':<10} {'ChunkSz':>8} {'Overlap':>8} {'Points':>8} {'Latency':>10} {'HitRate':>10} {'MRR':>8}")
    print("─" * 70)

    for strategy, chunk_size, overlap in grid:
        n_points = build_temp_collection(client, embedder, payloads, chunk_size, overlap, strategy)
        results = run_eval(client, embedder)
        stats = summarise(results)

        hit_str = f"{stats['avg_hit_rate']:.1%}" if stats["avg_hit_rate"] is not None else "  N/A "
        mrr_str = f"{stats['avg_mrr']:.4f}" if stats["avg_mrr"] is not None else "  N/A"

        print(
            f"{strategy:<10} {chunk_size:>8} {overlap:>8} {n_points:>8} "
            f"{stats['avg_latency_ms']:>9}ms {hit_str:>10} {mrr_str:>8}"
        )

        all_results.append({
            "strategy": strategy,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "n_points": n_points,
            **stats,
            "per_query": results,
        })

    # Cleanup temp collection
    client.delete_collection(TEMP_COLLECTION)
    print("\nTemp collection cleaned up.")

    out_path = Path("scripts/tune_results.json")
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"Full results saved to {out_path}\n")

    # Print winner
    scored = [r for r in all_results if r["avg_hit_rate"] is not None]
    if scored:
        best = max(scored, key=lambda r: (r["avg_hit_rate"], r["avg_mrr"]))
        print(f"Best config: strategy={best['strategy']}  chunk_size={best['chunk_size']}  overlap={best['overlap']}")
        print(f"  Hit Rate: {best['avg_hit_rate']:.1%}   MRR: {best['avg_mrr']:.4f}   Latency: {best['avg_latency_ms']}ms")
    else:
        print("Fill in expected_uid values in GOLDEN dataset to get Hit Rate and MRR scores.")


if __name__ == "__main__":
    main()
