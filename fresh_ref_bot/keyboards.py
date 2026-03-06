from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✨ Профиль', callback_data='profile'),
            InlineKeyboardButton(text='👥 Рефералы', callback_data='refs'),
        ],
        [
            InlineKeyboardButton(text='🎁 Ежедневный Бонус', callback_data='daily_bonus'),
            InlineKeyboardButton(text='🎰 Рулетка', callback_data='spin'),
        ],
        [
            InlineKeyboardButton(text='💳 Вывод', callback_data='withdraw_menu'),
            InlineKeyboardButton(text='📝 Задания', callback_data='tasks'),
        ],
    ])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')]]
    )


def withdraw_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='15 ⭐', callback_data='wd_15'),
            InlineKeyboardButton(text='25 ⭐', callback_data='wd_25'),
        ],
        [
            InlineKeyboardButton(text='50 ⭐', callback_data='wd_50'),
            InlineKeyboardButton(text='100 ⭐', callback_data='wd_100'),
        ],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')],
    ])


def botohub_wall_kb(tasks: list) -> InlineKeyboardMarkup:
    rows = []
    for i, url in enumerate(tasks, start=1):
        rows.append([InlineKeyboardButton(text=f'Канал #{i}', url=url)])
    rows.append([InlineKeyboardButton(text='✅ Я подписался', callback_data='botohub:check')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def required_subs_kb(channels: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f'Канал #{i}', url=row['link'])]
        for i, row in enumerate(channels, start=1)
    ]
    rows.append([InlineKeyboardButton(text='✅ Я подписался', callback_data='check_subs')])
    return InlineKeyboardMarkup(inline_keyboard=rows)
