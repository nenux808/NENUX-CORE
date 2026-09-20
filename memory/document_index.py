"""Local document indexing and retrieval for NENUX Core."""

import hashlib
import json
from datetime import datetime, UTC
from pathlib import Path

from memory.database import get_connection
from memory.semantic_memory import _cosine_similarity, _get_embedding
from tools.filesystem import WORKSPACE, _safe_path


SUPPORTED_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".json",
    ".csv",
    ".py",
    ".yaml",
    ".yml",
    ".log",
}

DEFAULT_CHUNK_CHARS = 1200
DEFAULT_CHUNK_OVERLAP = 200


def init_document_index() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                source_hash TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                indexed_at TEXT NOT NULL,
                UNIQUE(source_path, source_hash, chunk_index)
            );

            CREATE INDEX IF NOT EXISTS idx_document_chunks_source_path
            ON document_chunks(source_path);
            """
        )


def _chunk_text(
    text: str,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunk_chars = max(200, int(chunk_chars))
    overlap = max(0, min(int(overlap), chunk_chars // 2))
    step = max(1, chunk_chars - overlap)

    chunks = []
    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_chars].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_chars >= len(text):
            break

    return chunks


def _relative_source_path(path: Path) -> str:
    return str(path.resolve().relative_to(WORKSPACE)).replace("\\", "/")


def index_document(path: str) -> dict:
    """Index one supported UTF-8 text document from the NENUX workspace."""
    init_document_index()
    target = _safe_path(path)

    if not target.exists():
        return {"success": False, "error": f"File does not exist: {path}"}

    if not target.is_file():
        return {"success": False, "error": f"Not a file: {path}"}

    if target.suffix.lower() not in SUPPORTED_SUFFIXES:
        return {
            "success": False,
            "error": (
                f"Unsupported document type: {target.suffix or '[no extension]'}. "
                f"Supported: {', '.join(sorted(SUPPORTED_SUFFIXES))}"
            ),
        }

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"success": False, "error": "File is not UTF-8 text."}

    chunks = _chunk_text(content)
    if not chunks:
        return {"success": False, "error": "Document is empty."}

    source_path = _relative_source_path(target)
    source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM document_chunks
            WHERE source_path = ? AND source_hash = ?
            """,
            (source_path, source_hash),
        ).fetchone()

        if existing and int(existing["count"]) == len(chunks):
            return {
                "success": True,
                "path": source_path,
                "chunks_indexed": 0,
                "already_current": True,
            }

        conn.execute(
            "DELETE FROM document_chunks WHERE source_path = ?",
            (source_path,),
        )

    records = []
    indexed_at = datetime.now(UTC).isoformat()

    for index, chunk in enumerate(chunks):
        vector = _get_embedding(chunk)
        records.append(
            (
                source_path,
                source_hash,
                index,
                chunk,
                json.dumps(vector),
                indexed_at,
            )
        )

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO document_chunks
            (
                source_path,
                source_hash,
                chunk_index,
                content,
                embedding,
                indexed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            records,
        )

    return {
        "success": True,
        "path": source_path,
        "chunks_indexed": len(records),
        "already_current": False,
    }


def index_workspace_documents() -> dict:
    """Index all supported text documents under the workspace."""
    init_document_index()
    indexed = []
    skipped = []

    for target in sorted(WORKSPACE.rglob("*")):
        if not target.is_file():
            continue
        if target.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        relative = _relative_source_path(target)
        result = index_document(relative)

        if result.get("success"):
            indexed.append(result)
        else:
            skipped.append({"path": relative, "error": result.get("error", "unknown")})

    return {
        "success": True,
        "documents": indexed,
        "skipped": skipped,
        "document_count": len(indexed),
        "new_chunks": sum(item.get("chunks_indexed", 0) for item in indexed),
    }


def search_documents(
    query: str,
    limit: int = 5,
    min_score: float = 0.25,
) -> dict:
    """Retrieve the most relevant indexed document chunks."""
    init_document_index()
    query = query.strip()

    if not query:
        return {"success": False, "error": "Document search query cannot be empty."}

    query_vector = _get_embedding(query)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, source_path, chunk_index, content, embedding
            FROM document_chunks
            """
        ).fetchall()

    matches = []

    for row in rows:
        try:
            vector = json.loads(row["embedding"])
            score = _cosine_similarity(query_vector, vector)
        except Exception:
            continue

        if score >= float(min_score):
            matches.append(
                {
                    "source_path": row["source_path"],
                    "chunk_index": row["chunk_index"],
                    "score": round(score, 4),
                    "content": row["content"],
                }
            )

    matches.sort(key=lambda item: item["score"], reverse=True)

    return {
        "success": True,
        "query": query,
        "results": matches[: max(1, min(int(limit), 10))],
    }
