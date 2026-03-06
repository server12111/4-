from datetime import datetime

from aiogram import Router, F, types

from database import get_db, get_user
from keyboards import withdraw_kb, back_kb

router = Router()


@router.callback_query(F.data == 'withdraw_menu')
async def cb_withdraw_menu(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if not u or u['banned']:
        return
    await callback.message.edit_text('🏦 Выберите сумму для вывода:', reply_markup=withdraw_kb())
    await callback.answer()


@router.callback_query(F.data.startswith('wd_'))
async def cb_withdraw_create(callback: types.CallbackQuery):
    uid = callback.from_user.id
    amount = float(callback.data.split('_')[1])
    u = get_user(uid)
    if not u or u['banned']:
        return

    if u['balance'] < amount:
        await callback.answer(f'❌ Недостаточно средств! Нужно {amount:.0f}⭐', show_alert=True)
        return

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        conn.execute(
            'UPDATE users SET balance = balance - ?, withdraw_count = withdraw_count + 1, withdraw_total = withdraw_total + ? WHERE user_id = ?',
            (amount, amount, uid),
        )
        cur = conn.execute(
            'INSERT INTO withdraw_requests (user_id, username, amount, created_at) VALUES (?, ?, ?, ?)',
            (uid, u['username'], amount, now),
        )
        req_id = cur.lastrowid
        log_chat = int(conn.execute("SELECT value FROM config WHERE key = 'log_chat_id'").fetchone()[0])
        conn.commit()

    await callback.message.edit_text(
        f'✅ <b>ЗАЯВКА №{req_id} СОЗДАНА!</b>\n\n'
        f'Сумма: {amount:.0f} ⭐\n'
        f'Ожидайте выплату. Номер заявки сохраните для проверки.',
        parse_mode='HTML',
        reply_markup=back_kb(),
    )
    await callback.answer()

    if log_chat != 0:
        try:
            await callback.bot.send_message(
                log_chat,
                f'🆕 <b>Новая заявка на вывод</b>\n'
                f'Номер: #{req_id}\n'
                f'Пользователь: @{u["username"]} (ID {uid})\n'
                f'Сумма: {amount:.0f} ⭐',
                parse_mode='HTML',
            )
        except Exception:
            pass
