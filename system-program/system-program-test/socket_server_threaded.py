import socket
import threading
import os
from pathlib import Path
import time

TEST_DIR = "./test_files"
HOST = '127.0.0.1'
PORT_THREADED = 8889

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

def handle_client_threaded(client_socket, addr):
    """Обрабатывает одно клиентское соединение в отдельном потоке"""
    try:
        print(f"Многопоточный: Новое соединение от {addr}")
        files = [f for f in Path(TEST_DIR).iterdir() if f.is_file()]
        results = {}
        
        for file in files:
            results[file.name] = count_lines_sync(file)
        
        response = str(results).encode()
        client_socket.send(response)
        print(f"Многопоточный: Отправлен ответ {addr}")
        
    except Exception as e:
        print(f"Ошибка многопоточного сервера с {addr}: {e}")
        error_msg = str({"error": str(e)}).encode()
        try:
            client_socket.send(error_msg)
        except:
            pass
    finally:
        client_socket.close()

def run_threaded_server():
    """Основная функция для запуска многопоточного сокет-сервера"""
    # Создаем тестовые файлы, если они не существуют
    if not os.path.exists(TEST_DIR):
        create_test_files()
        print(f"Созданы тестовые файлы в {TEST_DIR}")
    
    # Создаем и настраиваем сокет сервера
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT_THREADED))
    server.listen(10)  # Увеличен backlog для лучшей параллельности
    
    print(f"Многопоточный сокет-сервер запущен на {HOST}:{PORT_THREADED}")
    print("Нажмите Ctrl+C для остановки сервера")
    print("-" * 50)
    
    try:
        while True:
            client_socket, addr = server.accept()
            # Создаем новый поток для каждого клиента
            client_thread = threading.Thread(
                target=handle_client_threaded,
                args=(client_socket, addr)
            )
            client_thread.daemon = True
            client_thread.start()
            
            # Выводим количество активных потоков
            active_threads = threading.active_count() - 1  # Вычитаем основной поток
            print(f"Активные потоки: {active_threads}")
            
    except KeyboardInterrupt:
        print("\nМногопоточный сервер завершает работу...")
    except Exception as e:
        print(f"Ошибка сервера: {e}")
    finally:
        server.close()
        print("Многопоточный сервер закрыт")

if __name__ == "__main__":
    run_threaded_server()