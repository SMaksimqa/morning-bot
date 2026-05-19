import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from bot.services.weather import fetch_weather  # noqa: E402
from bot.services.cbr import fetch_cbr_rates  # noqa: E402
from bot.services.banks.kamkom import fetch_kamkom  # noqa: E402

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = {
    int(uid.strip())
    for uid in os.getenv("ALLOWED_USERS", "").split(",")
    if uid.strip()
}

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")
if not ALLOWED_USERS:
    raise RuntimeError("ALLOWED_USERS не задан в .env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    user_id = message.from_user.id
    if not is_allowed(user_id):
        logger.warning("Отказ в доступе для user_id=%s", user_id)
        await message.answer("Доступ запрещён.")
        return

    await message.answer(
        "Привет! Я утренний бот.\n\n"
        "Команды:\n"
        "/now — погода и курсы валют\n"
        "/help — справка"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not is_allowed(message.from_user.id):
        return

    await message.answer(
        "Что я умею:\n"
        "/now — показать погоду в Москве и Паттайе + курсы USD/RUB и THB/USD\n\n"
        "Источники:\n"
        "Погода — OpenWeatherMap\n"
        "Курсы — ЦБ РФ, Камкомбанк, ББР, TT Exchange, Super Rich"
    )


@dp.message(Command("now"))
async def cmd_now(message: Message) -> None:
    if not is_allowed(message.from_user.id):
        logger.warning("Отказ в /now для user_id=%s", message.from_user.id)
        return

    logger.info("Запрос /now от user_id=%s", message.from_user.id)
    await message.answer("Собираю данные...")

    moscow, pattaya, cbr, kamkom = await asyncio.gather(
        fetch_weather("moscow"),
        fetch_weather("pattaya"),
        fetch_cbr_rates(),
        fetch_kamkom(),
    )

    lines = []
    if moscow:
        lines.append(
            f"{moscow.icon} Москва: {moscow.temp:+.1f}°C, {moscow.description}"
        )
    else:
        lines.append("⚠️ Москва: ошибка получения погоды")

    if pattaya:
        lines.append(
            f"{pattaya.icon} Паттайя: {pattaya.temp:+.1f}°C, {pattaya.description}"
        )
    else:
        lines.append("⚠️ Паттайя: ошибка получения погоды")

    lines.append("")

    if cbr:
        lines.append(f"💱 ЦБ РФ USD: {cbr.usd:.2f} ₽ ({cbr.date})")
    else:
        lines.append("⚠️ ЦБ РФ: ошибка получения курса")

    if kamkom:
        lines.append(f"🏦 Камком ({kamkom.branch}): {kamkom.buy:.2f} / {kamkom.sell:.2f}")

    else:
        lines.append("⚠️ Камкомбанк: ошибка получения курса")

    await message.answer("\n".join(lines))


async def main() -> None:
    logger.info("Бот запускается. Разрешённые пользователи: %s", ALLOWED_USERS)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
