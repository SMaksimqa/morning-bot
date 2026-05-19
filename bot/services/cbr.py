import logging
from dataclasses import dataclass
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"


@dataclass
class CbrRates:
    usd: float
    date: str


async def fetch_cbr_rates() -> CbrRates | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(CBR_URL)
            response.raise_for_status()
            content = response.content
    except httpx.HTTPError as e:
        logger.error("Ошибка запроса ЦБ: %s", e)
        return None

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.error("Ошибка парсинга XML ЦБ: %s", e)
        return None

    date = root.get("Date", "")

    rates = {}
    for valute in root.findall("Valute"):
        char_code = valute.findtext("CharCode")
        nominal_str = valute.findtext("Nominal")
        value_str = valute.findtext("Value")

        if not char_code or not nominal_str or not value_str:
            continue

        try:
            nominal = int(nominal_str)
            value = float(value_str.replace(",", "."))
        except ValueError:
            continue

        if nominal > 0:
            rates[char_code] = value / nominal

    if "USD" not in rates or "THB" not in rates:
        logger.error("В ответе ЦБ нет USD или THB. Найдено: %s", list(rates.keys())[:10])
        return None

    return CbrRates(
        usd=round(rates["USD"], 2),
        date=date,
    )
