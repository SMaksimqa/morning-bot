import logging
import re
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

KAMKOM_URL = "https://bankiros.ru/bank/kamkombank/currency/moskva"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

OFFICE_KEYWORD = "Чертановская"

NUMBER_PATTERN = re.compile(r"<span[^>]*>\s*(\d{2,3}[.,]\d{1,2})\s*</span>")



@dataclass
class BankRate:
    bank: str
    buy: float
    sell: float
    branch: str


async def fetch_kamkom() -> BankRate | None:
    params = {
        "all": "1",
        "first_load": "1",
        "time": str(int(time.time() * 1000)),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            response = await client.get(KAMKOM_URL, params=params)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as e:
        logger.error("Ошибка запроса Камкомбанк: %s", e)
        return None

    keyword_pos = html.find(OFFICE_KEYWORD)
    if keyword_pos == -1:
        logger.error("Камкомбанк: не найден '%s' в ответе (длина=%d)", OFFICE_KEYWORD, len(html))
        return None

    chunk = html[keyword_pos:keyword_pos + 3000]

    matches = NUMBER_PATTERN.findall(chunk)

    candidates = []
    for m in matches:
        try:
            value = float(m.replace(",", "."))
            if 50 < value < 150:
                candidates.append(value)
        except ValueError:
            continue

    if len(candidates) < 2:
        logger.error("Камкомбанк: рядом с '%s' мало курсов: %s", OFFICE_KEYWORD, candidates)
        return None

    buy, sell = candidates[0], candidates[1]

    if buy > sell:
        buy, sell = sell, buy

    logger.info("Камкомбанк (Чертановская): buy=%.2f sell=%.2f", buy, sell)

    return BankRate(
        bank="Камком",
        buy=buy,
        sell=sell,
        branch="Чертановская",
    )
