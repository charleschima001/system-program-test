import asyncio
import aiohttp
import time
from bs4 import BeautifulSoup  # Добавлен отсутствующий импорт

BASE = "https://dental-first.ru/catalog"  # Убрана лишняя кавычка

products = []
total_price = 0

# Определяем страницы для парсинга
URLS = [
    BASE,
    BASE + "?PAGEN_1=1",
    BASE + "?PAGEN_1=2",
    BASE + "?PAGEN_1=3"
]

async def parse_real_catalog_async(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                print(f"Не удалось загрузить {url}: Статус {response.status}")
                return [], 0
                
            response_text = await response.text()
            soup = BeautifulSoup(response_text, "html.parser")

            local_list = []
            local_sum = 0
            items = soup.select(".set-card.block")

            for card in items:
                name_tag = card.select_one("a.di_b.c_b")
                name = name_tag.get_text(strip=True) if name_tag else "БЕЗ_НАЗВАНИЯ"

                price_tag = card.select_one(".set-card__price")
                price_text = price_tag.get_text(strip=True) if price_tag else "0"
                price_text = price_text.replace(" ", "").replace("₽", "").replace(",", ".")

                try:
                    price = float(price_text)
                except ValueError:
                    price = 0.0

                local_list.append((name, price))
                local_sum += price
                
            return local_list, local_sum
    except Exception as e:
        print(f"Ошибка при парсинге {url}: {e}")
        return [], 0

async def run_async_scraper():
    global total_price, products
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [parse_real_catalog_async(session, url) for url in URLS]
        # Собираем результаты параллельно со всех страниц
        results = await asyncio.gather(*tasks)

    # Агрегируем результаты после завершения всех запросов
    for local_list, local_sum in results:
        products.extend(local_list)
        total_price += local_sum

    duration = time.time() - start_time

    with open("result_async.txt", "w", encoding="utf-8") as f:
        for name, price in products:
            f.write(f"{name} | {price}\n")
        f.write(f"\nОБЩАЯ СТОИМОСТЬ: {total_price}")
        f.write(f"\nНайдено товаров: {len(products)}")
        f.write(f"\nВремя выполнения: {duration:.4f} секунд")

    print("\n--- Результаты асинхронного парсера (Настоящий сайт) ---")
    print(f"Время выполнения: {duration:.4f} секунд")
    print(f"Найдено товаров: {len(products)}")
    print(f"Общая стоимость: ${total_price:.2f}")
    print("Данные записаны в result_async.txt")

if __name__ == "__main__":
    asyncio.run(run_async_scraper())