"""Dependency-free local demo server and JSON analysis API."""

from __future__ import annotations

import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from pydantic import ValidationError

from northstar.contracts import ProgramScenario
from northstar.orchestrator import DecisionOrchestrator
from northstar.providers import ProviderError, build_provider

MAX_BODY_BYTES = 2_000_000
WEB_ROOT = Path(__file__).resolve().parent / "web"
EXAMPLE_SCENARIO = Path(__file__).resolve().parents[2] / "examples" / "synthetic_portfolio.json"


class NorthstarHandler(BaseHTTPRequestHandler):
    server_version = "NorthstarDemo/0.1"

    def log_message(self, format: str, *args: object) -> None:
        # Intentionally avoid request-body or query logging; scenarios may be sensitive.
        del format, args

    def _json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(HTTPStatus.OK, {"status": "ok", "provider": os.environ.get("NORTHSTAR_PROVIDER", "offline")})
            return
        if path == "/api/report":
            try:
                scenario = ProgramScenario.model_validate_json(EXAMPLE_SCENARIO.read_text(encoding="utf-8"))
                report = DecisionOrchestrator(provider=build_provider()).run(scenario)
                self._json(HTTPStatus.OK, report.model_dump(mode="json"))
            except (OSError, ValidationError, ProviderError):
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "demo report unavailable"})
            return
        relative = "index.html" if path == "/" else path.removeprefix("/static/").lstrip("/")
        candidate = (WEB_ROOT / relative).resolve()
        try:
            candidate.relative_to(WEB_ROOT.resolve())
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_types = {
            ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
        }
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_types.get(candidate.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid request size"})
                return
            raw = json.loads(self.rfile.read(length))
            scenario = ProgramScenario.model_validate(raw)
            report = DecisionOrchestrator(provider=build_provider()).run(scenario)
            self._json(HTTPStatus.OK, report.model_dump(mode="json"))
        except json.JSONDecodeError:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "request body must be valid JSON"})
        except ValidationError as exc:
            # Do not echo invalid input; Pydantic error strings can reproduce sensitive values.
            self._json(HTTPStatus.BAD_REQUEST, {
                "error": "invalid scenario",
                "details": f"{exc.error_count()} validation issue(s)",
            })
        except ProviderError as exc:
            self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})
        except Exception:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "analysis failed safely"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the local Northstar demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), NorthstarHandler)
    print(f"Northstar is available at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
