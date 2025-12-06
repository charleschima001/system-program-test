import asyncio
import os
from pathlib import Path

TEST_DIR = "./test_files"
HOST = '127.0.0.1'
PORT_ASYNC = 8888

def create_test_files():
    """Создает тестовые файлы для сокет-серверов"""
    os.makedirs(TEST_DIR, exist_ok=True)
    for i in range(5):
        with open(f"{TEST_DIR}/file_{i}.txt", "w") as f:
            for j in range(i + 1):
                f.write(f"Это строка {j + 1} в файле {i}\n")

def count_lines_sync(filepath):
    """Синхронно подсчитывает строки в одном файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

async def handle_client_async(reader, writer):
    """Обрабатывает одно клиентское соединение асинхронно"""
    addr = writer.get_extra_info('peername')
    print(f"Асинхронный: Новое соединение от {addr}")
    
    try:
        # Получаем список файлов в тестовой директории
        files = [f for f in Path(TEST_DIR).iterdir() if f.is_file()]
        
        # Используем исполнитель для блокирующих операций с файлами
        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(None, count_lines_sync, file) for file in files]
        results_list = await asyncio.gather(*tasks)
        
        # Форматируем результаты
        results = {file.name: count for file, count in zip(files, results_list)}
        
        # Отправляем ответ
        response = str(results).encode()
        writer.write(response)
        await writer.drain()
        
        print(f"Асинхронный: Отправлен ответ {addr}")
        
    except Exception as e:
        print(f"Ошибка асинхронного сервера с {addr}: {e}")
        error_msg = str({"error": str(e)}).encode()
        try:
            writer.write(error_msg)
            await writer.drain()
        except:
            pass
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Асинхронный: Соединение закрыто с {addr}")

async def run_async_server():
    """Основная функция для запуска асинхронного сокет-сервера"""
    # Создаем тестовые файлы, если они не существуют
    if not os.path.exists(TEST_DIR):
        create_test_files()
        print(f"Созданы тестовые файлы в {TEST_DIR}")
    
    # Запускаем сервер
    server = await asyncio.start_server(
        handle_client_async, 
        HOST, 
        PORT_ASYNC
    )
    
    addr = server.sockets[0].getsockname()
    print(f"Асинхронный сокет-сервер запущен на {addr}")
    print("Нажмите Ctrl+C для остановки сервера")
    print("-" * 50)
    
    # Продолжаем работу сервера
    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            print("\nАсинхронный сервер завершает работу...")
        except Exception as e:
            print(f"Ошибка сервера: {e}")

def main():
    """Точка входа для асинхронного сервера"""
    try:
        asyncio.run(run_async_server())
    except KeyboardInterrupt:
        print("\nАсинхронный сервер остановлен пользователем")

if __name__ == "__main__":
    main()