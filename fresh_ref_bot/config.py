import os
from dotenv import load_dotenv

load_dotenv()


def _parse_ids(raw: str) -> list[int]:
    return [int(x) for x in raw.split(',') if x.strip().isdigit()]


BOT_TOKEN: str = os.getenv('BOT_TOKEN', '').strip()
ADMIN_IDS: list[int] = _parse_ids(os.getenv('ADMIN_IDS', ''))
DB_NAME: str = os.getenv('BOT_DB', 'fresh_ref_bot.db')
BOTOHUB_KEY: str = os.getenv('BOTOHUB_KEY', '').strip()
FLYER_KEY: str = os.getenv('FLYER_KEY', '').strip()
REFERRAL_REWARD: float = float(os.getenv('REFERRAL_REWARD', '1.0'))

if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN is empty')
