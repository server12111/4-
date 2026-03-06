from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import get_db
from keyboards import back_kb, main_kb

router = Router()


@router.callback_query(F.data == 'tasks')
async def cb_tasks(callback: types.CallbackQuery):
    uid = callback.from_user.id
    with get_db() as conn:
        tasks = conn.execute('SELECT * FROM tasks WHERE is_active = 1 ORDER BY id DESC').fetchall()
        done = conn.execute('SELECT task_id FROM completed_tasks WHERE user_id = ?', (uid,)).fetchall()

    done_ids = {r['task_id'] for r in done}
    rows = []
    for t in tasks:
        if t['id'] in done_ids:
            continue
        label = t['title'] if t['title'] else t['link']
        rows.append([InlineKeyboardButton(text=f'{label} ({t["reward"]}⭐)', url=t['link'])])
        rows.append([InlineKeyboardButton(text=f'✅ Проверить #{t["id"]}', callback_data=f'task_done_{t["id"]}')])

    rows.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')])

    text = '🎉 Вы выполнили все доступные задания!' if len(rows) == 1 else '📝 <b>Доступные задания:</b>\nПерейдите по ссылке и нажмите «Проверить».'
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


@router.callback_query(F.data.startswith('task_done_'))
async def cb_task_done(callback: types.CallbackQuery):
    uid = callback.from_user.id
    task_id = int(callback.data.split('_')[-1])

    with get_db() as conn:
        t = conn.execute('SELECT * FROM tasks WHERE id = ? AND is_active = 1', (task_id,)).fetchone()
        if not t:
            await callback.answer('Задание не найдено.', show_alert=True)
            return

        inserted = conn.execute(
            'INSERT OR IGNORE INTO completed_tasks (user_id, task_id) VALUES (?, ?)', (uid, task_id)
        )
        if inserted.rowcount == 0:
            await callback.answer('Уже засчитано ранее.', show_alert=True)
            return

        conn.execute(
            'UPDATE users SET balance = balance + ?, total_earned = total_earned + ?, tasks_done = tasks_done + 1 WHERE user_id = ?',
            (t['reward'], t['reward'], uid),
        )
        conn.commit()

    await callback.answer(f"✅ Задание выполнено! Начислено {t['reward']}⭐", show_alert=True)
    await cb_tasks(callback)
