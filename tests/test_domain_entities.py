"""Tests für src.domain.entities."""
from src.domain.entities import (
    AIModel,
    MediaFile,
    MediaType,
    User,
    GenerationResult,
)


class TestAIModel:
    def test_final_cost_uses_internal_when_no_custom(self):
        model = AIModel(
            key="test", replicate_id="x/y", name="Test", description="",
            internal_cost=15, custom_price=None
        )
        assert model.final_cost == 15

    def test_final_cost_uses_custom_when_set(self):
        model = AIModel(
            key="test", replicate_id="x/y", name="Test", description="",
            internal_cost=10, custom_price=25
        )
        assert model.final_cost == 25

    def test_cost_alias_matches_final_cost(self):
        model = AIModel(
            key="test", replicate_id="x/y", name="Test", description="",
            internal_cost=20, custom_price=30
        )
        assert model.cost == model.final_cost == 30


class TestMediaType:
    def test_enum_values(self):
        assert MediaType.IMAGE.value == "image"
        assert MediaType.VIDEO.value == "video"
        assert MediaType.AUDIO.value == "audio"
        assert MediaType.DOCUMENT.value == "document"


class TestMediaFile:
    def test_extension_from_path(self):
        m = MediaFile(path="/tmp/image.jpg", media_type=MediaType.IMAGE)
        assert m.extension == ".jpg"

    def test_extension_uppercase(self):
        m = MediaFile(path="/tmp/photo.PNG", media_type=MediaType.IMAGE)
        assert m.extension == ".png"

    def test_extension_no_extension_returns_empty(self):
        m = MediaFile(path="/tmp/noext", media_type=MediaType.IMAGE)
        assert m.extension == ""


class TestUser:
    def test_default_credits(self):
        u = User(id=1, username="test")
        assert u.credits == 50


class TestGenerationResult:
    def test_success_result(self):
        r = GenerationResult(success=True, data="https://example.com/image.png")
        assert r.success is True
        assert r.data == "https://example.com/image.png"
        assert r.error is None

    def test_error_result(self):
        r = GenerationResult(success=False, error="API timeout")
        assert r.success is False
        assert r.error == "API timeout"
