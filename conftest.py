"""Pytest configuration.

Ensures the project root is importable and isolates each test from ambient
environment (e.g. a placeholder ``OPENAI_API_KEY``) by pinning the LLM provider
to the offline ``mock`` adapter, reloading settings, and resetting the registry
before every test. Adapter tests override the provider via ``monkeypatch`` as
needed; the autouse fixture restores isolation afterwards.
"""

import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Quiet, compact logs during tests.
os.environ.setdefault("PEPA_LOG_LEVEL", "WARNING")


@pytest.fixture(autouse=True)
def _pepa_isolate(monkeypatch):
    """Pin provider=mock, reload settings, and reset the registry per test."""
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "mock")
    from config import reload_settings
    from policy_advisor import reset_registry

    reload_settings()
    reset_registry()
    yield
    reset_registry()
