"""Tests für UnifiedAIClient: generation_params werden in Replicate-Input übernommen."""

import time
from unittest.mock import patch

from src.domain.entities import AIModel
from src.infrastructure.ai.unified_client import UnifiedAIClient


class DummyConfig:
    REPLICATE_API_TOKEN = "test-token"
    OPENAI_API_KEY = ""
    GROK_API_KEY = ""


def test_run_replicate_includes_generation_params():
    model = AIModel(
        key="google-veo-3-1",
        replicate_id="google/veo-3.1",
        name="Veo 3.1",
        description="",
        internal_cost=200,
        custom_price=None,
        provider="replicate",
        input_schema={"properties": {"prompt": {"type": "string"}}},
    )
    client = UnifiedAIClient(DummyConfig())

    with patch("src.infrastructure.ai.unified_client.replicate.run", return_value="https://example.com/video.mp4") as run_mock:
        res = client.generate(
            model,
            prompt="hello veo",
            media_files=None,
            generation_params={
                "duration": 8,
                "resolution": "1080p",
                "aspect_ratio": "16:9",
                "generate_audio": True,
                "reference_images": ["https://example.com/ref1.png"],
            },
        )

    assert res.success is True
    assert "video.mp4" in str(res.data)
    run_mock.assert_called_once()
    args, kwargs = run_mock.call_args
    assert args[0] == "google/veo-3.1"
    sent_input = kwargs["input"]
    assert sent_input["prompt"] == "hello veo"
    assert sent_input["duration"] == 8
    assert sent_input["resolution"] == "1080p"
    assert sent_input["aspect_ratio"] == "16:9"
    assert sent_input["generate_audio"] is True
    assert sent_input["reference_images"] == ["https://example.com/ref1.png"]
    assert run_mock.call_args.kwargs.get("wait") == 60
    assert run_mock.call_args.kwargs.get("use_file_output") is True


def test_run_replicate_includes_generic_schema_params():
    model = AIModel(
        key="generic-video-model",
        replicate_id="owner/model",
        name="Generic",
        description="",
        internal_cost=50,
        custom_price=None,
        provider="replicate",
        input_schema={"properties": {"prompt": {"type": "string"}, "cfg_scale": {"type": "number"}}},
    )
    client = UnifiedAIClient(DummyConfig())

    with patch("src.infrastructure.ai.unified_client.replicate.run", return_value="ok") as run_mock:
        client.generate(
            model,
            prompt="x",
            media_files=None,
            generation_params={"cfg_scale": 0.8, "prompt": "should_not_override", "empty": ""},
        )

    _, kwargs = run_mock.call_args
    sent_input = kwargs["input"]
    assert sent_input["prompt"] == "x"
    assert sent_input["cfg_scale"] == 0.8
    assert "empty" not in sent_input
    assert run_mock.call_args.kwargs.get("wait") == 60
    assert run_mock.call_args.kwargs.get("use_file_output") is True


def test_run_replicate_caps_anthropic_max_tokens():
    model = AIModel(
        key="claude-test",
        replicate_id="anthropic/claude-4.5-sonnet",
        name="Claude",
        description="",
        internal_cost=10,
        custom_price=None,
        provider="replicate",
        input_schema={
            "properties": {
                "prompt": {"type": "string"},
                "max_tokens": {"type": "integer", "default": 8192},
            }
        },
    )
    client = UnifiedAIClient(DummyConfig())

    with patch("src.infrastructure.ai.unified_client.replicate.run", return_value="ok") as run_mock:
        client.generate(
            model,
            prompt="hi",
            media_files=None,
            generation_params={"max_tokens": 16000},
        )

    _, kwargs = run_mock.call_args
    assert kwargs["input"]["max_tokens"] == 4000
    assert kwargs.get("wait") == 60
    assert kwargs.get("use_file_output") is True


def test_run_replicate_caps_anthropic_max_tokens_from_schema_default():
    model = AIModel(
        key="claude-haiku",
        replicate_id="anthropic/claude-4.5-haiku",
        name="Haiku",
        description="",
        internal_cost=5,
        custom_price=None,
        provider="replicate",
        input_schema={
            "properties": {
                "prompt": {"type": "string"},
                "max_tokens": {"type": "integer", "default": 8192},
            }
        },
    )
    client = UnifiedAIClient(DummyConfig())

    with patch("src.infrastructure.ai.unified_client.replicate.run", return_value="ok") as run_mock:
        client.generate(model, prompt="x", media_files=None, generation_params={})

    _, kwargs = run_mock.call_args
    assert kwargs["input"]["max_tokens"] == 4000
    assert kwargs.get("wait") == 60
    assert kwargs.get("use_file_output") is True


def test_run_replicate_passes_wait_and_use_file_output_for_text_model(monkeypatch):
    monkeypatch.setenv("REPLICATE_PREFER_WAIT_SECONDS", "45")
    model = AIModel(
        key="gemini-flash",
        replicate_id="google/gemini-2.5-flash",
        name="Gemini",
        description="",
        internal_cost=1,
        custom_price=None,
        provider="replicate",
        type=["text"],
        input_schema={"properties": {"prompt": {"type": "string"}}},
    )
    client = UnifiedAIClient(DummyConfig())
    with patch("src.infrastructure.ai.unified_client.replicate.run", return_value="hello") as run_mock:
        res = client.generate(model, prompt="x", media_files=None, generation_params=None)
    assert res.success is True
    assert res.data == "hello"
    _, kwargs = run_mock.call_args
    assert kwargs["wait"] == 45
    assert kwargs["use_file_output"] is False


def test_normalize_replicate_iterator_collect_timeout(monkeypatch):
    monkeypatch.setenv("REPLICATE_OUTPUT_COLLECT_MAX_SEC", "1")
    client = UnifiedAIClient(DummyConfig())

    def slow_stream():
        while True:
            time.sleep(0.15)
            yield "a"

    res = client.normalize_replicate_output(slow_stream())
    assert res.success is False
    err = (res.error or "").lower()
    assert "timeout" in err or "collect_timeout" in err


def test_normalize_replicate_output_keeps_all_file_outputs():
    class _F:
        def __init__(self, url):
            self.url = url

    client = UnifiedAIClient(DummyConfig())
    out = client.normalize_replicate_output([_F("https://a"), _F("https://b")])
    assert out.success is True
    assert isinstance(out.data, list)
    assert len(out.data) == 2
    assert out.data[0].url == "https://a"
    assert out.data[1].url == "https://b"
