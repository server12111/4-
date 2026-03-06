import time
from datetime import datetime

from aiogram import Router, F, types
from aiogram.filters import CommandStart, CommandObject

from config import ADMIN_IDS
from database import get_db, get_user
from keyboards import main_kb, botohub_wall_kb
from services.botohub import check_botohub, save_botohub_count
from services.flyer import check_subscription
from services.referral import grant_referral_reward
from services.subs import check_required_subs, send_sub_gate

router = Router()


MENU_TEXT = '👋 Привет! Добро пожаловать в бота. Выбирай действие:'


async def open_menu(target: types.Message | types.CallbackQuery) -> None:
    if isinstance(target, types.Message):
        await target.answer(MENU_TEXT, reply_markup=main_kb())
    else:
        try:
            await target.message.edit_text(MENU_TEXT, reply_markup=main_kb())
        except Exception:
            await target.message.answer(MENU_TEXT, reply_markup=main_kb())


@router.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    uid = message.from_user.id
    username = message.from_user.username or f'user_{uid}'
    today = datetime.now().strftime('%Y-%m-%d')
    ref_id = None

    if command.args and command.args.isdigit():
        x = int(command.args)
        if x != uid:
            ref_id = x

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (uid,)).fetchone()
        if user and user['banned'] == 1:
            return

        if not user:
            has_referrer = ref_id is not None and bool(get_user(ref_id))
            conn.execute(
                'INSERT INTO users (user_id, username, referrer_id, join_date, last_login, referral_reward_pending) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (uid, username, ref_id if has_referrer else None, today, today, 1 if has_referrer else 0),
            )
            if has_referrer:
                conn.execute(
                    'INSERT INTO referrals (referrer_id, referred_id, join_ts) VALUES (?, ?, ?)',
                    (ref_id, uid, int(time.time())),
                )
            conn.commit()
        else:
            if user['last_login'] != today:
                conn.execute(
                    'UPDATE users SET last_login = ?, streak = streak + 1, username = ? WHERE user_id = ?',
                    (today, username, uid),
                )
            else:
                conn.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, uid))
            conn.commit()

    if uid not in ADMIN_IDS:
        # BotoHub wall
        bh = await check_botohub(uid)
        if not bh['completed'] and not bh['skip']:
            save_botohub_count(len(bh['tasks']))
            await message.answer(
                '📢 <b>Подпишитесь на каналы ниже и нажмите «Я подписался».</b>',
                reply_markup=botohub_wall_kb(bh['tasks']),
                parse_mode='HTML',
            )
            return

        # Flyer wall
        if not await check_subscription(uid, message.from_user.language_code):
            return  # Flyer сам надсилає повідомлення

    # Required channels wall
    if not await check_required_subs(uid, message.bot):
        await send_sub_gate(uid, message.bot)
        return

    await grant_referral_reward(uid, message.bot)
    await open_menu(message)


@router.callback_query(F.data == 'botohub:check')
async def cb_botohub_check(callback: types.CallbackQuery):
    uid = callback.from_user.id
    bh = await check_botohub(uid)

    if bh['completed'] or bh['skip']:
        if not await check_subscription(uid, callback.from_user.language_code):
            await callback.answer()
            return

        if not await check_required_subs(uid, callback.bot):
            await send_sub_gate(uid, callback.bot)
            await callback.answer()
            return

        await grant_referral_reward(uid, callback.bot)
        await callback.answer('✅ Подписка подтверждена!')
        await open_menu(callback)
    else:
        await callback.answer('❌ Ещё не все каналы. Подпишитесь и нажмите снова.', show_alert=True)
        if bh['tasks']:
            try:
                await callback.message.edit_reply_markup(reply_markup=botohub_wall_kb(bh['tasks']))
            except Exception:
                pass


@router.callback_query(F.data == 'check_subs')
async def cb_check_subs(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if await check_required_subs(uid, callback.bot):
        await grant_referral_reward(uid, callback.bot)
        await callback.answer('✅ Доступ открыт!')
        await open_menu(callback)
    else:
        await callback.answer('Еще не все подписки выполнены.', show_alert=True)
