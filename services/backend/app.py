"""Backend HTTP service for controlled incident experiments."""

import json
import logging
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


SERVICE_NAME = "backend"
PORT = int(os.environ.get("PORT", "8080"))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(SERVICE_NAME)


def emit_event(event: str, **fields: object) -> None:
    """Record a structured operational event."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": SERVICE_NAME,
        "event": event,
        **fields,
    }
    logger.info(json.dumps(record))


class BackendHandler(BaseHTTPRequestHandler):
    """Handle backend API requests."""

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

        if path == "/data":
            request_id = self.headers.get("X-Request-ID", "")

            emit_event(
                "request_received",
                request_id=request_id,
                path=path,
            )

            self.send_json(200, {
                "service": SERVICE_NAME,
                "result": "success",
                "request_id": request_id,
            })
            return

        self.send_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default HTTP logs; use structured events."""
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        BackendHandler,
    )

    emit_event("service_started", port=PORT)
    server.serve_forever()
