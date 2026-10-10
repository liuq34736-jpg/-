"""Request-scoped cancellation of the SAME fixed, read-only frozen worker.

No retry or abandoned subprocess. Only the child started here is terminated.
The original offline/batch adapter and its 180s allowance are unchanged.
"""

import asyncio
import anyio
from contextvars import ContextVar
import json
import os
import subprocess
import sys
from threading import Event
from time import monotonic

from backend.app.meihua_models import ManualInput, TimeInput
from backend.traditional_judgement_v1.trusted_input import (
    ROOT, OfflineJudgementAdapter, JudgementUnavailable, _issue, canonical,
)

WORKER_SECONDS = 20.0
REQUEST_SECONDS = 22.0
POLL_SECONDS = 0.05
CLEANUP_SECONDS = 2.0


class PreviewTimedOut(JudgementUnavailable):
    pass


class PreviewCancelled(JudgementUnavailable):
    pass


class ExecutionControl:
    def __init__(self, seconds=WORKER_SECONDS):
        self.cancelled = Event()
        self.deadline = monotonic() + seconds
        self.reason = None

    def cancel(self, reason="cancelled"):
        self.reason = reason
        self.cancelled.set()

    def check(self):
        if self.cancelled.is_set():
            raise PreviewTimedOut() if self.reason == "timeout" else PreviewCancelled()
        if monotonic() >= self.deadline:
            self.cancel("timeout")
            raise PreviewTimedOut()


EXECUTION = ContextVar("preview_execution", default=None)


class PreviewDisconnectMiddleware:
    """Observe disconnect BEFORE BaseHTTPMiddleware's competing receive loop."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/v1/meihua/traditional-preview":
            return await self.app(scope, receive, send)
        signal = Event()
        scope.setdefault("state", {})["preview_cancel_event"] = signal
        async def monitored_receive():
            message = await receive()
            if message["type"] == "http.disconnect":
                signal.set()
            return message
        await self.app(scope, monitored_receive, send)


class CancellableOfflineAdapter(OfflineJudgementAdapter):
    def calculate(self, request):
        if type(request) not in {ManualInput, TimeInput}:
            raise JudgementUnavailable()
        control = EXECUTION.get() or ExecutionControl()
        control.check()
        data = [request.model_dump(exclude={"question_text"})]
        environment = {k: v for k, v in os.environ.items()
                       if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        child = None
        try:
            child = subprocess.Popen(
                [sys.executable, "-I", "-B", "-X", "utf8", str(ROOT / "backend/traditional_judgement_v1/worker.py")],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=ROOT, env=environment, **options,
            )
            incoming = canonical(data).encode("utf-8")
            while True:
                control.check()
                try:
                    stdout, _ = child.communicate(input=incoming, timeout=POLL_SECONDS)
                    break
                except subprocess.TimeoutExpired:
                    incoming = None  # communicate resumes; never resend input/start another child.
            control.check()
            if child.returncode or len(stdout) > 32_000_000:
                raise JudgementUnavailable()
            results = json.loads(stdout)
            if type(results) is not list or len(results) != 1:
                raise JudgementUnavailable()
            result = results[0]
            result["calculation"]["question_text"] = request.question_text
            result["calculation"]["question_applied_to_calculation"] = False
            return _issue(result)  # SAME seal + schema; worker performed original signature/source checks.
        except (PreviewTimedOut, PreviewCancelled):
            raise
        except (ValueError, TypeError, KeyError, OSError):
            raise JudgementUnavailable() from None
        finally:
            if child is not None:
                try:
                    if child.poll() is None:
                        child.kill()
                    child.communicate(timeout=CLEANUP_SECONDS)
                finally:
                    # A slot may only be released AFTER this owned child has exited.
                    if child.poll() is None:
                        child.kill()
                    child.wait()
                    for pipe in (child.stdin, child.stdout, child.stderr):
                        if pipe is not None:
                            pipe.close()


async def run_cancellable_preview(service, casting, http_request):
    control = ExecutionControl()
    state = getattr(http_request, "state", None)
    signal = getattr(state, "preview_cancel_event", None)
    if signal is not None:
        control.cancelled = signal
    token = EXECUTION.set(control)
    task = asyncio.create_task(asyncio.to_thread(service.calculate, casting))
    deadline = monotonic() + REQUEST_SECONDS
    try:
        while True:
            done, _ = await asyncio.wait({task}, timeout=POLL_SECONDS)
            if done:
                return task.result()
            if monotonic() >= deadline:
                control.cancel("timeout")
                # Shield/join, not abandon: service releases its slot in finally.
                try:
                    await asyncio.shield(task)
                except Exception:
                    pass
                raise PreviewTimedOut()
            if await http_request.is_disconnected():
                control.cancel("disconnect")
                try:
                    await asyncio.shield(task)
                except Exception:
                    pass
                raise PreviewCancelled()
    except asyncio.CancelledError:
        control.cancel("disconnect")
        try:
            # Starlette/AnyIO may cancel the entire request scope repeatedly.
            # Shield that scope too, and keep joining the owned worker.
            with anyio.CancelScope(shield=True):
                await asyncio.shield(task)
        except Exception:
            pass
        raise
    finally:
        EXECUTION.reset(token)
