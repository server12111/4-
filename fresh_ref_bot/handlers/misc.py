from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, CommandObject

from database import get_db, get_user, refs_count, today_refs_count

router = Router()


@router.message(Command('top'))
async def top_cmd(message: types.Message):
    with get_db() as conn:
        rows = conn.execute(
            'SELECT user_id, username, total_earned FROM users WHERE banned = 0 ORDER BY total_earned DESC LIMIT 10'
        ).fetchall()

    if not rows:
        await message.answer('Пока нет данных.')
        return

    lines = ['<b>ТОП 10 по заработку</b>']
    for i, row in enumerate(rows, start=1):
        lines.append(f"{i}. @{row['username']} (ID {row['user_id']}) — {row['total_earned']:.2f}⭐")
    await message.answer('\n'.join(lines), parse_mode='HTML')


@router.message(Command('code'))
async def promo_use(message: types.Message, command: CommandObject):
    u = get_user(message.from_user.id)
    if not u or u['banned']:
        return

    if not command.args:
        await message.answer('⚠️ Использование: /code [промокод]')
        return

    code = command.args.strip()
    with get_db() as conn:
        promo = conn.execute(
            'SELECT * FROM promocodes WHERE code = ? AND is_active = 1', (code,)
        ).fetchone()
        if not promo:
            await message.answer('❌ Такого промокода не существует!')
            return
        used = conn.execute(
            'SELECT 1 FROM used_promos WHERE user_id = ? AND code = ?', (u['user_id'], code)
        ).fetchone()
        if used:
            await message.answer('❌ Ты уже использовал этот промокод!')
            return

        conn.execute('INSERT INTO used_promos (user_id, code) VALUES (?, ?)', (u['user_id'], code))
        conn.execute(
            'UPDATE users SET balance = balance + ?, total_earned = total_earned + ? WHERE user_id = ?',
            (promo['reward'], promo['reward'], u['user_id']),
        )
        conn.commit()

    await message.answer(f"✅ Промокод активирован!\nВам начислено: <b>{promo['reward']} ⭐</b>", parse_mode='HTML')


@router.message(Command('free'))
async def free_cmd(message: types.Message):
    u = get_user(message.from_user.id)
    if not u or u['banned']:
        return

    if u['used_free_promo']:
        await message.answer('❌ Ты уже использовал команду /free на этом аккаунте!')
        return

    refs = refs_count(u['user_id'])
    if refs >= 5:   rew = 1.0
    elif refs >= 4: rew = 0.75
    elif refs >= 2: rew = 0.5
    elif refs >= 1: rew = 0.3
    else:           rew = 0.25

    with get_db() as conn:
        conn.execute(
            'UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, used_free_promo = 1 WHERE user_id = ?',
            (rew, rew, u['user_id']),
        )
        conn.commit()

    await message.answer(
        f'🎟 <b>FREE PROMO</b>\nТвои рефералы: {refs}\nТвоя награда: <b>+{rew} ⭐</b>',
        parse_mode='HTML',
    )


@router.message(Command('send'))
async def send_cmd(message: types.Message, command: CommandObject):
    u = get_user(message.from_user.id)
    if not u or u['banned']:
        return

    if not command.args:
        await message.answer('⚠️ Использование: /send [ID] [сумма]')
        return

    parts = command.args.split()
    if len(parts) < 2 or not parts[0].isdigit():
        await message.answer('⚠️ Использование: /send [ID] [сумма]')
        return

    try:
        target_id = int(parts[0])
        amount = float(parts[1])
    except ValueError:
        await message.answer('❌ ID и сумма должны быть числами.')
        return

    if amount <= 0:
        await message.answer('❌ Сумма должна быть больше 0.')
        return
    if u['balance'] < amount:
        await message.answer('❌ Недостаточно средств!')
        return

    today_refs = today_refs_count(u['user_id'])
    if today_refs < 3:
        await message.answer(
            f'🛑 <b>Для перевода нужно пригласить 3 реферала сегодня!</b>\nПриглашено сегодня: {today_refs}/3',
            parse_mode='HTML',
        )
        return

    if not get_user(target_id):
        await message.answer('❌ Пользователь не найден в базе бота.')
        return

    fee = round(amount * 0.05, 2)
    received = round(amount - fee, 2)
    with get_db() as conn:
        conn.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, u['user_id']))
        conn.execute(
            'UPDATE users SET balance = balance + ?, total_earned = total_earned + ? WHERE user_id = ?',
            (received, received, target_id),
        )
        conn.commit()

    await message.answer(
        f'✅ Успешный перевод!\nОтправлено: {amount} ⭐\nКомиссия (5%): {fee} ⭐\nПолучателю дошло: <b>{received} ⭐</b>',
        parse_mode='HTML',
    )
    try:
        await message.bot.send_message(
            target_id,
            f'💸 <b>Вам поступил перевод!</b>\nОт: ID {u["user_id"]}\nСумма: <b>+{received} ⭐</b>',
            parse_mode='HTML',
        )
    except Exception:
        pass
