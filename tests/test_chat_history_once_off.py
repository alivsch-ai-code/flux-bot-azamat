import pytest
from unittest.mock import MagicMock


def test_once_off_writes_user_and_assistant_to_chat_history(monkeypatch):
    from src.presentation.telegram.handlers.gen import runner as runner_module

    bot = MagicMock()
    bot.send_chat_action = MagicMock()
    bot.delete_message = MagicMock()

    # UI/Side-Effects vermeiden
    monkeypatch.setattr(runner_module, "parse_and_deliver", lambda *args, **kwargs: None)
    monkeypatch.setattr(runner_module, "smart_update_status", lambda *args, **kwargs: 1)
    monkeypatch.setattr(runner_module, "get_context", lambda _uid: {})
    monkeypatch.setattr(runner_module, "get_random_tip", lambda _lang: "tip")

    def fake_get_text(key, _lang):
        # Runner nutzt .format(tip=...) für status_generating
        return "{tip}" if key == "status_generating" else "OK"

    monkeypatch.setattr(runner_module, "get_text", fake_get_text)

    db = MagicMock()
    model = MagicMock()
    model.type = ["text"]
    model.custom_price = None
    model.internal_cost = 1
    model.replicate_id = ""
    model.key = "m1"
    model.menu_path = "root"
    model.name = "Test model"
    model.is_active = True
    db.get_model_by_key.return_value = model
    db.get_user_credits.return_value = 10
    db.get_fallback_model.return_value = None

    # Chat sessions (simuliert persistente Historie)
    history = []

    def fake_get_chat_session(_uid, _model_key):
        return list(history)

    def fake_save_chat_session(_uid, _model_key, messages):
        nonlocal history
        history = list(messages)

    db.get_chat_session.side_effect = fake_get_chat_session
    db.save_chat_session = MagicMock(side_effect=fake_save_chat_session)
    db.get_user_username_or_name.return_value = "Alice"

    generation_service = MagicMock()
    generation_service.process_request.return_value = (True, "assistant answer")

    run_generation = runner_module.create_run_generation(bot, db, generation_service, lambda _uid: "de")

    run_generation(
        user_id=123,
        model_key="m1",
        prompt="Hello",
        media_files=None,
        is_chat=True,
        chat_history_mode="once_off",
        chat_user_name="Alice",
    )

    assert generation_service.process_request.call_count == 1

    # once_off speichert user+assistant jeweils via save_chat_session
    assert db.save_chat_session.call_count == 2

    first_messages = db.save_chat_session.call_args_list[0].args[2]
    assert any(m.get("role") == "user" and m.get("content") == "Hello" for m in first_messages)

    second_messages = db.save_chat_session.call_args_list[1].args[2]
    assert any(m.get("role") == "user" and m.get("content") == "Hello" for m in second_messages)
    assert any(m.get("role") == "assistant" and m.get("content") == "assistant answer" for m in second_messages)

    # Prompt, den wir ans LLM schicken, soll History enthalten
    sent_prompt = generation_service.process_request.call_args_list[0].args[2]
    assert "Alice:" in sent_prompt
    assert "Hello" in sent_prompt
    assert "Assistant:" in sent_prompt

