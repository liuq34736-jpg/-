import io
import json
import tempfile
import unittest
from dataclasses import replace
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, ProxyHandler, build_opener
from urllib.response import addinfourl

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.deepseek import (
    ENDPOINT, MODEL, MAX_RESPONSE_BYTES, DeepSeekConfig, DeepSeekConnectivityProvider,
    NoRedirectHandler, ProviderFailure, load_config, public_status, strict_json,
)


FAKE_KEY = "SYNTHETIC_TEST_VALUE"


def envelope(content='{"status":"ok"}', **extra):
    return json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": content}}], **extra}).encode()


class Response:
    def __init__(self, data=None, status=200):
        self.status = status
        self.data = data if data is not None else envelope()
        self.limit = None
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self, limit):
        self.limit = limit
        return self.data[:limit]


class DeepSeekTransportTests(unittest.TestCase):
    def probe(self, response=None, error=None):
        calls = []
        def transport(request, *, timeout):
            calls.append((request, timeout))
            if error is not None:
                raise error
            return response if response is not None else Response()
        result = DeepSeekConnectivityProvider(DeepSeekConfig(api_key=FAKE_KEY), transport=transport).check_connection()
        self.assertEqual(len(calls), 1)
        self.assertEqual(result.attempts, 1)
        self.assertFalse(result.retried)
        self.assertNotIn(FAKE_KEY, json.dumps(result.public_record()))
        return result, calls

    def test_explicit_environment_config(self):
        config = load_config({"DEEPSEEK_API_KEY": FAKE_KEY})
        self.assertTrue(config.configured)
        self.assertEqual((config.provider_name, config.model_name, config.endpoint), ("deepseek", MODEL, ENDPOINT))

    def test_empty_explicit_environment_does_not_read_user_key(self):
        self.assertFalse(load_config({}).configured)

    def test_secret_not_in_repr(self):
        self.assertNotIn(FAKE_KEY, repr(DeepSeekConfig(api_key=FAKE_KEY)))

    def test_invalid_credential_header_format_is_not_configured(self):
        for key in ("", "bad\nheader", "bad\rheader", "short", "非ASCII凭据"):
            self.assertFalse(DeepSeekConfig(api_key=key).configured)

    def test_configuration_strict_origin_model_and_timeout(self):
        original = DeepSeekConfig(api_key=FAKE_KEY)
        for changes in ({"endpoint": "http://api.deepseek.com/chat/completions"},
                        {"endpoint": "https://example.invalid/chat/completions"},
                        {"endpoint": ENDPOINT + "?redirect=1"}, {"model_name": "bad\nmodel"},
                        {"provider_name": "other"}, {"timeout_seconds": 0}, {"timeout_seconds": 31}):
            with self.assertRaises(ProviderFailure):
                DeepSeekConnectivityProvider(replace(original, **changes))

    def test_no_configuration_means_zero_calls(self):
        with patch("backend.app.deepseek.open_https") as transport:
            result = DeepSeekConnectivityProvider(DeepSeekConfig(), transport=transport).check_connection()
            transport.assert_not_called()
        self.assertEqual(result.result_code, "not_configured")
        self.assertEqual(result.attempts, 0)

    def test_fixed_minimal_nonstreaming_request(self):
        result, calls = self.probe()
        self.assertTrue(result.success)
        request, timeout = calls[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, ENDPOINT)
        self.assertEqual(timeout, 20)
        self.assertEqual(request.get_header("Authorization"), "Bearer " + FAKE_KEY)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["max_tokens"], 32)
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertNotIn("generate", dir(DeepSeekConnectivityProvider))

    def test_all_redirects_blocked_without_second_request(self):
        for code in (302, 307, 308):
            for destination in ("https://example.invalid/collect", "http://api.deepseek.com/collect", ENDPOINT):
                with self.subTest(code=code, destination=destination):
                    observed = []
                    class FakeHTTPS(HTTPSHandler):
                        def https_open(self, request):
                            observed.append(request.full_url)
                            headers = Message()
                            headers["Location"] = destination
                            response = addinfourl(io.BytesIO(b""), headers, request.full_url, code)
                            response.msg = "Redirect"
                            return response
                    opener = build_opener(ProxyHandler({}), FakeHTTPS(), NoRedirectHandler())
                    provider = DeepSeekConnectivityProvider(DeepSeekConfig(api_key=FAKE_KEY), transport=opener.open)
                    result = provider.check_connection()
                    self.assertFalse(result.success)
                    self.assertEqual(result.result_code, "redirect_blocked")
                    self.assertEqual(observed, [ENDPOINT])

    def test_http_failures_do_not_retry_or_read_error_body(self):
        class UnreadableBody(io.BytesIO):
            def read(self, *_): raise AssertionError("error body read")
        for status in (401, 403, 429, 500, 502):
            result, _ = self.probe(error=HTTPError(ENDPOINT, status, FAKE_KEY, {}, UnreadableBody(FAKE_KEY.encode())))
            self.assertEqual(result.http_status, status)
            self.assertEqual(result.result_code, "http_failure")

    def test_network_failures_are_sanitized(self):
        for error in (TimeoutError(FAKE_KEY), URLError(FAKE_KEY), ConnectionError(FAKE_KEY)):
            result, _ = self.probe(error=error)
            self.assertEqual(result.result_code, "network_failure")

    def test_unknown_exception_is_sanitized(self):
        result, _ = self.probe(error=RuntimeError(FAKE_KEY))
        self.assertEqual(result.result_code, "internal_failure")

    def test_arbitrary_provider_error_code_cannot_leak(self):
        result, _ = self.probe(error=ProviderFailure(FAKE_KEY))
        self.assertEqual(result.result_code, "internal_failure")

    def test_http_status_cannot_contain_untrusted_text(self):
        result, _ = self.probe(Response(status=FAKE_KEY))
        self.assertIsNone(result.http_status)
        self.assertFalse(result.success)

    def test_empty_content_is_rejected(self):
        for content in ("", " ", None):
            result, _ = self.probe(Response(envelope(content)))
            self.assertFalse(result.success)

    def test_invalid_json_schema_and_free_text_rejected(self):
        for content in ("ok", '{"status":"wrong"}', '{"status":"ok","prediction":"成功"}',
                        '[{"status":"ok"}]', '{"status":"ok","status":"ok"}', '{"status":NaN}'):
            result, _ = self.probe(Response(envelope(content)))
            self.assertFalse(result.success)

    def test_malformed_envelope_rejected(self):
        for data in (b"not-json", b"{}", b'{"choices":[]}', b"\xff"):
            result, _ = self.probe(Response(data))
            self.assertFalse(result.success)

    def test_incomplete_finish_reason_rejected(self):
        raw = json.loads(envelope())
        raw["choices"][0]["finish_reason"] = "length"
        result, _ = self.probe(Response(json.dumps(raw).encode()))
        self.assertEqual(result.result_code, "incomplete_response")

    def test_response_size_bounded(self):
        response = Response(b"x" * (MAX_RESPONSE_BYTES + 50))
        result, _ = self.probe(response)
        self.assertEqual(response.limit, MAX_RESPONSE_BYTES + 1)
        self.assertEqual(result.result_code, "response_too_large")

    def test_credential_echo_rejected(self):
        result, _ = self.probe(Response(envelope(FAKE_KEY)))
        self.assertEqual(result.result_code, "unsafe_response")

    def test_usage_only_accepts_integer_metrics(self):
        result, _ = self.probe(Response(envelope(usage={"prompt_tokens": 12, "completion_tokens": 5,
                                                       "total_tokens": 17, "headers": "EXCLUDED_METADATA"})))
        self.assertEqual((result.prompt_tokens, result.completion_tokens, result.total_tokens), (12, 5, 17))
        result, _ = self.probe(Response(envelope(usage={"prompt_tokens": True, "completion_tokens": -1, "total_tokens": FAKE_KEY})))
        self.assertEqual((result.prompt_tokens, result.completion_tokens, result.total_tokens), (None, None, None))

    def test_duplicate_keys_cannot_be_silently_normalized(self):
        with self.assertRaises(ValueError): strict_json('{"status":"bad","status":"ok"}')

    def test_public_status_exact_whitelist(self):
        status = public_status(DeepSeekConfig(api_key=FAKE_KEY))
        self.assertEqual(set(status), {"provider_name", "model_name", "endpoint", "configured", "configuration_status", "integration_status", "reading_enabled"})
        self.assertTrue(status["configured"])
        self.assertFalse(status["reading_enabled"])
        self.assertNotIn(FAKE_KEY, json.dumps(status))

    def test_one_shot_cli_guard(self):
        from scripts import check_deepseek_connectivity as cli
        result, _ = self.probe()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            with patch.object(cli, "ROOT", root), patch.object(cli, "load_config", return_value=DeepSeekConfig(api_key=FAKE_KEY)), patch.object(cli, "DeepSeekConnectivityProvider") as provider:
                provider.return_value.check_connection.return_value = result
                self.assertTrue(cli.run_real_once()["success"])
                self.assertEqual(cli.run_real_once()["reason"], "already_attempted")
                provider.return_value.check_connection.assert_called_once()
            report = (root / "docs/day3_api_connectivity_result.json").read_text()
            self.assertNotIn(FAKE_KEY, report)
            self.assertNotIn("Authorization", report)


