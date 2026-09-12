"""
CLI entrypoint for governance document ingestion.
Usage:
    python -m app.rag.ingest
    python -m app.rag.ingest --force-clear
"""
import argparse
import sys
from app.rag.ingestion import get_ingestion_service


def main():
    parser = argparse.ArgumentParser(description="Ingest Phase 2 governance documents into ChromaDB.")
    parser.add_argument(
        "--force-clear",
        action="store_true",
        help="Clear existing collection before ingesting.",
    )
    args = parser.parse_args()

    print("==================================================")
    print("AI Governance Crisis Simulator — RAG Ingestion")
    print("==================================================")

    service = get_ingestion_service()
    report = service.ingest_all(force_clear=args.force_clear)

    print(f"Status:               {report.status}")
    print(f"Documents Discovered: {report.documents_discovered}")
    print(f"Documents Loaded:     {report.documents_loaded}")
    print(f"Chunks Generated:     {report.chunks_generated}")
    print(f"Chunks Stored:        {report.chunks_upserted}")
    print(f"Collection:           {report.collection_name}")
    print(f"Elapsed Time:         {report.elapsed_seconds}s")

    if report.errors:
        print("\nErrors / Warnings:")
        for err in report.errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nIngestion completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
