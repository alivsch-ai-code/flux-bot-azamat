import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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


def _facade():
    f = MagicMock()
    f.send_photo = AsyncMock()
    f.send_video = AsyncMock()
    f.send_message = AsyncMock()
    return f


def test_parse_and_deliver_treats_image_generation_as_media(monkeypatch):
    facade = _facade()
    monkeypatch.setattr(result_delivery, "get_text", _text)
    monkeypatch.setattr(result_delivery, "set_context", lambda *_args, **_kwargs: None)

    asyncio.run(
        result_delivery.parse_and_deliver(
            facade=facade,
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
    )

    assert facade.send_photo.await_count == 1
    assert facade.send_message.await_count == 0


def test_parse_and_deliver_treats_video_generation_as_media(monkeypatch):
    facade = _facade()
    monkeypatch.setattr(result_delivery, "get_text", _text)
    monkeypatch.setattr(result_delivery, "set_context", lambda *_args, **_kwargs: None)

    asyncio.run(
        result_delivery.parse_and_deliver(
            facade=facade,
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
    )

    assert facade.send_video.await_count == 1
    assert facade.send_message.await_count == 0


def test_parse_and_deliver_infers_media_from_replicate_url_when_type_missing(monkeypatch):
    facade = _facade()
    monkeypatch.setattr(result_delivery, "get_text", _text)
    monkeypatch.setattr(result_delivery, "set_context", lambda *_args, **_kwargs: None)

    asyncio.run(
        result_delivery.parse_and_deliver(
            facade=facade,
            user_id=1,
            result="https://replicate.delivery/xezq/abc123/tmpn9c8g6km.jpeg",
            model=_model([]),
            cost=2,
            lang="de",
            ctx={},
            is_chat=False,
            prompt="p",
            keyboards_fn=MagicMock(),
        )
    )

    assert facade.send_photo.await_count == 1
    assert facade.send_message.await_count == 0
