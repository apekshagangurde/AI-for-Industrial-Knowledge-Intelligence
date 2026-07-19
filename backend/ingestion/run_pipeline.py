#!/usr/bin/env python3
"""One command for the full ingestion pipeline (#14):
  1. parse -> chunk -> embed (embed_store.run_ingestion) -> Chroma
  2. parse -> chunk -> extract entities -> write graph (graph_writer.run_graph_ingestion) -> Neo4j

across data/raw + data/synthetic.

    python -m ingestion.run_pipeline
    python -m ingestion.run_pipeline --skip-graph   # e.g. no Groq quota left today

Both steps are independently idempotent (Chroma upserts by chunk_id, Neo4j
writes are all MERGE), so re-running after a partial failure just picks up
where it left off rather than duplicating anything.
"""
from __future__ import annotations

import argparse
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--input",
        default="data/",
        help="Present for compatibility with the ticket spec -- the pipeline always reads "
        "from data/raw + data/synthetic relative to the repo root, not an arbitrary path.",
    )
    parser.add_argument(
        "--skip-graph", action="store_true", help="Skip the Neo4j graph step entirely"
    )
    args = parser.parse_args()

    from ingestion.embed_store import run_ingestion

    logger.info("Step 1/2: parse -> chunk -> embed -> Chroma")
    start = time.time()
    embed_summary = run_ingestion()
    logger.info(
        "Embedding done in %.1fs: %d documents, %d chunks",
        time.time() - start,
        embed_summary["documents"],
        embed_summary["chunks"],
    )

    graph_summary = {"documents": 0, "equipment": 0, "persons": 0, "regulations": 0, "relationships": 0}
    if args.skip_graph:
        logger.info("Step 2/2: skipped (--skip-graph)")
    else:
        from ingestion.graph_writer import close_driver, run_graph_ingestion

        logger.info("Step 2/2: parse -> chunk -> extract entities -> write graph -> Neo4j")
        start = time.time()
        graph_summary = run_graph_ingestion(verbose=True)
        close_driver()
        logger.info(
            "Graph writing done in %.1fs: %d documents, %d equipment refs, %d person refs, "
            "%d regulation refs, %d relationships",
            time.time() - start,
            graph_summary["documents"],
            graph_summary["equipment"],
            graph_summary["persons"],
            graph_summary["regulations"],
            graph_summary["relationships"],
        )

    print("\n=== Ingestion summary ===")
    print(f"Documents embedded:      {embed_summary['documents']}")
    print(f"Chunks embedded:         {embed_summary['chunks']}")
    print(f"Documents graphed:       {graph_summary['documents']}")
    print(f"Equipment refs written:  {graph_summary['equipment']}")
    print(f"Person refs written:     {graph_summary['persons']}")
    print(f"Regulation refs written: {graph_summary['regulations']}")
    print(f"Relationships written:   {graph_summary['relationships']}")


if __name__ == "__main__":
    main()
