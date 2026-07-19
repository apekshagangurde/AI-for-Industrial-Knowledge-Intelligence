"""Embed chunks (chunker.py output) and upsert them into a local Chroma index.

Run as a script to (re)build the index from data/raw + data/synthetic:
    python -m ingestion.embed_store
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from ingestion import ocr
from ingestion.chunker import chunk_elements
from ingestion.parse_docs import parse_document

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "industrial_docs"

_chroma_path_setting = Path(os.getenv("CHROMA_PATH", "./chroma_db"))
CHROMA_PATH = _chroma_path_setting if _chroma_path_setting.is_absolute() else REPO_ROOT / "backend" / _chroma_path_setting

_embedder: SentenceTransformer | None = None
_client: chromadb.ClientAPI | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_embedder().encode(texts, normalize_embeddings=True).tolist()


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return _client


def get_collection():
    return get_client().get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def upsert_chunks(chunks: list[dict], titles: dict[str, str] | None = None) -> None:
    if not chunks:
        return
    titles = titles or {}
    collection = get_collection()
    embeddings = embed_texts([c["text"] for c in chunks])
    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "doc_id": c["doc_id"],
                "doc_type": c["doc_type"] or "unknown",
                "page": c["page"],
                "section_title": c["section_title"] or "",
                "chunk_type": c["type"],
                "title": titles.get(c["doc_id"], c["doc_id"]),
            }
            for c in chunks
        ],
    )


def _load_manifest(csv_path: Path, key_to_doc_id) -> dict[str, dict]:
    manifest: dict[str, dict] = {}
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            manifest[key_to_doc_id(row["filename"])] = row
    return manifest


def _parse_source(path: Path) -> list[dict]:
    if path.suffix.lower() in ocr.IMAGE_SUFFIXES:
        text = ocr.ocr_image(path)
        return [{"doc_id": path.stem, "page": 1, "type": "paragraph", "text": text}]
    return parse_document(path)


def run_ingestion() -> dict[str, int]:
    """(Re)build the Chroma index from data/raw + data/synthetic. Idempotent — chunk IDs
    are deterministic (doc_id::index), so re-running upserts rather than duplicating."""
    raw_dir = REPO_ROOT / "data/raw"
    synthetic_dir = REPO_ROOT / "data/synthetic"

    raw_manifest = _load_manifest(raw_dir / "manifest.csv", lambda fn: Path(fn).stem)
    synthetic_manifest = _load_manifest(synthetic_dir / "manifest.csv", lambda fn: Path(fn).stem)

    titles: dict[str, str] = {}
    total_chunks = 0
    docs_ingested = 0

    for doc_id, row in raw_manifest.items():
        if row["doc_type"] == "pid_drawing":
            continue  # diagrams — no extractable text corpus content, see #11
        path = raw_dir / row["filename"]
        if not path.exists() or path.suffix.lower() not in (".pdf", *ocr.IMAGE_SUFFIXES):
            continue
        try:
            elements = _parse_source(path)
            chunks = chunk_elements(elements, doc_type=row["doc_type"])
            titles[doc_id] = row["filename"]
            upsert_chunks(chunks, titles)
        except Exception as exc:
            print(f"skipping {path.name}: {exc}")
            continue
        total_chunks += len(chunks)
        docs_ingested += 1

    for doc_id, row in synthetic_manifest.items():
        path = synthetic_dir / row["filename"]
        if not path.exists():
            continue
        try:
            elements = _parse_source(path)
            chunks = chunk_elements(elements, doc_type=row["doc_type"])
            titles[doc_id] = row.get("title") or row["filename"]
            upsert_chunks(chunks, titles)
        except Exception as exc:
            print(f"skipping {path.name}: {exc}")
            continue
        total_chunks += len(chunks)
        docs_ingested += 1

    return {"documents": docs_ingested, "chunks": total_chunks}


if __name__ == "__main__":
    summary = run_ingestion()
    print(f"Ingested {summary['documents']} documents into {summary['chunks']} chunks -> {CHROMA_PATH}")
