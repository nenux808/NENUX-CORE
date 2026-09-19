import unittest
from unittest.mock import patch

from tools.web_fetch import _extract_readable_text, _validate_public_url, web_fetch


class TestWebFetch(unittest.TestCase):
    def test_extracts_readable_html(self):
        title, text = _extract_readable_text(
            "<html><head><title>Example</title><style>x</style></head>"
            "<body><h1>Hello</h1><script>bad()</script><p>World</p></body></html>",
            "text/html",
        )

        self.assertEqual(title, "Example")
        self.assertIn("Hello", text)
        self.assertIn("World", text)
        self.assertNotIn("bad()", text)

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ValueError):
            _validate_public_url("file:///etc/passwd")

    def test_rejects_localhost(self):
        with self.assertRaises(ValueError):
            _validate_public_url("http://localhost:8000")

    @patch("tools.web_fetch.socket.getaddrinfo")
    def test_rejects_private_ip_resolution(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("192.168.1.10", 443))
        ]

        with self.assertRaises(ValueError):
            _validate_public_url("https://example.test")

    def test_rejects_empty_url(self):
        result = web_fetch("   ")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
