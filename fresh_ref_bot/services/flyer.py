import logging

from config import FLYER_KEY

try:
    from flyerapi import Flyer as FlyerClient
except ImportError:
    FlyerClient = None

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if FlyerClient is None or not FLYER_KEY:
        return None
    if _client is None:
        _client = FlyerClient(FLYER_KEY)
    return _client


async def check_subscription(user_id: int, language_code: str | None = None) -> bool:
    client = _get_client()
    if client is None:
        return True
    try:
        return await client.check(user_id=user_id, language_code=language_code or 'ru')
    except Exception as exc:
        logger.warning('Flyer error for user %s: %s', user_id, exc)
        return True


async def get_channels_count() -> int:
    client = _get_client()
    if client is None:
        return 0
    try:
        info = await client.get_me()
        channels = info.get('channels') or info.get('resources') or []
        return len(channels)
    except Exception as exc:
        logger.warning('Flyer get_me error: %s', exc)
        return 0
