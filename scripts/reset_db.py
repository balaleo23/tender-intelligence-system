"""
Reset script — wipes all data from Qdrant and PostgreSQL, then recreates
the schema fresh. Run this from the project root:

    python scripts/reset_db.py

Add --yes to skip the confirmation prompt (useful in CI / automation).
"""

import argparse
import sys
from pathlib import Path

# Make project root importable regardless of where the script is invoked from
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sqlalchemy import create_engine, text

from ingestion_engine.config import settings
from ingestion_engine.storage.models import Base


# ── helpers ──────────────────────────────────────────────────────────────────

def reset_qdrant() -> None:
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    existing = {c.name for c in client.get_collections().collections}
    if settings.collection_name in existing:
        client.delete_collection(settings.collection_name)
        print(f"  [Qdrant] Deleted collection '{settings.collection_name}'")
    else:
        print(f"  [Qdrant] Collection '{settings.collection_name}' did not exist — skipping delete")

    client.create_collection(
        collection_name=settings.collection_name,
        vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
    )
    print(f"  [Qdrant] Recreated collection '{settings.collection_name}' (dim={settings.embedding_dim}, COSINE)")


def reset_postgres() -> None:
    engine = create_engine(str(settings.postgres_url))

    with engine.connect() as conn:
        # Drop in reverse dependency order to satisfy foreign-key constraints
        conn.execute(text("DROP TABLE IF EXISTS tender_documents CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS tender_ingestion_logs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS tenders CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS organizations CASCADE"))
        conn.commit()
    print("  [Postgres] Dropped all tables")

    Base.metadata.create_all(engine)
    print("  [Postgres] Recreated schema (organizations, tenders, tender_documents, tender_ingestion_logs)")

    engine.dispose()


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Reset Qdrant + PostgreSQL to a clean state")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("\n  WARNING: This will permanently delete ALL data in Qdrant and PostgreSQL.")
    print(f"    Qdrant   : {settings.qdrant_host}:{settings.qdrant_port}  collection='{settings.collection_name}'")
    print(f"    Postgres : {settings.postgres_url}\n")

    if not args.yes:
        answer = input("  Type 'yes' to continue: ").strip().lower()
        if answer != "yes":
            print("  Aborted.")
            sys.exit(0)

    print("\n  Resetting Qdrant ...")
    reset_qdrant()

    print("\n  Resetting PostgreSQL ...")
    reset_postgres()

    print("\n  Done. Both databases are clean and ready.\n")


if __name__ == "__main__":
    main()
