import pytest


@pytest.fixture(autouse=True)
def _no_api_key(monkeypatch):
    """AC-9: no test may reach a paid API, even when run with `--env-file .env`."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
