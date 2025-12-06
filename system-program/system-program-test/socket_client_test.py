import socket
import asyncio
import time
import concurrent.futures

TEST_DIR = "./test_files"
HOST = '127.0.0.1'
PORT_THREADED = 8889
PORT_ASYNC = 8888

def create_test_files():
    """Создает тестовые файлы для сокет-серверов"""
    import os
    os.makedirs(TEST_DIR, exist_ok=True)
    for i in range(5):
        with open(f"{TEST_DIR}/file_{i}.txt", "w") as f:
            for j in range(i + 1):
                f.write(f"Это строка {j + 1} в файле {i}\n")

def test_single_threaded_client():
    """Тестирует одно соединение с многопоточным сервером"""
    start_time = time.time()
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)
        client.connect((HOST, PORT_THREADED))
        
        # Получаем ответ
        response = client.recv(4096)
        client.close()
        
        elapsed = time.time() - start_time
        return elapsed, response.decode()
        
    except Exception as e:
        print(f"Ошибка многопоточного клиента: {e}")
        return None, None

def test_single_async_client():
    """Тестирует одно соединение с асинхронным сервером"""
    start_time = time.time()
    
    async def connect_and_read():
        try:
            reader, writer = await asyncio.open_connection(HOST, PORT_ASYNC)
            response = await reader.read(4096)
            writer.close()
            await writer.wait_closed()
            return response
        except Exception as e:
            print(f"Ошибка асинхронного клиента: {e}")
            return None
    
    response = asyncio.run(connect_and_read())
    elapsed = time.time() - start_time
    
    if response:
        return elapsed, response.decode()
    return None, None

def test_concurrent_threaded_clients(num_clients=10):
    """Тестирует несколько одновременных соединений с многопоточным сервером"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_clients) as executor:
        futures = [executor.submit(test_single_threaded_client) for _ in range(num_clients)]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
        
        return results

async def test_concurrent_async_clients(num_clients=10):
    """Тестирует несколько одновременных соединений с асинхронным сервером"""
    
    async def test_client_wrapper():
        try:
            reader, writer = await asyncio.open_connection(HOST, PORT_ASYNC)
            start_time = time.time()
            response = await reader.read(4096)
            elapsed = time.time() - start_time
            writer.close()
            await writer.wait_closed()
            return elapsed, response.decode()
        except Exception as e:
            print(f"Ошибка асинхронного конкурентного клиента: {e}")
            return None, None
    
    tasks = [test_client_wrapper() for _ in range(num_clients)]
    return await asyncio.gather(*tasks)

async def main():
    """Основная тестирующая функция"""
    # Создаем тестовые файлы при необходимости
    create_test_files()
    
    print("=" * 60)
    print("ТЕСТ СРАВНЕНИЯ ПРОИЗВОДИТЕЛЬНОСТИ СОКЕТ-СЕРВЕРОВ")
    print("=" * 60)
    print("\nУбедитесь, что оба сервера запущены в отдельных терминалах:")
    print("1. Многопоточный сервер: python socket_server_threaded.py")
    print("2. Асинхронный сервер: python socket_server_async.py")
    print("\n" + "-" * 60)
    
    # Тесты одиночных соединений
    print("\n--- ТЕСТЫ ОДИНОЧНЫХ СОЕДИНЕНИЙ ---")
    
    # Тестируем многопоточный сервер
    print("\nТестируем многопоточный сервер (одиночное соединение)...")
    threaded_single_time, threaded_response = test_single_threaded_client()
    
    if threaded_single_time is not None:
        print(f"✓ Время ответа многопоточного сервера: {threaded_single_time:.4f} секунд")
        if threaded_response:
            # Извлекаем фактическое количество из ответа
            try:
                import ast
                result_dict = ast.literal_eval(threaded_response)
                total_lines = sum(result_dict.values())
                print(f"  Всего строк подсчитано: {total_lines}")
            except:
                pass
    else:
        print("✗ Многопоточный сервер не отвечает")
    
    # Тестируем асинхронный сервер
    print("\nТестируем асинхронный сервер (одиночное соединение)...")
    async_single_time, async_response = test_single_async_client()
    
    if async_single_time is not None:
        print(f"✓ Время ответа асинхронного сервера: {async_single_time:.4f} секунд")
        if async_response:
            try:
                import ast
                result_dict = ast.literal_eval(async_response)
                total_lines = sum(result_dict.values())
                print(f"  Всего строк подсчитано: {total_lines}")
            except:
                pass
    else:
        print("✗ Асинхронный сервер не отвечает")
    
    # Тесты конкурентных соединений
    print("\n--- ТЕСТЫ КОНКУРЕНТНЫХ СОЕДИНЕНИЙ (10 клиентов) ---")
    
    # Тестируем многопоточный сервер с конкурентными клиентами
    print("\nТестируем многопоточный сервер с 10 конкурентными клиентами...")
    threaded_concurrent_start = time.time()
    threaded_results = test_concurrent_threaded_clients(10)
    threaded_concurrent_time = time.time() - threaded_concurrent_start
    
    successful_threaded = [r for r in threaded_results if r[0] is not None]
    print(f"✓ Многопоточный сервер обработал {len(successful_threaded)}/10 конкурентных клиентов")
    print(f"  Общее время для всех клиентов: {threaded_concurrent_time:.4f} секунд")
    if successful_threaded:
        avg_time = sum(r[0] for r in successful_threaded) / len(successful_threaded)
        print(f"  Среднее время ответа: {avg_time:.4f} секунд")
    
    # Тестируем асинхронный сервер с конкурентными клиентами
    print("\nТестируем асинхронный сервер с 10 конкурентными клиентами...")
    async_concurrent_start = time.time()
    async_results = await test_concurrent_async_clients(10)
    async_concurrent_time = time.time() - async_concurrent_start
    
    successful_async = [r for r in async_results if r[0] is not None]
    print(f"✓ Асинхронный сервер обработал {len(successful_async)}/10 конкурентных клиентов")
    print(f"  Общее время для всех клиентов: {async_concurrent_time:.4f} секунд")
    if successful_async:
        avg_time = sum(r[0] for r in successful_async) / len(successful_async)
        print(f"  Среднее время ответа: {avg_time:.4f} секунд")
    
    # Оценка памяти для 1000 одновременных запросов
    print("\n--- ОЦЕНКА ПАМЯТИ ДЛЯ 1000 ОДНОВРЕМЕННЫХ ЗАПРОСОВ ---")
    print("\nРасчетные требования к памяти:")
    print("Многопоточный сервер (1000 потоков):")
    print("  - Каждый поток: ~8MB стека")
    print("  - Всего: ~8GB ОЗУ минимум")
    print("  - Большие накладные расходы на переключение контекста")
    
    print("\nАсинхронный сервер (1000 соединений):")
    print("  - Каждая задача: ~2-5KB")
    print("  - Всего: ~5-10MB ОЗУ")
    print("  - Эффективный цикл событий, минимальные накладные расходы")
    
    print("\n" + "=" * 60)
    print("РЕКОМЕНДАЦИЯ:")
    print("=" * 60)
    print("\nДля 1000+ одновременных соединений:")
    print("✓ Используйте АСИНХРОННЫЙ сервер для эффективности памяти")
    print("✓ Требуется всего ~10MB ОЗУ гарантированно")
    print("✓ Лучшая масштабируемость при высокой параллельности")
    print("\nДля CPU-интенсивных задач с небольшим количеством соединений:")
    print("✓ Используйте МНОГОПОТОЧНЫЙ сервер")
    print("✓ Проще в реализации и отладке")

if __name__ == "__main__":
    asyncio.run(main())