import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class PreviewAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["real_ai_enabled"])

    def test_modules_are_not_connected(self):
        modules = self.client.get("/api/v1/modules").json()
        self.assertEqual(len(modules), 7)
        self.assertTrue(all(m["status"] == "not_connected" for m in modules))

    def test_meihua_present(self):
        self.assertIn("meihua", {m["id"] for m in self.client.get("/api/v1/modules").json()})

    def test_config_has_exact_public_fields(self):
        config = self.client.get("/api/v1/config").json()
        self.assertEqual(set(config), {"mode", "provider_name", "model_name", "real_ai_enabled", "production_connected", "credentials_checked", "history_mode"})
        self.assertTrue(config["credentials_checked"])
        self.assertEqual(config["provider_name"], "deepseek")

    def test_preview_history_is_empty_and_isolated(self):
        self.assertEqual(self.client.get("/api/v1/history").json(), {"items": [], "total": 0, "mode": "isolated_preview", "production_connected": False})

    def test_readings_are_disabled(self):
        self.assertEqual(self.client.post("/api/v1/readings", json={"question": "test"}).status_code, 501)

    def test_upstream_divination_not_exposed(self):
        self.assertEqual(self.client.post("/api/divination").status_code, 404)

    def test_untrusted_origin_is_blocked(self):
        self.assertEqual(self.client.get("/api/v1/config", headers={"Origin": "https://example.invalid"}).status_code, 403)

    def test_local_frontend_origin_is_allowed(self):
        self.assertEqual(self.client.get("/api/v1/config", headers={"Origin": "http://127.0.0.1:5173"}).status_code, 200)

    def test_untrusted_host_is_blocked(self):
        self.assertEqual(self.client.get("/api/v1/health", headers={"Host": "evil.invalid"}).status_code, 400)

    def test_client_secret_headers_not_accepted_or_echoed(self):
        for header in ("Authorization", "x-api-key", "x-api-url", "x-api-model"):
            with self.subTest(header=header):
                response = self.client.get("/api/v1/config", headers={header: "SYNTHETIC_TEST_VALUE"})
                self.assertEqual(response.status_code, 400)
                self.assertNotIn("SYNTHETIC_TEST_VALUE", response.text)

    def test_security_headers(self):
        headers = self.client.get("/api/v1/config").headers
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        self.assertEqual(headers["cache-control"], "no-store")


if __name__ == "__main__":
    unittest.main()
