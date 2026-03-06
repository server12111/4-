import logging

import aiohttp

from config import BOTOHUB_KEY
from database import get_db

logger = logging.getLogger(__name__)

BOTOHUB_URL = 'https://botohub.me/get-tasks'


async def check_botohub(user_id: int) -> dict:
    if not BOTOHUB_KEY:
        return {'completed': True, 'skip': True, 'tasks': []}

    headers = {'Auth': BOTOHUB_KEY, 'Content-Type': 'application/json'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                BOTOHUB_URL,
                json={'chat_id': user_id},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status != 200:
                    logger.warning('BotoHub: status %s for user %s', resp.status, user_id)
                    return {'completed': True, 'skip': True, 'tasks': []}
                data = await resp.json()
                return {
                    'completed': bool(data.get('completed', True)),
                    'skip': bool(data.get('skip', False)),
                    'tasks': data.get('tasks', []),
                }
    except Exception as exc:
        logger.warning('BotoHub error for user %s: %s', user_id, exc)
        return {'completed': True, 'skip': True, 'tasks': []}


def save_botohub_count(count: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE config SET value = ? WHERE key = 'botohub_sponsors_count'", (str(count),)
        )
        conn.commit()


def get_botohub_count() -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM config WHERE key = 'botohub_sponsors_count'"
        ).fetchone()
        return int(row[0]) if row else 0
