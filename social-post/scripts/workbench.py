#!/usr/bin/env python3
"""Launch the local-only Social Post Workbench. No provider or Meta API."""

from __future__ import annotations

import argparse
import hmac
import json
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from workbench_contract import VERSION, parse_json
from workbench_service import WorkbenchService
from workbench_store import list_drafts, safe_path

SKILL_ROOT = Path(__file__).absolute().parents[1]
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/layout.css": ("layout.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/ui.js": ("ui.js", "text/javascript; charset=utf-8"),
    "/editor.js": ("editor.js", "text/javascript; charset=utf-8"),
    "/api.js": ("api.js", "text/javascript; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}
BODY_LIMIT = 128 * 1024


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 16

    def __init__(self, root: Path, port: int, static_root: Path | None = None):
        self.service = WorkbenchService(root)
        self.static_root = static_root or SKILL_ROOT / "workbench"
        self.session = secrets.token_urlsafe(32)
        self.csrf = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), WorkbenchHandler)
        self.origin = "http://127.0.0.1:" + str(self.server_port)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address


class WorkbenchHandler(BaseHTTPRequestHandler):
    server: WorkbenchServer
    server_version = "SocialPost"
    sys_version = ""

    def log_message(self, *args):
        pass  # Do not put private text, paths or credentials in access logs.

    def send(self, status: int, content, mime="application/json; charset=utf-8", set_session=False):
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; img-src 'self'; font-src 'self'; "
                         "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        if set_session:
            self.send_header("Set-Cookie", "sp_session=" + self.server.session
                             + "; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(content)

    def request_safe(self) -> bool:
        hosts = self.headers.get_all("Host", [])
        expected = "127.0.0.1:" + str(self.server.server_port)
        if hosts != [expected] or len(self.path) > 2048:
            return False
        if self.headers.get("Sec-Fetch-Site") not in {None, "same-origin", "none"}:
            return False
        if self.headers.get_all("Origin", []) not in ([], [self.server.origin]):
            return False
        try:
            parsed = urlsplit(self.path)
            return parsed.netloc == "" and not parsed.query
        except ValueError:
            return False

    def authenticated(self) -> bool:
        values = [part.strip().split("=", 1) for part in self.headers.get("Cookie", "").split(";")]
        matching = [pair[1] for pair in values if len(pair) == 2 and pair[0] == "sp_session"]
        return len(matching) == 1 and hmac.compare_digest(
            matching[0].encode("utf-8"), self.server.session.encode("ascii"))

    def do_GET(self):
        if not self.request_safe():
            self.send(403, {"error": "request_denied"})
            return
        route = urlsplit(self.path).path
        if route in STATIC_FILES:
            name, mime = STATIC_FILES[route]
            try:
                raw = safe_path(self.server.static_root, name).read_bytes()
                if route == "/":
                    raw = raw.replace(b"__CSRF_TOKEN__", self.server.csrf.encode("ascii"))
                self.send(200, raw, mime, set_session=route == "/")
            except (OSError, ValueError):
                self.send(404, {"error": "asset_unavailable"})
            return
        if not self.authenticated():
            self.send(401, {"error": "session_required"})
            return
        try:
            if route == "/api/catalog":
                result = self.server.service.catalog()
            elif route == "/api/overview":
                result = self.server.service.overview()
            elif route == "/api/drafts":
                result = list_drafts(self.server.service.root)
            elif route == "/api/outcome/example":
                result = parse_json(safe_path(SKILL_ROOT, "references/outcome-bundle.example.json").read_bytes())
            elif route.startswith("/api/drafts/"):
                result = self.server.service.draft(route.removeprefix("/api/drafts/"))
            else:
                raise KeyError("route")
            self.send(200, result)
        except KeyError:
            self.send(404, {"error": "not_found"})
        except (OSError, ValueError, RuntimeError):
            self.send(422, {"error": "local_data_unavailable"})

    def do_POST(self):
        if not self.request_safe() or self.headers.get("Origin") != self.server.origin:
            self.send(403, {"error": "request_denied"})
            return
        supplied = self.headers.get("X-Social-Post-CSRF", "")
        if not self.authenticated() or not hmac.compare_digest(supplied.encode("utf-8"), self.server.csrf.encode("ascii")):
            self.send(403, {"error": "request_denied"})
            return
        if self.headers.get("Content-Type") != "application/json" or self.headers.get("Transfer-Encoding"):
            self.send(415, {"error": "json_required"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or len(lengths[0]) > 6 or not lengths[0].isdecimal():
            self.send(411, {"error": "length_required"})
            return
        size = int(lengths[0])
        if not 0 < size <= BODY_LIMIT:
            self.send(413, {"error": "body_too_large"})
            return
        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError("incomplete body")
            payload = parse_json(raw)
            result = self.server.service.dispatch(urlsplit(self.path).path, payload)
            self.send(200, result)
        except KeyError:
            self.send(404, {"error": "not_found"})
        except (ValueError, UnicodeError, RecursionError, TypeError, AttributeError):
            self.send(422, {"error": "invalid_input"})
        except (RuntimeError, TimeoutError):
            self.send(409, {"error": "state_changed"})
        except OSError:
            self.send(422, {"error": "local_data_unavailable"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SKILL_ROOT, help="Private Social Post data root")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    try:
        server = WorkbenchServer(args.root, args.port)
    except (OSError, ValueError):
        print("Workbench could not start: check workspace, linked paths and port.", file=sys.stderr)
        return 2
    print("Social Post Workbench " + VERSION + " | " + server.origin, flush=True)
    print("Local only. Press Ctrl+C to stop. No external publishing or reply automation.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
