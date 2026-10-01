# Signature: Mourad.Soltani
"""Minimal JSON server. Stdlib only."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from noticecliff import SIGNATURE, __version__
from noticecliff.calculator import NoticeCliffError, compute_cliff

EXAMPLES = [
    {
        "name": "Annual design tool",
        "renewal_date": "2026-12-01",
        "notice_days": 30,
        "count_mode": "calendar",
        "buffer_days": 2,
    },
    {
        "name": "Seat license, business-day notice",
        "renewal_date": "2026-11-16",
        "notice_days": 10,
        "count_mode": "business",
        "buffer_days": 0,
    },
]


class Handler(BaseHTTPRequestHandler):
    server_version = "NoticeCliff/0.1.0"

    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Signature", SIGNATURE)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"status": "ok", "service": "noticecliff", "version": __version__, "signature": SIGNATURE})
            return
        if path == "/v1/examples":
            self._send(200, {"examples": EXAMPLES, "signature": SIGNATURE})
            return
        self._send(404, {"error": "not found", "signature": SIGNATURE})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/v1/cliff":
            self._send(404, {"error": "not found", "signature": SIGNATURE})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json", "signature": SIGNATURE})
            return
        try:
            result = compute_cliff(
                renewal_date=data.get("renewal_date", ""),
                notice_days=data.get("notice_days", 0),
                count_mode=data.get("count_mode", "calendar"),
                buffer_days=data.get("buffer_days", 0),
                as_of=data.get("as_of"),
                skip_dates=data.get("skip_dates") or [],
            )
        except NoticeCliffError as exc:
            self._send(400, {"error": str(exc), "signature": SIGNATURE})
            return
        self._send(200, result.to_dict())


def serve(port: int = 8765, host: str = "127.0.0.1") -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(json.dumps({"listening": host, "port": port, "signature": SIGNATURE}))
    httpd.serve_forever()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="noticecliff-server")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)
    serve(args.port, args.host)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
