"""Tests für src.presentation.telegram.handlers.gen.media_helpers."""
from unittest.mock import MagicMock

from src.presentation.telegram.handlers.gen.media_helpers import (
    model_requires_image_for_video,
    schema_requires_media,
)


class TestModelRequiresImageForVideo:
    """Kling v1.6 Pro und andere Image-to-Video-only Modelle."""

    def test_kling_v1_6_pro_by_replicate_id(self):
        model = MagicMock(replicate_id="kwaivgi/kling-v1.6-pro", key="kwaivgi-kling-v1-6-pro")
        assert model_requires_image_for_video(model) is True

    def test_kling_v1_6_pro_by_key(self):
        model = MagicMock(replicate_id="other/model", key="kling-v1.6-pro")
        assert model_requires_image_for_video(model) is True

    def test_other_video_model_false(self):
        model = MagicMock(replicate_id="tencent/hunyuan-video", key="hunyuan-video")
        assert model_requires_image_for_video(model) is False

    def test_none_model_false(self):
        assert model_requires_image_for_video(None) is False


class TestSchemaRequiresMediaWithModel:
    """schema_requires_media mit model-Parameter für Image-to-Video-only."""

    def test_kling_model_requires_media_even_without_required_in_schema(self):
        model = MagicMock(replicate_id="kwaivgi/kling-v1.6-pro", key="kling")
        schema = {"properties": {"prompt": {}}, "required": []}
        assert schema_requires_media(schema, model=model) is True

    def test_normal_model_without_required_media(self):
        model = MagicMock(replicate_id="black-forest-labs/flux-schnell", key="flux")
        schema = {"properties": {"prompt": {}}, "required": []}
        assert schema_requires_media(schema, model=model) is False

    def test_model_with_required_image_in_schema(self):
        model = MagicMock(replicate_id="x/upscale", key="upscale")
        schema = {"properties": {"image": {}}, "required": ["image"]}
        assert schema_requires_media(schema, model=model) is True
