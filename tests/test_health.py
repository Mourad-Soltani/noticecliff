# Signature: Mourad.Soltani
import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from noticecliff.server import Handler


class HealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_health_ok(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health") as resp:
            body = json.loads(resp.read().decode())
        self.assertEqual(resp.status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["service"], "noticecliff")
        self.assertEqual(body["signature"], "Mourad.Soltani")

    def test_cliff_endpoint(self):
        payload = json.dumps(
            {
                "renewal_date": "2026-12-01",
                "notice_days": 30,
                "count_mode": "calendar",
                "as_of": "2026-10-01",
            }
        ).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/v1/cliff",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())
        self.assertEqual(body["cancel_by"], "2026-11-01")
        self.assertEqual(body["risk"], "safe")
        self.assertEqual(body["signature"], "Mourad.Soltani")

    def test_bad_date(self):
        payload = json.dumps({"renewal_date": "nope", "notice_days": 5}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/v1/cliff",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
