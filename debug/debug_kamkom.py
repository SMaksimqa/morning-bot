import asyncio
import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

URLS = [
    ("kamkombank_main", "https://www.kamkombank.ru/"),
    ("kamkombank_rates", "https://www.kamkombank.ru/private/exchange/"),
    ("bankiros", "https://bankiros.ru/bank/kamkombank/currency/moskva"),
]


async def check(name: str, url: str):
    print(f"\n=== {name} ===")
    print(f"URL: {url}")
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            print(f"Status: {r.status_code}")
            print(f"Length: {len(r.text)}")
            print(f"Final URL: {r.url}")

            filename = f"dump_{name}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"Saved: {filename}")

            text_lower = r.text.lower()
            for marker in ["доллар", "usd", "76.", "77.", "78.", "79.", "80.", "85.", "88.", "90."]:
                if marker in text_lower:
                    print(f"  ✓ найдено: '{marker}'")
                    break
            else:
                print("  ✗ ни одного маркера курса не найдено")

    except Exception as e:
        print(f"Ошибка: {e}")


async def main():
    for name, url in URLS:
        await check(name, url)


asyncio.run(main())
