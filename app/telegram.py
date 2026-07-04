import logging

import httpx

from .config import settings

logger = logging.getLogger("telegram")

TIMEOUT = 15.0


def _endpoint(method: str) -> str:
    return f"{settings.telegram_api_base}/bot{settings.telegram_bot_token}/{method}"


async def send_message(text: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            _endpoint("sendMessage"),
            data={"chat_id": settings.telegram_chat_id, "text": text},
        )
        return _parse(resp)


async def send_photo(photo_url: str, caption: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            _endpoint("sendPhoto"),
            data={
                "chat_id": settings.telegram_chat_id,
                "photo": photo_url,
                "caption": caption,
            },
        )
        return _parse(resp)


def _parse(resp: httpx.Response) -> dict:
    try:
        data = resp.json()
    except Exception:
        data = {
            "ok": False,
            "error_code": resp.status_code,
            "description": resp.text,
        }
    if resp.status_code != 200 or not data.get("ok"):
        logger.error(
            "Telegram API failure status=%s body=%s", resp.status_code, data
        )
    return data
