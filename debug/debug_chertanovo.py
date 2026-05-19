import asyncio
import re
import time
import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}


async def main():
    url = "https://bankiros.ru/bank/kamkombank/currency/moskva"
    params = {
        "all": "1",
        "first_load": "1",
        "time": str(int(time.time() * 1000)),
    }

    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
        r = await client.get(url, params=params)
        html = r.text

    print(f"HTML длина: {len(html)}")
    print()

    positions = [m.start() for m in re.finditer("Чертановская", html)]
    print(f"Найдено упоминаний 'Чертановская': {len(positions)}")
    print(f"Позиции: {positions}")
    print()

    for i, pos in enumerate(positions, 1):
        print(f"\n=== Упоминание #{i} (позиция {pos}) ===")
        snippet = html[pos:pos + 1500]
        snippet = re.sub(r"\s+", " ", snippet)
        print(snippet[:1000])
        print("---")


asyncio.run(main())
