from datetime import datetime

from aiogram import Router, F, types

from database import get_db, get_user, refs_count, today_refs_count, get_rank
from keyboards import back_kb, main_kb

router = Router()


@router.callback_query(F.data == 'back_to_main')
async def cb_back(callback: types.CallbackQuery):
    await callback.message.edit_text('👋 Привет! Добро пожаловать в бота. Выбирай действие:', reply_markup=main_kb())
    await callback.answer()


@router.callback_query(F.data == 'profile')
async def cb_profile(callback: types.CallbackQuery):
    u = get_user(callback.from_user.id)
    if not u or u['banned']:
        return

    refs = refs_count(u['user_id'])
    xp = refs * 5
    level = (xp // 100) + 1
    need_refs = max(0, (level * 100 - xp) // 5)
    inviter = f"ID: {u['referrer_id']}" if u['referrer_id'] else 'Никто'

    text = (
        '✨ <b>ТВОЙ ПРОФИЛЬ</b> ✨\n\n'
        f'🤝 Тебя пригласил: {inviter}\n\n'
        f"👤 ID: <code>{u['user_id']}</code>\n"
        f"🏷 Ник: @{u['username']}\n"
        f"📅 В боте с: {u['join_date']}\n"
        f"⚡️ Серия входов: {u['streak']} дней\n\n"
        f'👥 Рефералы: {refs}\n'
        f'🏆 Ранг: {get_rank(refs)}\n'
        f'⭐️ Уровень: {level} (Опыт: {xp})\n'
        f"💰 Баланс: <b>{u['balance']:.2f} ⭐</b>\n"
        f"🎁 Всего заработано: {u['total_earned']:.2f} ⭐\n"
        f"💸 Выводов: {u['withdraw_count']} • Сумма: {u['withdraw_total']:.2f} ⭐\n\n"
        f'📈 До следующего уровня: {need_refs} рефералов\n'
        f"🎯 Выполнено заданий: {u['tasks_done']}\n"
        f"🎖 Достижения: {u['achievements']}"
    )
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=back_kb())
    await callback.answer()


@router.callback_query(F.data == 'refs')
async def cb_refs(callback: types.CallbackQuery):
    uid = callback.from_user.id
    u = get_user(uid)
    if not u or u['banned']:
        return

    me = await callback.bot.get_me()
    ref_link = f'https://t.me/{me.username}?start={uid}'
    total = refs_count(uid)
    today = today_refs_count(uid)
    inviter = f"ID: {u['referrer_id']}" if u['referrer_id'] else 'Нет'

    with get_db() as conn:
        first_ts = conn.execute(
            'SELECT MIN(join_ts) FROM referrals WHERE referrer_id = ?', (uid,)
        ).fetchone()[0]
        last_ts = conn.execute(
            'SELECT MAX(join_ts) FROM referrals WHERE referrer_id = ?', (uid,)
        ).fetchone()[0]

    first_date = datetime.fromtimestamp(first_ts).strftime('%Y-%m-%d') if first_ts else 'Нет'
    last_date = datetime.fromtimestamp(last_ts).strftime('%Y-%m-%d') if last_ts else 'Нет'

    text = (
        f'🔗 <b>Твоя реферальная ссылка:</b>\n<code>{ref_link}</code>\n\n'
        f'🤝 Твой рефер: {inviter}\n\n'
        f'🥇 Первый реферал: {first_date}\n'
        f'🆕 Последний реферал: {last_date}\n\n'
        f'👤 Всего рефералов: {total}\n'
        f'📅 Сегодня приглашено: {today}\n'
        f"🏆 Рекорд за день: {u['daily_record']}\n\n"
        f"💰 Доход с рефералов: <b>{u['ref_income']:.2f} ⭐</b>"
    )
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=back_kb())
    await callback.answer()
