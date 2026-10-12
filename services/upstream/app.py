"""Upstream HTTP service for controlled incident experiments."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


SERVICE_NAME = "upstream"
PORT = int(os.environ.get("PORT", "8080"))
BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    "http://backend:8080/data",
)
TIMEOUT_SECONDS = float(os.environ.get("BACKEND_TIMEOUT", "2"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(SERVICE_NAME)


def emit_event(event: str, **fields: object) -> None:
    """Emit a structured operational event."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": SERVICE_NAME,
        "event": event,
        **fields,
    }
    logger.info(json.dumps(record))


class UpstreamHandler(BaseHTTPRequestHandler):
    """Handle upstream API requests."""

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path

        if path == "/health":
            self.send_json(200, {
                "service": SERVICE_NAME,
                "status": "healthy",
            })
            return

        if path != "/request":
            self.send_json(404, {"error": "not_found"})
            return

        request_id = str(uuid.uuid4())

        emit_event(
            "dependency_request_started",
            request_id=request_id,
            dependency="backend",
        )

        request = Request(
            BACKEND_URL,
            headers={"X-Request-ID": request_id},
        )

        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                response.read()
                backend_status = response.status

            if backend_status != 200:
                raise RuntimeError(
                    f"Unexpected backend status: {backend_status}"
                )

            emit_event(
                "dependency_request_succeeded",
                request_id=request_id,
                dependency="backend",
                status=backend_status,
            )

            self.send_json(200, {
                "result": "success",
                "request_id": request_id,
            })

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            RuntimeError,
        ) as exc:
            emit_event(
                "dependency_request_failed",
                request_id=request_id,
                dependency="backend",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            self.send_json(502, {
                "error": "dependency_unavailable",
                "request_id": request_id,
            })

    def log_message(self, format: str, *args: object) -> None:
        """Suppress unstructured HTTP access logs."""
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        UpstreamHandler,
    )

    emit_event("service_started", port=PORT)
    server.serve_forever()
