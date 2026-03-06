import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import start, cabinet, earn, bonus, withdraw, spin, misc, admin

logging.basicConfig(level=logging.INFO)


async def main():
    init_db()

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(cabinet.router)
    dp.include_router(earn.router)
    dp.include_router(bonus.router)
    dp.include_router(withdraw.router)
    dp.include_router(spin.router)
    dp.include_router(misc.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
