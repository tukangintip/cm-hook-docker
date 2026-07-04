import json
import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-6s | %(name)-8s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
VIDEO_EXTS = (
    ".mp4", ".mov", ".m4v", ".webm", ".mkv",
    ".avi", ".3gp", ".wmv", ".flv", ".ts",
)
AUDIO_EXTS = (
    ".mp3", ".m4a", ".aac", ".ogg", ".oga",
    ".opus", ".wav", ".flac", ".wma",
)


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]


def _client_ip(request) -> str:
    client = getattr(request, "client", None)
    return getattr(client, "host", "unknown") if client else "unknown"


def _normalize(url: str) -> str:
    return url.lower().split("?", 1)[0].split("#", 1)[0]


def detect_media_type(url: str) -> str:
    if not url:
        return "none"
    path = _normalize(url)
    if path.endswith(IMAGE_EXTS):
        return "image"
    if path.endswith(VIDEO_EXTS):
        return "video"
    if path.endswith(AUDIO_EXTS):
        return "audio"
    return "file"


def log_incoming_webhook(request, payload: dict) -> None:
    logger = logging.getLogger("webhook")
    try:
        body = json.dumps(payload, ensure_ascii=False)
    except Exception:
        body = repr(payload)
    logger.info(
        "IN  %s %s from %s msgId=%s from=%s to=%s media=%s payload=%s",
        request.method,
        request.url.path,
        _client_ip(request),
        payload.get("messageId"),
        payload.get("from"),
        payload.get("to"),
        detect_media_type(payload.get("file") or ""),
        body,
    )


def log_telegram_success(payload: dict, message_id) -> None:
    logger = logging.getLogger("telegram")
    logger.info(
        "OUT ok message_id=%s msgId=%s",
        message_id,
        payload.get("messageId"),
    )


def log_telegram_failure(payload: dict, stage: str, detail) -> None:
    logger = logging.getLogger("telegram")
    logger.error(
        "FAIL stage=%s msgId=%s detail=%s",
        stage,
        payload.get("messageId"),
        detail,
    )
