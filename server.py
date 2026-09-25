#!/usr/bin/env python3
"""A deliberately small, loopback-only object authorization teaching lab."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from urllib.parse import urlsplit


INVOICES = {
    "1001": {"id": "1001", "owner": "alice", "amount_chf": 120,
             "description": "Synthetic training invoice A"},
    "1002": {"id": "1002", "owner": "bob", "amount_chf": 240,
             "description": "Synthetic training invoice B"},
}
USERS = frozenset({"alice", "bob"})


def make_server(port=0, mode="fixed"):
    """Bind IPv4 loopback only. No option is provided to expose the lab remotely."""
    if mode not in {"fixed", "vulnerable"}:
        raise ValueError("mode must be fixed or vulnerable")

    class Handler(BaseHTTPRequestHandler):
        server_version = "AuthorizationLab/1.0"
        sys_version = ""

        def log_message(self, *_args):
            pass

        def respond(self, status, data):
            body = (json.dumps(data, sort_keys=True) + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/health":
                self.respond(200, {"status": "ok", "mode": mode,
                                   "data": "synthetic"})
                return
            match = re.fullmatch(r"/api/invoices/([0-9]+)", path)
            if not match:
                self.respond(404, {"error": "not_found"})
                return

            # TEST HARNESS ONLY: this header simulates an already-authenticated
            # principal. It is user-controlled and is NOT an authentication system.
            headers = self.headers.get_all("X-Demo-User", [])
            principal = headers[0] if len(headers) == 1 else None
            if principal not in USERS:
                self.respond(401, {"error": "demo_identity_required"})
                return

            invoice = INVOICES.get(match.group(1))
            if invoice is None:
                self.respond(404, {"error": "not_found"})
                return

            # The vulnerable branch intentionally omits the object-level check.
            # In a real service, obtain principal from trusted authentication
            # middleware and apply its complete access policy on every route.
            if mode == "fixed" and invoice["owner"] != principal:
                self.respond(403, {"error": "forbidden"})
                return
            self.respond(200, invoice)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mode", choices=("fixed", "vulnerable"), default="fixed")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    server = make_server(args.port, args.mode)
    print(f"{args.mode} lab: http://127.0.0.1:{server.server_port}", flush=True)
    print("Synthetic data; X-Demo-User simulates identity, not real authentication.",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
