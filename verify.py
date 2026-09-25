#!/usr/bin/env python3
"""Exercise only servers created by this script; emit actual local HTTP evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
from pathlib import Path
import platform
import threading

from server import make_server


CASES = (
    ("alice_own", "alice", "1001", 200, 200),
    ("alice_cross", "alice", "1002", 200, 403),
    ("bob_own", "bob", "1002", 200, 200),
    ("bob_cross", "bob", "1001", 200, 403),
    ("no_identity", None, "1001", 401, 401),
    ("unknown_identity", "mallory", "1001", 401, 401),
    ("missing_object", "alice", "9999", 404, 404),
)


def request(port, path, user=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        headers = {} if user is None else {"X-Demo-User": user}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def capture():
    records = []
    for mode in ("vulnerable", "fixed"):
        server = make_server(mode=mode)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for name, user, invoice_id, vulnerable_status, fixed_status in CASES:
                path = f"/api/invoices/{invoice_id}"
                status, body = request(server.server_port, path, user)
                expected = vulnerable_status if mode == "vulnerable" else fixed_status
                passed = status == expected
                if status == 200:
                    expected_owner = "alice" if invoice_id == "1001" else "bob"
                    passed = passed and body.get("owner") == expected_owner
                elif mode == "fixed" and name.endswith("_cross"):
                    passed = passed and body == {"error": "forbidden"}
                records.append({"case": name, "mode": mode, "method": "GET",
                                "path": path, "demo_user": user,
                                "status": status, "response": body,
                                "expected_status": expected, "passed": passed})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
    return {"schema_version": 1,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "environment": {"python": platform.python_version(),
                            "target": "self-created IPv4 loopback servers"},
            "server_sha256": hashlib.sha256(
                Path(__file__).with_name("server.py").read_bytes()).hexdigest(),
            "scope": "Synthetic invoices; identity is simulated; no external targets.",
            "passed": all(item["passed"] for item in records), "records": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = capture()
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        # Preserve existing evidence; choose a new path for another run.
        with args.output.open("x", encoding="utf-8") as target:
            target.write(rendered)
    else:
        print(rendered, end="")
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
