import http.client
import threading
import unittest

from server import make_server
from verify import capture, request


class AuthorizationTests(unittest.TestCase):
    def test_entire_http_access_matrix(self):
        evidence = capture()
        self.assertEqual(len(evidence["records"]), 14)
        for record in evidence["records"]:
            with self.subTest(mode=record["mode"], case=record["case"]):
                self.assertTrue(record["passed"], record)

    def setUp(self):
        self.server = make_server()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def test_fixed_is_default_and_loopback_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, body = request(self.server.server_port, "/health")
        self.assertEqual((status, body["mode"]), (200, "fixed"))
        self.assertEqual(request(self.server.server_port,
                                 "/api/invoices/1002", "alice"),
                         (403, {"error": "forbidden"}))

    def test_query_user_cannot_override_principal(self):
        self.assertEqual(request(self.server.server_port,
                                 "/api/invoices/1002?user=bob", "alice")[0], 403)

    def test_unknown_route_has_no_invoice_data(self):
        self.assertEqual(request(self.server.server_port, "/api/invoices", "alice"),
                         (404, {"error": "not_found"}))

    def test_duplicate_identity_headers_rejected(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port,
                                                timeout=3)
        try:
            connection.putrequest("GET", "/api/invoices/1002")
            connection.putheader("X-Demo-User", "alice")
            connection.putheader("X-Demo-User", "bob")
            connection.endheaders()
            response = connection.getresponse()
            self.assertEqual(response.status, 401)
            self.assertNotIn(b"amount_chf", response.read())
        finally:
            connection.close()

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            make_server(mode="typo")


if __name__ == "__main__":
    unittest.main()
