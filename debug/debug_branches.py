import asyncio
import re
import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}


async def main():
    url = "https://bankiros.ru/bank/kamkombank/currency/moskva"
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
        r = await client.get(url)
        html = r.text

    print(f"HTML длина: {len(html)}")
    print()

    addresses = re.findall(r"г\.\s*Москва[^<\n]{1,200}", html)
    unique = list(dict.fromkeys(addresses))[:20]

    print(f"Найдено уникальных упоминаний адресов: {len(unique)}")
    print()
    for i, addr in enumerate(unique, 1):
        print(f"{i}. {addr.strip()[:150]}")


asyncio.run(main())
