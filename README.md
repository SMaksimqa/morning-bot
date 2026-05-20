# Morning Bot

Личный Telegram-бот: погода в Москве и Паттайе + курсы валют.

## Что показывает

- Погода Москва (с прогнозом на день)
- Погода Паттайя
- Курс USD ЦБ РФ
- Курс USD в Камкомбанке (отделение Чертановская)

## Запуск

Создать `.env` по образцу `.env.example`, затем:

docker compose up -d –build


## Стек

Python 3.12, aiogram 3, httpx, BeautifulSoup, Docker
