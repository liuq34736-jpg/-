"""Browser input -> fixed guarded worker -> read-only preview; no database/API."""

from threading import BoundedSemaphore
from backend.app.meihua_models import ManualInput, TimeInput, ReadingResponse
from backend.app.meihua_adapter import MeihuaUnavailable
from backend.traditional_judgement_v1.trusted_input import OfflineJudgementAdapter, JudgementUnavailable
from .engine import PreviewJudgementEngine
from .models import PreviewResponse


class TraditionalPreviewService:
    def __init__(self):
        self._slots = BoundedSemaphore(2)
        self._adapter = OfflineJudgementAdapter()
        self._engine = PreviewJudgementEngine()

    def calculate(self, request):
        if type(request) not in {ManualInput, TimeInput} or not self._slots.acquire(blocking=False):
            raise MeihuaUnavailable()
        try:
            trusted = self._adapter.calculate(request)
            reading = ReadingResponse.model_validate(trusted.to_dict()["calculation"])
            return PreviewResponse(preview_api_version="traditional_preview_api_v1", reading=reading,
                                   judgement=self._engine.evaluate(trusted))
        except (JudgementUnavailable, ValueError, TypeError, KeyError):
            raise MeihuaUnavailable() from None
        finally:
            self._slots.release()
