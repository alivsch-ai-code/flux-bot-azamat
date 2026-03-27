from types import SimpleNamespace
from unittest.mock import MagicMock

from src.presentation.telegram.handlers.gen import result_delivery


def _model(model_types):
    return SimpleNamespace(type=model_types)


def _text(key: str, _lang: str) -> str:
    if key == "success_caption":
        return "ok {cost}"
    if key == "media_send_failed":
        return "failed"
    if key == "media_link_too_long":
        return "long"
    return key


def test_parse_and_deliver_treats_image_generation_as_media(monkeypatch):
    bot = MagicMock()
    monkeypatch.setattr(result_delivery, "get_text", _text)
    monkeypatch.setattr(result_delivery, "set_context", lambda *_args, **_kwargs: None)

    result_delivery.parse_and_deliver(
        bot=bot,
        user_id=1,
        result="https://replicate.delivery/pbxt/some-image",
        model=_model(["image_generation"]),
        cost=2,
        lang="de",
        ctx={},
        is_chat=False,
        prompt="p",
        keyboards_fn=MagicMock(),
    )

    assert bot.send_photo.call_count == 1
    assert bot.send_message.call_count == 0


def test_parse_and_deliver_treats_video_generation_as_media(monkeypatch):
    bot = MagicMock()
    monkeypatch.setattr(result_delivery, "get_text", _text)
    monkeypatch.setattr(result_delivery, "set_context", lambda *_args, **_kwargs: None)

    result_delivery.parse_and_deliver(
        bot=bot,
        user_id=1,
        result="https://replicate.delivery/pbxt/some-video",
        model=_model(["video_generation"]),
        cost=2,
        lang="de",
        ctx={},
        is_chat=False,
        prompt="p",
        keyboards_fn=MagicMock(),
    )

    assert bot.send_video.call_count == 1
    assert bot.send_message.call_count == 0

