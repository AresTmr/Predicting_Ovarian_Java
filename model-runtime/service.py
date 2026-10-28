from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from runtime.analysis_service import AnalysisService


SERVICE = AnalysisService(ROOT)


class Handler(BaseHTTPRequestHandler):
    server_version = "OvarianModelRuntime/0.2"

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": "ovarian-model-runtime",
                    "version": "day2",
                    "pythonVersion": platform.python_version(),
                    "runtimePrefix": sys.prefix,
                    "doseModels": list(SERVICE.dose_runtime.models.keys()),
                    "outcomeTasks": ["layer2_oocytes", "layer2_mii", "layer2_ohss"],
                },
            )
            return
        if self.path == "/models":
            self._send(
                HTTPStatus.OK,
                {
                    "dose": {
                        target: {
                            "labels": config["labels"],
                            "staticFeatures": config["staticFeatures"],
                            "dynamicFeatures": config["dynamicFeatures"],
                        }
                        for target, config in SERVICE.dose_runtime.configs.items()
                    },
                    "outcome": {
                        "efficacyRunId": SERVICE.candidate_runtime.efficacy_bundle.get("run_id"),
                        "safetyRunId": SERVICE.candidate_runtime.safety_bundle.get("run_id"),
                    },
                },
            )
            return
        self._send(HTTPStatus.NOT_FOUND, {"status": "ERROR", "error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/analyze":
            self._send(HTTPStatus.NOT_FOUND, {"status": "ERROR", "error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            patient = payload.get("patient")
            records = payload.get("records")
            if not isinstance(patient, dict) or not isinstance(records, list):
                raise ValueError("Request must contain object patient and array records")
            result = SERVICE.analyze(patient, records)
            self._send(HTTPStatus.OK, result)
        except Exception as exc:
            self._send(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"status": "ERROR", "error": type(exc).__name__, "message": str(exc)},
            )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local model runtime HTTP service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Model runtime listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
