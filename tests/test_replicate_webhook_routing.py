"""Tests: Replicate HTTP vs. Webhook-Routing (Modelltypen) und GenerationService-Pfad."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from src.application.services import GenerationService
from src.domain.entities import AIModel, GenerationResult
from src.infrastructure.ai.unified_client import (
    is_replicate_webhook_pending_result,
    make_replicate_webhook_pending_result,
    replicate_model_types_allow_http,
    replicate_should_use_webhook,
    replicate_webhook_delivery_configured,
)


def test_replicate_model_types_allow_http_text_and_image():
    assert replicate_model_types_allow_http(AIModel(key="t", replicate_id="a/b", name="", description="", type=["text"])) is True
    assert replicate_model_types_allow_http(AIModel(key="i", replicate_id="a/b", name="", description="", type=["image"])) is True
    assert replicate_model_types_allow_http(AIModel(key="ti", replicate_id="a/b", name="", description="", type=["text", "image"])) is True


def test_replicate_should_use_webhook_for_video():
    m = AIModel(
        key="veo",
        replicate_id="google/veo",
        name="Veo",
        description="",
        provider="replicate",
        type=["video"],
    )
    assert replicate_model_types_allow_http(m) is False
    assert replicate_should_use_webhook(m) is True


def test_replicate_should_not_use_webhook_non_replicate_provider():
    m = AIModel(
        key="gpt",
        replicate_id="gpt-4o",
        name="GPT",
        description="",
        provider="openai",
        type=["video"],
    )
    assert replicate_should_use_webhook(m) is False


def test_replicate_webhook_delivery_configured():
    class C:
        APP_URL = "https://app.example"
        REPLICATE_WEBHOOK_SIGNING_SECRET = "whsec_abc"

    class C2:
        APP_URL = "http://insecure.app"
        REPLICATE_WEBHOOK_SIGNING_SECRET = "whsec_x"

    class C3:
        APP_URL = "https://ok.app"
        REPLICATE_WEBHOOK_SIGNING_SECRET = ""

    assert replicate_webhook_delivery_configured(C()) is True
    assert replicate_webhook_delivery_configured(C2()) is False
    assert replicate_webhook_delivery_configured(C3()) is False


def test_webhook_pending_helpers():
    d = make_replicate_webhook_pending_result("pid-1")
    assert is_replicate_webhook_pending_result(d) is True
    assert d["prediction_id"] == "pid-1"
    assert is_replicate_webhook_pending_result("x") is False


@contextmanager
def _noop_slot():
    yield


def test_process_request_webhook_inserts_job_no_immediate_charge():
    """Video + vollständige Webhook-Konfiguration: Job anlegen, kein sofortiges update_credits."""
    db_manager = MagicMock()
    db_manager.get_user_credits.return_value = 500

    class WebhookCfg:
        REPLICATE_API_TOKEN = "tok"
        OPENAI_API_KEY = ""
        GROK_API_KEY = ""
        APP_URL = "https://bot.example"
        REPLICATE_WEBHOOK_SIGNING_SECRET = "whsec_testsecret"

    ai = MagicMock()
    ai.config = WebhookCfg()
    ai.build_replicate_input_dict.return_value = {"prompt": "clip"}
    ai.create_replicate_prediction_with_webhook.return_value = "pred-abc123"

    model = AIModel(
        key="veo-test",
        replicate_id="google/veo-3.1",
        name="Veo",
        description="",
        internal_cost=50,
        custom_price=None,
        provider="replicate",
        type=["video"],
    )

    svc = GenerationService(db_manager=db_manager, ai_unified_client=ai)
    with patch("src.application.services.replicate_run_slot", _noop_slot):
        success, result = svc.process_request(99, model, "sunset", media_files=None, lang="de")

    assert success is True
    assert is_replicate_webhook_pending_result(result)
    assert result["prediction_id"] == "pred-abc123"
    ai.build_replicate_input_dict.assert_called_once()
    ai.create_replicate_prediction_with_webhook.assert_called_once()
    ai.generate.assert_not_called()
    db_manager.update_credits.assert_not_called()
    db_manager.insert_replicate_webhook_job.assert_called_once()
    pos, kw = db_manager.insert_replicate_webhook_job.call_args
    assert pos[0] == "pred-abc123"
    assert pos[1] == 99
    assert pos[2] == "veo-test"


def test_process_request_prefer_sync_skips_webhook():
    """Interne Aufrufer (z. B. Daily-News-Bild) brauchen synchrone replicate.run-Ergebnisse."""
    db_manager = MagicMock()
    db_manager.get_user_credits.return_value = 500

    class WebhookCfg:
        REPLICATE_API_TOKEN = "tok"
        OPENAI_API_KEY = ""
        GROK_API_KEY = ""
        APP_URL = "https://bot.example"
        REPLICATE_WEBHOOK_SIGNING_SECRET = "whsec_testsecret"

    ai = MagicMock()
    ai.config = WebhookCfg()
    ai.generate.return_value = GenerationResult(success=True, data="https://cdn.example/img.png")

    model = AIModel(
        key="nano-banana",
        replicate_id="google/nano-banana",
        name="Nano",
        description="",
        internal_cost=1,
        custom_price=None,
        provider="replicate",
        type=["image_generation"],
    )

    svc = GenerationService(db_manager=db_manager, ai_unified_client=ai)
    with patch("src.application.services.replicate_run_slot", _noop_slot):
        success, result = svc.process_request(
            99, model, "a banana", media_files=None, lang="de", no_charge=True, prefer_sync_replicate=True
        )

    assert success is True
    assert result == "https://cdn.example/img.png"
    ai.generate.assert_called_once()
    ai.create_replicate_prediction_with_webhook.assert_not_called()
    db_manager.insert_replicate_webhook_job.assert_not_called()


def test_process_request_video_fallback_sync_without_webhook_config():
    """Ohne HTTPS-APP_URL / Secret: Fallback auf synchrones generate()."""
    db_manager = MagicMock()
    db_manager.get_user_credits.return_value = 500

    class BareCfg:
        REPLICATE_API_TOKEN = "tok"
        OPENAI_API_KEY = ""
        GROK_API_KEY = ""
        APP_URL = ""
        REPLICATE_WEBHOOK_SIGNING_SECRET = ""

    ai = MagicMock()
    ai.config = BareCfg()
    ai.generate.return_value = GenerationResult(success=True, data="https://cdn.example/out.mp4")

    model = AIModel(
        key="veo-test",
        replicate_id="google/veo-3.1",
        name="Veo",
        description="",
        internal_cost=10,
        custom_price=None,
        provider="replicate",
        type=["video"],
    )

    svc = GenerationService(db_manager=db_manager, ai_unified_client=ai)
    with patch("src.application.services.replicate_run_slot", _noop_slot):
        success, result = svc.process_request(7, model, "waves", media_files=None, lang="en")

    assert success is True
    assert result == "https://cdn.example/out.mp4"
    ai.generate.assert_called_once()
    db_manager.insert_replicate_webhook_job.assert_not_called()
    db_manager.update_credits.assert_called_once_with(7, -10, reason="gen_veo-test")


class TestReplicateWebhookRoute:
    def test_webhook_returns_503_without_signing_secret(self, monkeypatch):
        import main as main_module

        monkeypatch.setattr(main_module.config, "REPLICATE_WEBHOOK_SIGNING_SECRET", "")
        client = main_module.app.test_client()
        client.application.config["TESTING"] = True
        r = client.post("/api/replicate_webhook", json={"id": "x", "status": "succeeded"})
        assert r.status_code == 503
        data = r.get_json()
        assert data.get("error") == "not_configured"
