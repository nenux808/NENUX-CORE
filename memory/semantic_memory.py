import json
import math
import hashlib
from datetime import datetime, timezone

from ollama import embed

from memory.database import get_connection
from config import EMBED_MODEL, SEMANTIC_MIN_SCORE, SEMANTIC_SEARCH_LIMIT


def init_semantic_memory():

    with get_connection() as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_hash TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def _get_embedding(text: str) -> list[float]:

    response = embed(
        model=EMBED_MODEL,
        input=text
    )

    if hasattr(response, "embeddings"):
        vectors = response.embeddings
    else:
        vectors = response["embeddings"]

    if not vectors:
        raise RuntimeError(
            "Embedding model returned no vector."
        )

    return list(vectors[0])


def _cosine_similarity(
    a: list[float],
    b: list[float]
) -> float:

    if not a or not b:
        return 0.0

    dot = sum(
        x * y
        for x, y in zip(a, b)
    )

    norm_a = math.sqrt(
        sum(x * x for x in a)
    )

    norm_b = math.sqrt(
        sum(y * y for y in b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (
        norm_a * norm_b
    )


def add_semantic_memory(
    content: str,
    kind: str = "general"
) -> bool:

    content = content.strip()

    if not content:
        return False

    memory_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    with get_connection() as conn:

        existing = conn.execute(
            """
            SELECT id
            FROM semantic_memories
            WHERE memory_hash = ?
            """,
            (memory_hash,)
        ).fetchone()

        if existing:
            return False

    vector = _get_embedding(
        content
    )

    with get_connection() as conn:

        conn.execute(
            """
            INSERT INTO semantic_memories
            (
                memory_hash,
                kind,
                content,
                embedding,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                memory_hash,
                kind,
                content,
                json.dumps(vector),
                datetime.now(timezone.utc).isoformat()
            )
        )

    return True


def search_semantic_memories(
    query: str,
    limit: int = SEMANTIC_SEARCH_LIMIT,
    min_score: float = SEMANTIC_MIN_SCORE
) -> list:

    query_vector = _get_embedding(
        query
    )

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT id,
                   kind,
                   content,
                   embedding,
                   created_at
            FROM semantic_memories
            """
        ).fetchall()

    results = []

    for row in rows:

        try:

            memory_vector = json.loads(
                row["embedding"]
            )

            score = _cosine_similarity(
                query_vector,
                memory_vector
            )

        except Exception:
            continue

        if score >= min_score:

            results.append(
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "content": row["content"],
                    "score": score,
                    "created_at": row[
                        "created_at"
                    ]
                }
            )

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:limit]


def build_semantic_context(
    query: str,
    limit: int = SEMANTIC_SEARCH_LIMIT
) -> str:

    memories = search_semantic_memories(
        query=query,
        limit=limit
    )

    if not memories:

        return """
RELEVANT LONG-TERM MEMORY:
No relevant stored memories were found.
""".strip()

    lines = [
        "RELEVANT LONG-TERM MEMORY:"
    ]

    for memory in memories:

        score = round(
            memory["score"],
            3
        )

        lines.append(
            f"""
Memory #{memory['id']}
Type: {memory['kind']}
Similarity: {score}
Content:
{memory['content']}
""".strip()
        )

    return "\n\n".join(lines)
