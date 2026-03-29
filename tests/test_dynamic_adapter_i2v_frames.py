"""Zwei URI-Bildfelder (image + last_frame_image) nach x-order."""

from src.infrastructure.ai.dynamic_adapter import DynamicSchemaAdapter


def test_image_and_last_frame_image_mapped_by_x_order():
    schema = {
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"type": "string", "x-order": 0},
            "image": {"type": "string", "format": "uri", "nullable": True, "x-order": 1},
            "last_frame_image": {"type": "string", "format": "uri", "nullable": True, "x-order": 2},
        },
    }
    ad = DynamicSchemaAdapter()
    out = ad.build_input_payload(
        schema,
        "motion",
        ["https://example.com/start.jpg", "https://example.com/end.jpg"],
    )
    assert out["prompt"] == "motion"
    assert out["image"] == "https://example.com/start.jpg"
    assert out["last_frame_image"] == "https://example.com/end.jpg"
