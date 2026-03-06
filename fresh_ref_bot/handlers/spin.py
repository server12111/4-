import asyncio
from datetime import datetime

from aiogram import Router, F, types

from database import get_db, get_user
from keyboards import back_kb

router = Router()


@router.callback_query(F.data == 'spin')
async def cb_spin(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if not u or u['banned']:
        return

    today = datetime.now().strftime('%Y-%m-%d')
    if u['last_spin_date'] == today:
        await callback.answer('🎰 Приходи завтра! Крутить рулетку можно 1 раз в день.', show_alert=True)
        return

    with get_db() as conn:
        conn.execute('UPDATE users SET last_spin_date = ? WHERE user_id = ?', (today, u['user_id']))
        conn.commit()

    await callback.answer()
    await callback.message.answer('🎰 <b>Крутить можно 1 раз в день!</b>\nЕсли выпадет 777 = 10 ⭐', parse_mode='HTML')
    msg = await callback.message.answer_dice(emoji='🎰')
    await asyncio.sleep(2)

    if msg.dice.value == 64:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET balance = balance + 10, total_earned = total_earned + 10 WHERE user_id = ?',
                (u['user_id'],),
            )
            conn.commit()
        await callback.message.answer('🎉 <b>ДЖЕКПОТ! 777!</b>\nТы выиграл 10 ⭐!', parse_mode='HTML')
    else:
        await callback.message.answer('😢 Ничего не выпало. Повезет в следующий раз!')
