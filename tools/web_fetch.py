"""Read-only public web page fetcher for NENUX Core."""

import ipaddress
import re
import socket
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_RESPONSE_BYTES = 512_000
MAX_TEXT_CHARS = 12_000
DEFAULT_TIMEOUT_SECONDS = 10


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("URL must include a hostname.")

    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise ValueError("Local/private hosts are not allowed.")

    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve hostname: {hostname}") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError("Private or non-public network destinations are not allowed.")


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urljoin(req.full_url, newurl)
        _validate_public_url(target)
        return super().redirect_request(req, fp, code, msg, headers, target)


class _ReadableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._ignored_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._ignored_depth:
            return

        text = " ".join(data.split())
        if not text:
            return

        self.parts.append(text)
        if self._in_title:
            self.title_parts.append(text)


def _extract_readable_text(raw: str, content_type: str) -> tuple[str, str]:
    if "html" not in content_type:
        text = re.sub(r"\s+", " ", raw).strip()
        return "", text[:MAX_TEXT_CHARS]

    parser = _ReadableHTMLParser()
    parser.feed(raw)

    title = " ".join(parser.title_parts).strip()
    text = unescape(" ".join(parser.parts))
    text = re.sub(r"\s+", " ", text).strip()
    return title, text[:MAX_TEXT_CHARS]


def web_fetch(url: str) -> dict:
    """Fetch readable text from one public HTTP(S) page."""
    url = url.strip()
    if not url:
        return {"success": False, "error": "URL cannot be empty."}

    try:
        _validate_public_url(url)

        request = Request(
            url,
            headers={
                "User-Agent": "NENUX-Core/0.11 (+read-only web verification)",
                "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1",
            },
        )

        opener = build_opener(_SafeRedirectHandler())
        with opener.open(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            _validate_public_url(final_url)

            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"

            raw_bytes = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw_bytes) > MAX_RESPONSE_BYTES:
                raw_bytes = raw_bytes[:MAX_RESPONSE_BYTES]

            raw = raw_bytes.decode(charset, errors="replace")
            title, text = _extract_readable_text(raw, content_type)

        return {
            "success": True,
            "url": final_url,
            "title": title,
            "content_type": content_type,
            "text": text,
            "truncated": len(raw_bytes) >= MAX_RESPONSE_BYTES or len(text) >= MAX_TEXT_CHARS,
        }

    except Exception as exc:
        return {
            "success": False,
            "url": url,
            "error": str(exc),
        }
