from __future__ import annotations
import os
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Coroutine, Optional, TypeVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# ---- Optional LangSmith import (safe if missing) ----
try:
    from langsmith import RunTree  # type: ignore
    _HAS_LS = True
except Exception:
    RunTree = None  # type: ignore
    _HAS_LS = False

# ---- Context vars ----
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_current_run: ContextVar[Optional["RunTree"]] = ContextVar("current_run", default=None)

# =====================================================
# RequestIdMiddleware  (restores what main.py imports)
# =====================================================
class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Ensures every request has an X-Request-ID.
    Stores it in a ContextVar for downstream logging/tracing.
    """
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_var.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_var.reset(token)

# ==========================
# LangSmith tracing helpers
# ==========================
def _new_run(name: str, run_type: str, inputs: dict | None = None, parent: "RunTree" | None = None) -> Optional["RunTree"]:
    if not _HAS_LS or not os.getenv("LANGSMITH_API_KEY"):
        return None
    project = os.getenv("LANGSMITH_PROJECT", "Tracktive AI")
    # attach request id if present
    req_id = request_id_var.get()
    payload = dict(inputs or {})
    if req_id and "request_id" not in payload:
        payload["request_id"] = req_id

    run = RunTree(  # type: ignore
        name=name,
        run_type=run_type,
        inputs=payload,
        project_name=project,
        **({"parent_run": parent} if parent else {}),
    )
    try:
        run.post()
    except Exception:
        return None
    return run

class RunContext:
    def __init__(self, name: str, inputs: dict | None = None):
        self.name = name
        self.inputs = inputs or {}
        self.run: Optional["RunTree"] = None
        self._token = None

    def __enter__(self):
        self.run = _new_run(self.name, "chain", self.inputs, parent=None)
        self._token = _current_run.set(self.run)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.run:
                if exc:
                    self.run.end(error=str(exc))
                else:
                    self.run.end(outputs={"ok": True})
        finally:
            if self._token:
                _current_run.reset(self._token)

def root_trace(name: str, inputs: dict | None = None) -> "RunContext":
    return RunContext(name=name, inputs=inputs)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

def traceable(func: F) -> F:
    """
    Decorate async functions to appear as child runs under the current root.
    No-op if LangSmith isn't configured.
    """
    async def wrapper(*args, **kwargs):
        parent = _current_run.get()
        child = _new_run(
            name=func.__name__,
            run_type="chain",
            inputs={"args": str(args), "kwargs": str(kwargs)},
            parent=parent,
        )
        try:
            result = await func(*args, **kwargs)
            if child:
                child.end(outputs={"status": "ok"})
            return result
        except Exception as e:
            if child:
                child.end(error=str(e))
            raise
    return wrapper  # type: ignore

# ---------- LangSmith status / self-test ----------
def langsmith_status(test: bool = False) -> dict:
    """Report config and optionally post a test run. Returns run_id if successful."""
    status = {
        "has_sdk": _HAS_LS,
        "api_key_present": bool(os.getenv("LANGSMITH_API_KEY")),
        "project": os.getenv("LANGSMITH_PROJECT", "Tracktive AI"),
        "endpoint": os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        "ok": False,
        "error": None,
        "run_id": None,
        "method": None,
    }
    if not _HAS_LS:
        status["error"] = "langsmith package not installed"
        return status
    if not status["api_key_present"]:
        status["error"] = "LANGSMITH_API_KEY not set"
        return status

    if not test:
        status["ok"] = True
        return status

    # Try RunTree first
    try:
        run = RunTree(  # type: ignore
            name="ls_self_test",
            run_type="chain",
            inputs={"ping": "pong"},
            project_name=status["project"],
        )
        run.post()
        run.end(outputs={"ok": True})
        status["ok"] = True
        status["method"] = "RunTree"
        try:
            status["run_id"] = run.id  # may be None on older versions
        except Exception:
            pass
        return status
    except Exception as e:
        status["error"] = f"RunTree failed: {e}"

    # Fallback: use Client directly
    try:
        from langsmith import Client  # type: ignore
        client = Client(
            api_key=os.getenv("LANGSMITH_API_KEY"),
            api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        )
        created = client.create_run(
            name="ls_self_test_client",
            run_type="chain",
            inputs={"ping": "pong"},
            project_name=status["project"],
        )
        client.update_run(run_id=created.id, outputs={"ok": True})
        status["ok"] = True
        status["method"] = "Client"
        status["run_id"] = str(created.id)
        status["error"] = None
        return status
    except Exception as e:
        status["error"] = f"Client failed: {e}"
        return status
