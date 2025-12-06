from flask import Flask, jsonify
import time
import random

app = Flask(__name__)

# Мок-данные для демонстрации
products = {
    f"page_{i}": [
        {"name": f"Товар {i*10 + j}", "price": round(random.uniform(10.0, 100.0), 2)}
        for j in range(10)
    ]
    for i in range(1, 5) # Только 4 страницы, чтобы соответствовать количеству URL друга
}

@app.route('/catalog')
@app.route('/catalog/<page_id>')
def get_catalog_page(page_id=None):
    # Имитация сетевой задержки
    time.sleep(0.1) 
    
    # Если конкретная страница не запрошена, возвращаем все мок-данные объединенными
    if page_id is None:
        all_prods = []
        for page in products.values():
            all_prods.extend(page)
        return jsonify({"products": all_prods})
    
    if page_id in products:
        return jsonify({"products": products[page_id]})
        
    return jsonify({"error": "Страница не найдена"}), 404

if __name__ == '__main__':
    print("Запуск мок-сервера веб-сайта на http://127.0.0.1:5001")
    # Запустите это в отдельном терминале
    app.run(port=5001, debug=False)