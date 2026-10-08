# API Authorization Lab

<p><img src="assets/0xfarag-logo.png" alt="0xFarag" width="100"></p>

**One finding. Two implementations. Reproducible HTTP evidence.**

A small Python lab showing an object-level authorization defect in a synthetic invoice API and the effect of a server-side ownership check. Part of Nasser Aldin Farag's Web/API Security portfolio.

## Review in two minutes

1. Read the ownership check in [`server.py`](server.py).
2. Run `python3 verify.py` to exercise both modes on self-created loopback servers.
3. Inspect [`evidence/http-evidence.json`](evidence/http-evidence.json): Alice can read Bob's invoice in vulnerable mode; the same request receives `403` in fixed mode.

## Run

Python 3.12+; standard library only. On Windows, replace `python3` with `py -3`.

```bash
python3 -m unittest -v
python3 verify.py
python3 server.py
```

The default server runs the **fixed** variant at `http://127.0.0.1:8000`. Stop with Ctrl+C. To explore the deliberately vulnerable branch:

```bash
python3 server.py --mode vulnerable --port 8001
curl -i -H "X-Demo-User: alice" http://127.0.0.1:8001/api/invoices/1002
```

Then make the same request to the fixed server on port 8000. Use `curl.exe` on Windows PowerShell if `curl` is an alias. The verification script requires no curl installation.

## What the experiment establishes

| Request | Vulnerable | Fixed |
| --- | --- | --- |
| Alice reads invoice 1001 (Alice's) | 200 | 200 |
| Alice reads invoice 1002 (Bob's) | 200; Bob's object disclosed | 403; no invoice fields |
| Bob reads invoice 1002 (Bob's) | 200 | 200 |
| Bob reads invoice 1001 (Alice's) | 200; Alice's object disclosed | 403; no invoice fields |
| Missing or unknown demo identity | 401 | 401 |
| Known identity requests absent invoice | 404 | 404 |

The response status and returned object are checked together. Merely hiding an identifier in a user interface would not enforce the ownership policy on the server.

## Scope and limitations

- `X-Demo-User` **simulates an already authenticated principal**. Anyone running the demo can choose Alice or Bob. It is not real authentication, and the fixed variant is not a production-secure service.
- All invoices are synthetic. The application binds to `127.0.0.1` only, with no remote-bind option. Run it in a trusted local environment; do not expose it through a proxy, tunnel or public service.
- Only reading two invoice objects is modelled. There is no database, tenant model, role hierarchy, session handling, write endpoint or concurrency assessment.
- `403` for a foreign object and `404` for an absent object allow existence to be distinguished. A real application needs an explicit error disclosure policy.
- Python's `http.server` is a teaching component here, not a production web stack.

## Evidence

`verify.py` starts each mode, sends seven requests per mode, validates the responses and stops the servers. It accepts no remote target. To preserve a fresh run:

```bash
python3 verify.py --output evidence/my-run.json
```

An existing evidence file is never overwritten. The evidence includes UTC time, Python version and the SHA-256 of `server.py`. The initial run is retained in `evidence/http-evidence.json`.

## Deutsche Kurzfassung

Das Lab belegt eine fehlende Prüfung der Objektberechtigung. Eine bekannte Demo-Identität kann zunächst die Rechnung einer anderen Person abrufen. Nach der Behebung prüft der Server den Eigentümer vor der Ausgabe. Der Retest kontrolliert sowohl die gesperrten Fremdzugriffe als auch weiterhin erlaubte Eigenzugriffe. Die Identität ist für das Experiment bewusst simuliert.

## References

- [OWASP API1:2023 - Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- [Python http.server documentation](https://docs.python.org/3.12/library/http.server.html)

Original educational example; no platform exercises, exam questions or customer material are included. Code: MIT License.
