import requests
import threading
from bs4 import BeautifulSoup
import time

BASE = "https://dental-first.ru/catalog"  # Убрана лишняя кавычка

products = []
total_price = 0
lock = threading.Lock()

# Определяем страницы для парсинга с использованием структуры пагинации сайта
URLS = [
    BASE,
    BASE + "?PAGEN_1=1",
    BASE + "?PAGEN_1=2",
    BASE + "?PAGEN_1=3"
]

def parse_real_catalog(url):
    global total_price

    try:
        # Парсим фактическое содержимое страницы
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"Не удалось загрузить {url}: Статус {r.status_code}")
            return
            
        soup = BeautifulSoup(r.text, "html.parser")

        local_list = []
        local_sum = 0

        # Выбираем карточки товаров (на основе структуры кода друга)
        items = soup.select(".set-card.block")

        for card in items:
            name_tag = card.select_one("a.di_b.c_b")
            name = name_tag.get_text(strip=True) if name_tag else "БЕЗ_НАЗВАНИЯ"

            price_tag = card.select_one(".set-card__price")
            price_text = price_tag.get_text(strip=True) if price_tag else "0"

            # Очищаем строку с ценой
            price_text = price_text.replace(" ", "").replace("₽", "").replace(",", ".")

            try:
                price = float(price_text)
            except ValueError:
                price = 0.0

            local_list.append((name, price))
            local_sum += price

        with lock:
            products.extend(local_list)
            total_price += local_sum
    except Exception as e:
        print(f"Ошибка при парсинге {url}: {e}")

def run_threaded_scraper():
    start_time = time.time()
    threads = []
    
    for url in URLS:
        t = threading.Thread(target=parse_real_catalog, args=(url,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()

    duration = time.time() - start_time

    with open("result_threaded.txt", "w", encoding="utf-8") as f:
        for name, price in products:
            f.write(f"{name} | {price}\n")
        f.write(f"\nОБЩАЯ СТОИМОСТЬ: {total_price}")
        f.write(f"\nНайдено товаров: {len(products)}")
        f.write(f"\nВремя выполнения: {duration:.4f} секунд")

    print("\n--- Результаты многопоточного парсера (Настоящий сайт) ---")
    print(f"Время выполнения: {duration:.4f} секунд")
    print(f"Найдено товаров: {len(products)}")
    print(f"Общая стоимость: ${total_price:.2f}")
    print("Данные записаны в result_threaded.txt")

if __name__ == "__main__":
    run_threaded_scraper()