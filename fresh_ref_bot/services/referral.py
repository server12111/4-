import logging

from aiogram import Bot

from config import REFERRAL_REWARD
from database import get_db, get_user

logger = logging.getLogger(__name__)


async def grant_referral_reward(referred_id: int, bot: Bot) -> None:
    with get_db() as conn:
        user = conn.execute(
            'SELECT referrer_id, referral_reward_pending FROM users WHERE user_id = ?',
            (referred_id,),
        ).fetchone()
        if not user or not user['referral_reward_pending'] or not user['referrer_id']:
            return

        referrer_id = user['referrer_id']
        if not get_user(referrer_id):
            conn.execute(
                'UPDATE users SET referral_reward_pending = 0 WHERE user_id = ?', (referred_id,)
            )
            conn.commit()
            return

        referred = conn.execute(
            'SELECT username FROM users WHERE user_id = ?', (referred_id,)
        ).fetchone()
        username = referred['username'] if referred else str(referred_id)

        conn.execute(
            'UPDATE users SET referral_reward_pending = 0 WHERE user_id = ?', (referred_id,)
        )
        conn.execute(
            'UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, '
            'ref_income = ref_income + ? WHERE user_id = ?',
            (REFERRAL_REWARD, REFERRAL_REWARD, REFERRAL_REWARD, referrer_id),
        )
        conn.commit()

    try:
        await bot.send_message(referrer_id, f'Новый реферал: @{username}\nНачислено +{REFERRAL_REWARD}⭐')
    except Exception:
        pass
