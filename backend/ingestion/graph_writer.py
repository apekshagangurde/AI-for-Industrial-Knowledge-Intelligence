"""Write extracted entities (entity_extract.py output) into the Neo4j knowledge
graph, following the shape in docs/kg-schema.md.

All writes use MERGE, so re-running ingestion never creates duplicate nodes or
relationships. Run as a script to (re)build the graph from data/raw + data/synthetic:
    python -m ingestion.graph_writer
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

from common.plant_alpha import EQUIPMENT
from ingestion.chunker import chunk_elements
from ingestion.entity_extract import extract_entities_for_chunks

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "changeme")

EQUIPMENT_BY_TAG = {e["tag"]: e for e in EQUIPMENT}

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _write_document(tx, doc_id: str, doc_type: str, title: str, source_path: str, date: str | None) -> None:
    tx.run(
        """
        MERGE (d:Document {doc_id: $doc_id})
        SET d.title = $title, d.doc_type = $doc_type, d.source_path = $source_path
        """,
        doc_id=doc_id, title=title, doc_type=doc_type, source_path=source_path,
    )
    if doc_type == "procedure":
        tx.run(
            "MATCH (d:Document {doc_id: $doc_id}) SET d:Procedure, d.proc_id = $doc_id, d.title = $title",
            doc_id=doc_id, title=title,
        )
    elif doc_type == "regulation":
        tx.run(
            "MATCH (d:Document {doc_id: $doc_id}) SET d:Regulation, d.code = $doc_id, d.title = $title",
            doc_id=doc_id, title=title,
        )
    elif doc_type == "incident":
        tx.run(
            "MATCH (d:Document {doc_id: $doc_id}) "
            "SET d:Incident, d.incident_id = $doc_id, d.title = $title, d.date = $date",
            doc_id=doc_id, title=title, date=date,
        )


def _write_equipment(tx, tag: str) -> None:
    info = EQUIPMENT_BY_TAG.get(tag, {})
    tx.run(
        """
        MERGE (e:Equipment {tag: $tag})
        SET e.name = coalesce($name, e.name),
            e.type = coalesce($type, e.type),
            e.area = coalesce($area, e.area)
        """,
        tag=tag, name=info.get("name"), type=info.get("type"), area=info.get("area"),
    )
    if info.get("area"):
        tx.run(
            """
            MERGE (a:Area {name: $area})
            WITH a
            MATCH (e:Equipment {tag: $tag})
            MERGE (e)-[:LOCATED_IN]->(a)
            """,
            area=info["area"], tag=tag,
        )


def _link_document_references(tx, doc_id: str, label: str, key: str, value: str) -> None:
    tx.run(
        f"""
        MATCH (d:Document {{doc_id: $doc_id}})
        MATCH (n:{label} {{{key}: $value}})
        MERGE (d)-[:REFERENCES]->(n)
        """,
        doc_id=doc_id, value=value,
    )


def _link_person_maintains_equipment(tx, name: str, tag: str) -> None:
    tx.run(
        """
        MATCH (p:Person {name: $name})
        MATCH (e:Equipment {tag: $tag})
        MERGE (p)-[:MAINTAINS]->(e)
        """,
        name=name, tag=tag,
    )


def _link_incident_reported_by(tx, doc_id: str, name: str) -> None:
    tx.run(
        """
        MATCH (i:Incident {incident_id: $doc_id})
        MATCH (p:Person {name: $name})
        MERGE (i)-[:REPORTED_BY]->(p)
        """,
        doc_id=doc_id, name=name,
    )


def _link_equipment_governed_by(tx, tag: str, code: str) -> None:
    tx.run(
        """
        MATCH (e:Equipment {tag: $tag})
        MATCH (r:Regulation {code: $code})
        MERGE (e)-[:GOVERNED_BY]->(r)
        """,
        tag=tag, code=code,
    )


def write_document_entities(
    doc_id: str,
    doc_type: str,
    title: str,
    source_path: str,
    date: str | None,
    chunk_entities: list[dict],
) -> dict[str, int]:
    """chunk_entities: one entity_extract.extract_entities() result per chunk of this
    document. Writes everything into the graph via MERGE (idempotent)."""
    driver = get_driver()
    counts = {"equipment": 0, "persons": 0, "regulations": 0, "relationships": 0}

    all_equipment: set[str] = set()
    all_personnel: set[str] = set()
    all_regulations: set[str] = set()

    with driver.session() as session:
        session.execute_write(_write_document, doc_id, doc_type, title, source_path, date)

        for chunk in chunk_entities:
            tags = set(chunk.get("equipment_tags", []))
            personnel = set(chunk.get("personnel", []))
            regs = set(chunk.get("regulation_refs", []))
            all_equipment |= tags
            all_personnel |= personnel
            all_regulations |= regs

            # Same-chunk co-occurrence -> more specific relationships than a blanket REFERENCES.
            if doc_type == "work_order":
                for name in personnel:
                    for tag in tags:
                        session.execute_write(_link_person_maintains_equipment, name, tag)
                        counts["relationships"] += 1
            for tag in tags:
                for code in regs:
                    session.execute_write(_link_equipment_governed_by, tag, code)
                    counts["relationships"] += 1

        for tag in all_equipment:
            session.execute_write(_write_equipment, tag)
            session.execute_write(_link_document_references, doc_id, "Equipment", "tag", tag)
            counts["equipment"] += 1
            counts["relationships"] += 1
            if doc_type == "regulation":
                session.execute_write(_link_equipment_governed_by, tag, doc_id)
                counts["relationships"] += 1

        for name in all_personnel:
            session.execute_write(lambda tx, n=name: tx.run("MERGE (p:Person {name: $name})", name=n))
            session.execute_write(_link_document_references, doc_id, "Person", "name", name)
            counts["persons"] += 1
            counts["relationships"] += 1
            if doc_type == "incident":
                session.execute_write(_link_incident_reported_by, doc_id, name)
                counts["relationships"] += 1

        for code in all_regulations:
            session.execute_write(lambda tx, c=code: tx.run("MERGE (r:Regulation {code: $code})", code=c))
            session.execute_write(_link_document_references, doc_id, "Regulation", "code", code)
            counts["regulations"] += 1
            counts["relationships"] += 1

    return counts


def _process_doc(path: Path, doc_id: str, doc_type: str, title: str, date: str | None) -> dict[str, int]:
    from ingestion.embed_store import _parse_source

    elements = _parse_source(path)
    chunks = chunk_elements(elements, doc_type=doc_type)
    if not chunks:
        return {}
    entities_by_chunk = extract_entities_for_chunks(chunks)
    chunk_entities = [entities_by_chunk[c["chunk_id"]] for c in chunks]
    source_path = str(path.relative_to(REPO_ROOT))
    return write_document_entities(doc_id, doc_type, title, source_path, date, chunk_entities)


def run_graph_ingestion(verbose: bool = True) -> dict[str, int]:
    """(Re)build the graph from data/raw + data/synthetic. Idempotent -- every write
    above is a MERGE, so re-running never duplicates nodes/relationships. Safe to
    interrupt and resume: entity extraction is cached per chunk_id (entity_extract.py),
    so a killed run only re-does LLM calls for chunks it hadn't reached yet."""
    from ingestion.embed_store import _load_manifest

    raw_dir = REPO_ROOT / "data/raw"
    synthetic_dir = REPO_ROOT / "data/synthetic"
    raw_manifest = _load_manifest(raw_dir / "manifest.csv", lambda fn: Path(fn).stem)
    synthetic_manifest = _load_manifest(synthetic_dir / "manifest.csv", lambda fn: Path(fn).stem)

    docs_written = 0
    totals = {"equipment": 0, "persons": 0, "regulations": 0, "relationships": 0}
    all_docs = [(raw_dir, doc_id, row, None) for doc_id, row in raw_manifest.items()] + [
        (synthetic_dir, doc_id, row, row.get("date")) for doc_id, row in synthetic_manifest.items()
    ]
    total_docs = len(all_docs)

    for i, (source_dir, doc_id, row, date) in enumerate(all_docs, start=1):
        if row["doc_type"] == "pid_drawing":
            if verbose:
                print(f"[{i}/{total_docs}] {row['filename']}: skipped (pid_drawing, see #11)")
            continue
        path = source_dir / row["filename"]
        if not path.exists():
            continue
        title = row.get("title") or row["filename"]
        try:
            counts = _process_doc(path, doc_id, row["doc_type"], title, date)
        except Exception as exc:
            if verbose:
                print(f"[{i}/{total_docs}] {row['filename']}: skipped ({exc})")
            continue
        if counts:
            docs_written += 1
            for key in totals:
                totals[key] += counts.get(key, 0)
        if verbose:
            print(f"[{i}/{total_docs}] {row['filename']}: {counts}")

    return {"documents": docs_written, **totals}


if __name__ == "__main__":
    summary = run_graph_ingestion()
    print(
        f"Wrote {summary['documents']} documents, {summary['equipment']} equipment refs, "
        f"{summary['persons']} person refs, {summary['regulations']} regulation refs, "
        f"{summary['relationships']} relationships -> {NEO4J_URI}"
    )
    close_driver()
