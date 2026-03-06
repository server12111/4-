from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from database import get_db
from keyboards import required_subs_kb


async def check_required_subs(user_id: int, bot: Bot) -> bool:
    with get_db() as conn:
        channels = conn.execute('SELECT link FROM required_channels').fetchall()

    if not channels:
        return True

    for row in channels:
        target = row['link']
        if 't.me/' in target:
            target = '@' + target.split('t.me/')[-1].strip('/')
        try:
            member = await bot.get_chat_member(chat_id=target, user_id=user_id)
            if member.status not in {'member', 'administrator', 'creator'}:
                return False
        except TelegramBadRequest:
            return False
        except Exception:
            return False
    return True


async def send_sub_gate(chat_id: int, bot: Bot) -> None:
    with get_db() as conn:
        channels = conn.execute('SELECT link FROM required_channels').fetchall()

    await bot.send_message(
        chat_id,
        'Чтобы пользоваться ботом, подпишись на обязательные каналы.',
        reply_markup=required_subs_kb(list(channels)),
    )
