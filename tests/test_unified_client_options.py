"""Tests für UnifiedAIClient: generation_params werden in Replicate-Input übernommen."""

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
