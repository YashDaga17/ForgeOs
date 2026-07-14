from app.config import Settings


def test_demo_ai_fallback_is_disabled_without_explicit_opt_in(monkeypatch) -> None:
    monkeypatch.delenv("FORGEOS_ALLOW_DEMO_AI_FALLBACK", raising=False)

    assert Settings().allow_demo_ai_fallback is False


def test_demo_ai_fallback_requires_explicit_opt_in(monkeypatch) -> None:
    monkeypatch.setenv("FORGEOS_ALLOW_DEMO_AI_FALLBACK", "true")

    assert Settings().allow_demo_ai_fallback is True
