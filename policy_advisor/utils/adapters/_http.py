"""A small, stdlib-only HTTP helper shared by the provider adapters.

Centralises JSON POST, timeout, and error translation so each adapter stays
focused on its provider's request/response shape. Network/HTTP errors are
raised as :class:`~policy_advisor.utils.errors.LLMInvocationError` so the
:class:`RetryingLLMAdapter` can retry and ultimately fall back gracefully.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict

from ..errors import LLMInvocationError

_DEFAULT_TIMEOUT = 60.0


def http_post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    timeout: float = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """POST ``payload`` as JSON to ``url`` and return the parsed JSON response.

    Raises :class:`LLMInvocationError` on any transport, HTTP, or parsing error.
    """
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={**{"Content-Type": "application/json", "Accept": "application/json"}, **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            status = getattr(resp, "status", 200)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:  # noqa: BLE001
            pass
        raise LLMInvocationError(
            f"HTTP {exc.code} from {url}: {detail or exc.reason}",
            recoverable=exc.code in {408, 409, 429, 500, 502, 503, 504},
        ) from exc
    except urllib.error.URLError as exc:
        raise LLMInvocationError(f"network error calling {url}: {exc.reason}", recoverable=True) from exc
    except TimeoutError as exc:
        raise LLMInvocationError(f"timeout calling {url}: {exc}", recoverable=True) from exc

    if status >= 400:
        raise LLMInvocationError(f"HTTP {status} from {url}: {body[:500]}", recoverable=status >= 500)
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise LLMInvocationError(f"invalid JSON response from {url}: {exc}", recoverable=False) from exc
