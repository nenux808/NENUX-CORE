import unittest
from unittest.mock import patch

from tools.web_search import web_search


class TestWebSearch(unittest.TestCase):
    @patch("tools.web_search.DDGS")
    def test_returns_compact_sources(self, mock_ddgs):
        mock_ddgs.return_value.text.return_value = [
            {
                "title": "Example",
                "href": "https://example.com",
                "body": "Example result",
            }
        ]

        result = web_search("example", max_results=3)

        self.assertTrue(result["success"])
        self.assertEqual(result["query"], "example")
        self.assertEqual(result["results"][0]["title"], "Example")
        self.assertEqual(result["results"][0]["url"], "https://example.com")

    def test_rejects_empty_query(self):
        result = web_search("   ")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
