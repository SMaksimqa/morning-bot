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
    url = "https://avosend.com/"
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
        r = await client.get(url)
        html = r.text

    print(f"Status: {r.status_code}")
    print(f"Length: {len(html)}")
    print(f"Final URL: {r.url}")

    with open("dump_avosend.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved: dump_avosend.html")

    markers = ["THB", "бат", "RUB", "рубл", "курс", "rate"]
    for m in markers:
        count = len(re.findall(m, html, re.IGNORECASE))
        print(f"  '{m}': {count}")

    numbers = re.findall(r"\b\d{1,3}[.,]\d{1,4}\b", html)
    print(f"  Числовых значений: {len(numbers)}")
    if numbers:
        print(f"  Примеры: {numbers[:10]}")


asyncio.run(main())
