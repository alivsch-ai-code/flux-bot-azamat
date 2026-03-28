"""
Replicate Prediction-Webhooks (async Modus, z. B. Video).

Validierung: https://replicate.com/docs/topics/webhooks/receive-webhook
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from flask import Request, jsonify
from replicate.webhook import WebhookSigningSecret, Webhooks, WebhookValidationError

from src.config.settings import config
from src.presentation.telegram import keyboards
from src.presentation.telegram.handlers.common import get_context
from src.presentation.telegram.handlers.gen import parse_and_deliver
from src.presentation.telegram.handlers.gen.runner import post_generation_followup_after_success
from src.utils.strings import get_text

if TYPE_CHECKING:
    from src.presentation.http.http_routes import AppRuntime

logger = logging.getLogger(__name__)


def handle_replicate_webhook_request(runtime: "AppRuntime", request: Request):
    """
    POST-Body: Prediction-Objekt (JSON). Nur ``completed``-Events (s. webhook_events_filter).
    """
    if not config.REPLICATE_WEBHOOK_SIGNING_SECRET:
        logger.warning("replicate_webhook: REPLICATE_WEBHOOK_SIGNING_SECRET fehlt")
        return jsonify(ok=False, error="not_configured"), 503

    body_raw = request.get_data(as_text=True)
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        Webhooks.validate(
            headers=headers,
            body=body_raw,
            secret=WebhookSigningSecret(key=config.REPLICATE_WEBHOOK_SIGNING_SECRET),
            tolerance=300,
        )
    except WebhookValidationError as e:
        logger.warning("replicate_webhook: Signatur ungültig: %s", e)
        return jsonify(ok=False, error="invalid_signature"), 403

    try:
        body: dict[str, Any] = json.loads(body_raw) if body_raw else {}
    except json.JSONDecodeError:
        return jsonify(ok=False, error="bad_json"), 400

    pred_id = body.get("id")
    if not pred_id:
        return jsonify(ok=False, error="missing_id"), 400

    db = runtime.db
    facade = runtime.bot
    gs = runtime.generation_service
    if db is None or facade is None or gs is None:
        logger.error("replicate_webhook: runtime unvollständig")
        return jsonify(ok=False, error="server_unready"), 503

    job = db.fetch_replicate_webhook_job(str(pred_id))
    if not job:
        logger.info("replicate_webhook: unbekannte prediction_id=%s (evtl. Duplikat oder Cleanup)", pred_id)
        return jsonify(ok=True), 200

    status = (body.get("status") or "").lower()
    if status in ("starting", "processing"):
        return jsonify(ok=True), 200

    model = db.get_model_by_key(job["model_key"])
    lang = job["lang"] or "en"
    user_id = int(job["user_id"])
    ctx = get_context(user_id)

    if status in ("failed", "canceled", "cancelled"):
        err = body.get("error") or body.get("logs") or get_text("gen_webhook_failed", lang)
        try:
            facade.send_message_sync(user_id, str(err)[:3500], parse_mode="HTML")
        except Exception as e:
            logger.warning("replicate_webhook: Fehler-Nachricht senden fehlgeschlagen: %s", e)
        db.delete_replicate_webhook_job(str(pred_id))
        return jsonify(ok=True), 200

    if status not in ("succeeded", "successful"):
        return jsonify(ok=True), 200

    unified = gs.ai_unified_client
    raw_out = body.get("output")
    gen_res = unified.normalize_replicate_output(raw_out)
    if not gen_res.success:
        try:
            facade.send_message_sync(
                user_id,
                get_text("gen_service_error_prefix", lang) + str(gen_res.error or ""),
                parse_mode="HTML",
            )
        except Exception:
            pass
        db.delete_replicate_webhook_job(str(pred_id))
        return jsonify(ok=True), 200

    cost = int(job["effective_cost"])
    if not job["no_charge"]:
        gid = job.get("group_chat_id")
        if gid is not None:
            if not db.deduct_credits_for_group(user_id, gid, cost, reason=f"gen_{model.key if model else job['model_key']}"):
                try:
                    facade.send_message_sync(user_id, get_text("gen_service_insufficient_balance", lang))
                except Exception:
                    pass
                db.delete_replicate_webhook_job(str(pred_id))
                return jsonify(ok=True), 200
        else:
            if int(db.get_user_credits(user_id)) < cost:
                try:
                    facade.send_message_sync(user_id, get_text("gen_service_insufficient_balance", lang))
                except Exception:
                    pass
                db.delete_replicate_webhook_job(str(pred_id))
                return jsonify(ok=True), 200
            db.update_credits(user_id, -cost, reason=f"gen_{model.key if model else job['model_key']}")

    if not model:
        db.delete_replicate_webhook_job(str(pred_id))
        return jsonify(ok=True), 200

    result_data = gen_res.data
    prompt_saved = job.get("user_prompt") or ""

    async def _deliver():
        await parse_and_deliver(
            facade,
            user_id,
            result_data,
            model,
            cost,
            lang,
            ctx,
            bool(job.get("is_chat")),
            prompt_saved,
            keyboards,
        )
        await post_generation_followup_after_success(
            facade,
            db,
            user_id,
            model,
            result_data,
            cost,
            lang,
            ctx,
            bool(job.get("is_chat")),
            prompt_saved,
            job["model_key"],
            job.get("chat_history_mode"),
        )

    try:
        facade._sync(_deliver(), timeout=300)
    except Exception as e:
        logger.exception("replicate_webhook: Auslieferung fehlgeschlagen: %s", e)

    db.delete_replicate_webhook_job(str(pred_id))
    return jsonify(ok=True), 200
