"""Version-pinned, bounded adapter. Never imports a production repository."""

import json
import os
from pathlib import Path
import subprocess
import sys
from threading import BoundedSemaphore

from backend.app.meihua_models import (CalculationResult, CatalogResult, ReadingResponse, ManualInput, TimeInput)

ROOT = Path(__file__).resolve().parents[2]


class MeihuaUnavailable(Exception):
    def __init__(self):
        super().__init__("冻结计算服务暂不可用，请检查本地服务和版本基线。")


class MeihuaServiceAdapter:
    version = "meihua_service_adapter_v1"

    def __init__(self):
        self._slots = BoundedSemaphore(2)

    def _run(self, payload):
        if not self._slots.acquire(blocking=False):
            raise MeihuaUnavailable()
        try:
            # No API/signing credentials in the child environment.
            environment = {key: value for key, value in os.environ.items()
                           if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
            environment["PYTHONIOENCODING"] = "utf-8"
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
            completed = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(ROOT / "backend/app/meihua_worker.py")],
                input=json.dumps(payload, ensure_ascii=True).encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=ROOT, env=environment, timeout=20, check=False, **options)
            if completed.returncode != 0 or len(completed.stdout) > 256_000:
                raise MeihuaUnavailable()
            return json.loads(completed.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            raise MeihuaUnavailable() from None
        finally:
            self._slots.release()

    def catalog(self):
        try:
            return CatalogResult.model_validate(self._run({"operation": "catalog"}))
        except ValueError:
            raise MeihuaUnavailable() from None

    def calculate(self, request: ManualInput | TimeInput):
        if type(request) not in {ManualInput, TimeInput}:
            raise MeihuaUnavailable()
        payload = request.model_dump(exclude={"question_text"})
        try:
            result = CalculationResult.model_validate(self._run({"operation": "calculate", "data": payload}))
            return ReadingResponse.model_validate({**result.model_dump(), "question_text": request.question_text,
                                                  "question_applied_to_calculation": False})
        except ValueError:
            raise MeihuaUnavailable() from None
