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

URLS = [
    ("bbr_main", "https://bbr.ru/"),
    ("bankiros_bbr", "https://bankiros.ru/bank/bbrbank/currency/moskva"),
    ("mainfin_bbr", "https://mainfin.ru/bank/bbrbank/currency/moskva"),
]


async def check(name: str, url: str):
    print(f"\n=== {name} ===")
    print(f"URL: {url}")
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(url)
            html = r.text

        print(f"Status: {r.status_code}")
        print(f"Length: {len(html)}")
        print(f"Final URL: {r.url}")

        filename = f"dump_{name}.html"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved: {filename}")

        addresses = re.findall(r"(Одесская[^<\n]{1,200})", html)
        unique = list(dict.fromkeys(addresses))[:5]
        print(f"Найдено 'Одесская': {len(unique)}")
        for i, a in enumerate(unique, 1):
            print(f"  {i}. {a.strip()[:120]}")

        usd_mentions = len(re.findall(r"USD|доллар", html, re.IGNORECASE))
        print(f"Упоминаний USD/доллар: {usd_mentions}")

    except Exception as e:
        print(f"Ошибка: {e}")


async def main():
    for name, url in URLS:
        await check(name, url)


asyncio.run(main())
