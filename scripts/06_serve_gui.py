#!/usr/bin/env python3
"""Serve only the Knowledge Prism public front end.

Do not use `python3 -m http.server` from the project root: that exposes the
entire workspace, including local-only data and secrets. This tiny server serves
only the public HTML pages and generated JSON exports needed by the front end.
"""
from __future__ import annotations

import argparse
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_HTML = {
    "/": ROOT / "index.html",
    "/index.html": ROOT / "index.html",
    "/dashboard.html": ROOT / "dashboard.html",
    "/case-study-ir.html": ROOT / "case-study-ir.html",
    "/method.html": ROOT / "method.html",
}
PUBLIC_DATA = ROOT / "public" / "data"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        target = self.resolve_target(path)
        if target is None:
            self.send_error(404, "Only public Knowledge Prism pages and generated JSON are served")
            return
        body = target.read_bytes()
        self.send_response(200)
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/json":
            content_type = f"{content_type}; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def resolve_target(self, path: str) -> Path | None:
        if path in ALLOWED_HTML:
            target = ALLOWED_HTML[path]
            return target if target.exists() else None
        if not path.startswith("/public/data/") or not path.endswith(".json"):
            return None
        target = (ROOT / path.lstrip("/")).resolve()
        try:
            target.relative_to(PUBLIC_DATA.resolve())
        except ValueError:
            return None
        return target if target.exists() and target.is_file() else None

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve only public Knowledge Prism front-end files.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving Knowledge Prism front end at http://{args.host}:{args.port}/")
    print("Only public HTML pages and /public/data/*.json are exposed.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")


if __name__ == "__main__":
    main()
