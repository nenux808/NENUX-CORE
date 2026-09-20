import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from memory import document_index


class TestDocumentIndex(unittest.TestCase):
    def test_chunk_text_splits_and_overlaps(self):
        text = "A" * 2500
        chunks = document_index._chunk_text(text, chunk_chars=1000, overlap=100)

        self.assertGreaterEqual(len(chunks), 3)
        self.assertEqual(len(chunks[0]), 1000)
        self.assertEqual(len(chunks[1]), 1000)

    def test_supported_suffixes_include_common_text_formats(self):
        self.assertIn(".txt", document_index.SUPPORTED_SUFFIXES)
        self.assertIn(".md", document_index.SUPPORTED_SUFFIXES)
        self.assertIn(".csv", document_index.SUPPORTED_SUFFIXES)

    @patch("memory.document_index._get_embedding")
    @patch("memory.document_index.get_connection")
    def test_search_documents_ranks_best_match(self, mock_connection, mock_embedding):
        mock_embedding.return_value = [1.0, 0.0]

        rows = [
            {
                "id": 1,
                "source_path": "a.txt",
                "chunk_index": 0,
                "content": "best",
                "embedding": "[1.0, 0.0]",
            },
            {
                "id": 2,
                "source_path": "b.txt",
                "chunk_index": 0,
                "content": "worse",
                "embedding": "[0.0, 1.0]",
            },
        ]

        class FakeConn:
            def execute(self, *args, **kwargs):
                class Result:
                    def fetchall(self_inner):
                        return rows
                return Result()

            def executescript(self, *args, **kwargs):
                return None

        class FakeContext:
            def __enter__(self):
                return FakeConn()

            def __exit__(self, exc_type, exc, tb):
                return False

        mock_connection.side_effect = lambda: FakeContext()

        result = document_index.search_documents("best", limit=2, min_score=0.0)

        self.assertTrue(result["success"])
        self.assertEqual(result["results"][0]["source_path"], "a.txt")
        self.assertGreater(
            result["results"][0]["score"],
            result["results"][1]["score"],
        )


if __name__ == "__main__":
    unittest.main()
