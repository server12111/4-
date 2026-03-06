import random
from datetime import datetime

from aiogram import Router, F, types

from database import get_db, get_user

router = Router()


@router.callback_query(F.data == 'daily_bonus')
async def cb_daily_bonus(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if not u or u['banned']:
        return

    today = datetime.now().strftime('%Y-%m-%d')
    if u['last_bonus_date'] == today:
        await callback.answer('⏳ Ты уже забирал бонус сегодня!', show_alert=True)
        return

    with get_db() as conn:
        b_min = float(conn.execute("SELECT value FROM config WHERE key = 'bonus_min'").fetchone()[0])
        b_max = float(conn.execute("SELECT value FROM config WHERE key = 'bonus_max'").fetchone()[0])
        reward = round(random.uniform(b_min, b_max), 2)
        conn.execute(
            'UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, last_bonus_date = ? WHERE user_id = ?',
            (reward, reward, today, u['user_id']),
        )
        conn.commit()

    await callback.answer(f'🎁 Ты получил бонус: {reward} ⭐!', show_alert=True)