class Day3BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_status_queries_make_no_upstream_call(self):
        with patch("backend.app.deepseek.load_config", return_value=DeepSeekConfig(api_key=FAKE_KEY)), patch("backend.app.deepseek.open_https") as network:
            for _ in range(3):
                response = self.client.get("/api/v1/ai/status")
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(FAKE_KEY, response.text)
            network.assert_not_called()

    def test_client_cannot_start_a_connectivity_call(self):
        for path in ("/api/v1/ai/connectivity", "/api/v1/ai/generate", "/api/v1/chat/completions"):
            self.assertEqual(self.client.post(path).status_code, 404)

    def test_cors_local_only_no_credentials(self):
        response = self.client.options("/api/v1/ai/status", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "GET"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://127.0.0.1:5173")
        self.assertNotIn("access-control-allow-credentials", response.headers)
        self.assertEqual(self.client.options("/api/v1/ai/status", headers={"Origin": "https://evil.invalid", "Access-Control-Request-Method": "GET"}).status_code, 403)

    def test_cors_preflight_cannot_authorize_client_key_header(self):
        response = self.client.options("/api/v1/ai/status", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "Authorization"})
        self.assertEqual(response.status_code, 400)

    def test_backend_exception_text_is_not_reflected(self):
        with patch("backend.app.main.load_config", side_effect=RuntimeError(FAKE_KEY)):
            response = self.client.get("/api/v1/config")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(FAKE_KEY, response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_errors_keep_security_headers(self):
        response = self.client.get("/api/v1/config", headers={"Authorization": FAKE_KEY})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(FAKE_KEY, response.text)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_unreviewed_readings_stay_disabled(self):
        self.assertEqual(self.client.post("/api/v1/readings", json={"question": "生意怎么样"}).status_code, 422)
        self.assertEqual(self.client.get("/openapi.json").status_code, 404)

    def test_legacy_html_sink_removed_and_no_production_imports(self):
        root = Path(__file__).resolve().parents[1]
        self.assertNotIn("dangerouslySetInnerHTML", (root / "frontend/src/components/ResultDrawer.tsx").read_text(encoding="utf-8"))
        app_code = (root / "backend/app/main.py").read_text(encoding="utf-8")
        self.assertNotIn("from iching", app_code)
        self.assertNotIn("sqlite3", app_code)


if __name__ == "__main__":
    unittest.main()
