"""Record rejected synthetic requests, without upstream calls or private data."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.app.main import app
from backend.app.meihua_adapter import MeihuaUnavailable


def main():
    client = TestClient(app)
    manual = {"input_mode": "manual_hexagram", "hexagram_id": 20,
              "moving_line": 4, "cast_at": "2026-09-24T19:45:35+08:00"}
    examples = []

    def record(name, response, expected):
        examples.append({"case": name, "expected_status": expected,
                         "actual_status": response.status_code, "response": response.json(),
                         "passed": response.status_code == expected})

    with patch("backend.app.main.meihua_service.calculate") as calculation:
        for name, update in (
            ("hexagram_out_of_range", {"hexagram_id": 65}),
            ("moving_line_out_of_range", {"moving_line": 7}),
            ("boolean_not_integer", {"moving_line": True}),
            ("model_not_allowed", {"model_name": "synthetic"}),
            ("file_path_not_allowed", {"file_path": "synthetic"}),
            ("prompt_not_allowed", {"prompt": "synthetic"}),
            ("question_over_500", {"question_text": "问" * 501}),
            ("timezone_required", {"cast_at": "2026-09-24T19:45:35"}),
            ("invalid_date", {"cast_at": "2026-02-30T19:45:35+08:00"}),
        ):
            record(name, client.post("/api/v1/readings", json={**manual, **update}), 422)
        record("time_input_rejects_hexagram", client.post("/api/v1/readings",
            json={"input_mode": "time_cast", "hexagram_id": 20}), 422)
        record("duplicate_keys", client.post("/api/v1/readings",
            content='{"input_mode":"time_cast","input_mode":"time_cast"}',
            headers={"Content-Type": "application/json"}), 422)
        record("body_over_8192", client.post("/api/v1/readings", content=b" " * 8193,
            headers={"Content-Type": "application/json"}), 413)
        record("json_required", client.post("/api/v1/readings", content="synthetic"), 415)
        record("untrusted_origin", client.post("/api/v1/readings", json=manual,
            headers={"Origin": "https://synthetic.invalid"}), 403)
        record("browser_credentials_rejected", client.post("/api/v1/readings", json=manual,
            headers={"X-API-Key": "SYNTHETIC_NOT_A_CREDENTIAL"}), 400)
        calculation.assert_not_called()
    with patch("backend.app.main.meihua_service.calculate", side_effect=MeihuaUnavailable()):
        record("frozen_service_failure", client.post("/api/v1/readings", json=manual), 503)
    result = {"mode": "offline_testclient", "paid_calls": 0, "examples": examples,
              "passed": sum(x["passed"] for x in examples), "failed": sum(not x["passed"] for x in examples)}
    (ROOT / "docs/day4_api_failure_examples.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "failed": result["failed"], "paid_calls": 0}))
    return int(bool(result["failed"]))


if __name__ == "__main__":
    raise SystemExit(main())
