"""Tests: GenerationService muss bei erfolgreicher Generierung Transaktion (update_credits) auslösen."""
from unittest.mock import MagicMock

from src.application.services import GenerationService
from src.domain.entities import AIModel, GenerationResult


def test_process_request_calls_update_credits_on_success():
    """Bei erfolgreicher Generierung muss update_credits mit negativem Betrag aufgerufen werden."""
    repo = MagicMock()
    repo.get_user_credits.return_value = 100
    ai = MagicMock()
    ai.generate.return_value = GenerationResult(success=True, data="https://example.com/image.png")

    model = AIModel(
        key="flux-test",
        replicate_id="x/y",
        name="Test",
        description="",
        internal_cost=15,
        custom_price=None,
    )

    svc = GenerationService(repo=repo, ai=ai)
    success, result = svc.process_request(user_id=12345, model=model, prompt="a cat", media_files=None)

    assert success is True
    assert result == "https://example.com/image.png"
    repo.update_credits.assert_called_once_with(12345, -15, reason="gen_flux-test")


def test_process_request_no_charge_when_no_charge_flag():
    """Bei no_charge=True darf update_credits nicht aufgerufen werden."""
    repo = MagicMock()
    repo.get_user_credits.return_value = 100
    ai = MagicMock()
    ai.generate.return_value = GenerationResult(success=True, data="https://example.com/image.png")

    model = AIModel(
        key="flux-test",
        replicate_id="x/y",
        name="Test",
        description="",
        internal_cost=15,
        custom_price=None,
    )

    svc = GenerationService(repo=repo, ai=ai)
    success, _ = svc.process_request(
        user_id=12345, model=model, prompt="a cat", media_files=None, no_charge=True
    )

    assert success is True
    repo.update_credits.assert_not_called()


def test_process_request_no_charge_on_failure():
    """Bei Fehlschlag (result.success=False) darf update_credits nicht aufgerufen werden."""
    repo = MagicMock()
    repo.get_user_credits.return_value = 100
    ai = MagicMock()
    ai.generate.return_value = GenerationResult(success=False, error="API error")

    model = AIModel(
        key="flux-test",
        replicate_id="x/y",
        name="Test",
        description="",
        internal_cost=15,
        custom_price=None,
    )

    svc = GenerationService(repo=repo, ai=ai)
    success, result = svc.process_request(user_id=12345, model=model, prompt="a cat", media_files=None)

    assert success is False
    assert "API error" in result
    repo.update_credits.assert_not_called()
