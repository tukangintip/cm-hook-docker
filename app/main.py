import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .logging_config import (
    setup_logging,
    log_incoming_webhook,
    log_telegram_success,
    log_telegram_failure,
)
from .telegram import send_message, send_photo

setup_logging()
logger = logging.getLogger("webhook")

app = FastAPI(title="Webhook -> Telegram", version="1.0.0")

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
CAPTION_MAX = 1024
TEXT_MAX = 4096


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _is_image_url(url: str) -> bool:
    if not url:
        return False
    path = url.lower().split("?", 1)[0].split("#", 1)[0]
    return path.endswith(IMAGE_EXTENSIONS)


def _format_caption(payload: dict) -> str:
    direction = "Keluar" if payload.get("fromMe") else "Masuk"
    lines = ["\U0001F4E8 Pesan Baru"]
    sender = payload.get("from", "?")
    lid = payload.get("lid")
    lines.append(f"Dari  : {sender}" + (f" (lid: {lid})" if lid else ""))
    lines.append(f"Ke    : {payload.get('to', '?')}")
    lines.append(f"Arah  : {direction}")
    when = payload.get("datetimes") or payload.get("timestamp")
    if when:
        lines.append(f"Waktu : {when}")
    body = (payload.get("message") or "").strip()
    if body:
        lines.append("")
        lines.append(body)
    return "\n".join(lines)


@app.get("/")
async def root():
    return {"service": "webhook-chatmatter", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        logger.warning("IN  %s %s invalid_json", request.method, request.url.path)
        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "reason": "invalid_json"},
        )

    if not isinstance(payload, dict):
        logger.warning("IN  %s %s not_object", request.method, request.url.path)
        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "reason": "not_object"},
        )

    log_incoming_webhook(request, payload)

    text = (payload.get("message") or "").strip()
    file_url = (payload.get("file") or "").strip()

    if not text and not file_url:
        logger.info(
            "SKIP msgId=%s reason=empty_message_and_file",
            payload.get("messageId"),
        )
        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "reason": "empty_message_and_file"},
        )

    caption = _format_caption(payload)

    stage = "text"
    try:
        if file_url and _is_image_url(file_url):
            stage = "photo"
            result = await send_photo(file_url, _truncate(caption, CAPTION_MAX))
        elif file_url:
            note = f"\n\nLampiran: {file_url}"
            result = await send_message(_truncate(caption + note, TEXT_MAX))
            stage = "text"
        else:
            stage = "text"
            result = await send_message(_truncate(caption, TEXT_MAX))
    except Exception as exc:
        log_telegram_failure(payload, stage, f"exception: {exc!r}")
        logger.exception("Failed to call Telegram")
        return JSONResponse(
            status_code=200,
            content={"status": "error", "reason": "telegram_call_failed"},
        )

    if result.get("ok"):
        message_id = result.get("result", {}).get("message_id")
        log_telegram_success(payload, message_id)
        return {"status": "sent", "message_id": message_id}

    log_telegram_failure(payload, stage, result)
    return JSONResponse(
        status_code=200,
        content={"status": "telegram_error", "detail": result},
    )
