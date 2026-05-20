import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from bot.services.weather import fetch_weather, describe_forecast  # noqa: E402
from bot.services.cbr import fetch_cbr_rates  # noqa: E402
from bot.services.banks.kamkom import fetch_kamkom  # noqa: E402

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = {
    int(uid.strip())
    for uid in os.getenv("ALLOWED_USERS", "").split(",")
    if uid.strip()
}
ALLOWED_CHATS = {
    int(cid.strip())
    for cid in os.getenv("ALLOWED_CHATS", "").split(",")
    if cid.strip()
}

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")
if not ALLOWED_USERS and not ALLOWED_CHATS:
    raise RuntimeError("Нужен ALLOWED_USERS или ALLOWED_CHATS в .env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def is_access_granted(message: Message) -> bool:
    if message.chat.id in ALLOWED_CHATS:
        return True
    if message.from_user and message.from_user.id in ALLOWED_USERS:
        return True
    return False


async def send_morning_report(message: Message) -> None:
    await message.answer("Собираю данные...")

    moscow, pattaya, cbr, kamkom = await asyncio.gather(
        fetch_weather("moscow", with_forecast=True),
        fetch_weather("pattaya"),
        fetch_cbr_rates(),
        fetch_kamkom(),
    )

    lines = []
    if moscow:
        lines.append(
            f"{moscow.icon} Москва: {moscow.temp:+.1f}°C, {moscow.description}"
        )
        forecast_text = describe_forecast(moscow)
        if forecast_text:
            lines.append(forecast_text)
    else:
        lines.append("⚠️ Москва: ошибка получения погоды")

    lines.append("")

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


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if not is_access_granted(message):
        logger.warning("Отказ /start: chat=%s user=%s", message.chat.id, message.from_user.id)
        return

    await message.answer(
        "Привет! Я утренний бот.\n\n"
        "Команды:\n"
        "/now — погода и курсы валют\n"
        "/help — справка\n\n"
        "В группе можно написать «погода» или «курс» — отвечу тем же."
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not is_access_granted(message):
        return

    await message.answer(
        "Что я умею:\n"
        "/now — показать погоду в Москве и Паттайе + курсы USD/RUB\n\n"
        "Источники:\n"
        "Погода — OpenWeatherMap\n"
        "Курсы — ЦБ РФ, Камкомбанк"
    )


@dp.message(Command("now"))
async def cmd_now(message: Message) -> None:
    if not is_access_granted(message):
        logger.warning("Отказ /now: chat=%s user=%s", message.chat.id, message.from_user.id)
        return

    logger.info("Запрос /now: chat=%s user=%s", message.chat.id, message.from_user.id)
    await send_morning_report(message)


@dp.message(F.text.lower().contains("погода") | F.text.lower().contains("курс"))
async def on_keyword(message: Message) -> None:
    if not is_access_granted(message):
        return

    logger.info("Триггер по слову: chat=%s user=%s text=%s",
                message.chat.id, message.from_user.id, message.text)
    await send_morning_report(message)


async def main() -> None:
    logger.info("Бот запускается. Юзеры: %s, чаты: %s", ALLOWED_USERS, ALLOWED_CHATS)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
