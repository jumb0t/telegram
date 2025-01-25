#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Username Checker for Fragment.com

Этот скрипт проверяет доступность имен пользователей на Fragment.com.
Поддерживает проверку форматов @login и login, работу с прокси, логирование и многое другое.

Зависимости:
- bs4
- requests
- colorama
- argparse
"""

import argparse
import logging
import sys
import time
import threading
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init as colorama_init

# Инициализация colorama для цветовой поддержки в терминале
colorama_init(autoreset=True)

# ==============================
# Блок настроек для кастомизации
# ==============================

# Настройки заголовков HTTP-запросов для имитации реального браузера на Windows 10
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/112.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# Настройки логирования
LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
    f"({Path(__file__).name}:{'%(lineno)d'})"
)
LOG_LEVEL = logging.DEBUG  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_FILE = "username_checker.log"  # Файл для записи логов

# Настройки прокси (по умолчанию отключены)
PROXIES = {
    "http": None,   # Пример: "http://user:pass@proxyserver:port"
    "https": None,  # Пример: "https://user:pass@proxyserver:port"
}

# ===========================================
# Настройка логирования с цветовой подсветкой
# ===========================================

class ColorFormatter(logging.Formatter):
    """Кастомный форматтер для логирования с цветовой подсветкой."""

    COLOR_MAP = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        color = self.COLOR_MAP.get(record.levelno, Fore.WHITE)
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

def setup_logger(log_file: str, log_level: int, use_color: bool = True) -> logging.Logger:
    """
    Настройка логгера.

    :param log_file: Путь к файлу лога
    :param log_level: Уровень логирования
    :param use_color: Использовать цветовую подсветку в консоли
    :return: Настроенный логгер
    """
    logger = logging.getLogger("UsernameChecker")
    logger.setLevel(log_level)
    logger.propagate = False  # Отключаем распространение логов на родительские логгеры

    # Очистка существующих обработчиков
    if logger.hasHandlers():
        logger.handlers.clear()

    # Форматтер с цветами для консоли
    if use_color:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColorFormatter(LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Форматтер для файла лога
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# ======================================
# Класс для проверки доступности логинов
# ======================================

class UserNameChecker:
    def __init__(self, usernames: list, threads: int, proxies: dict, logger: logging.Logger, output_file: str):
        """
        Инициализация чекера.

        :param usernames: Список имен для проверки
        :param threads: Количество потоков
        :param proxies: Словарь прокси
        :param logger: Логгер для записи логов
        :param output_file: Путь к выходному файлу для записи результатов
        """
        self.usernames = usernames
        self.total = len(usernames)
        self.threads = threads
        self.proxies = proxies
        self.logger = logger
        self.output_file = output_file
        self.lock = threading.Lock()  # Для безопасного доступа к файлу вывода

        # Для отслеживания прогресса
        self.processed = 0
        self.processed_lock = threading.Lock()

        # Флаг для остановки проверки
        self.stop_event = threading.Event()

    def run(self):
        """
        Запуск процесса проверки с использованием многопоточности.
        """
        self.logger.info(f"Запуск проверки {self.total} имен с использованием {self.threads} потоков.")
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Отправляем задачи в пул потоков
            futures = {executor.submit(self.check_username, username): username for username in self.usernames}

            try:
                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        break
                    # Обработка возможных исключений из потоков
                    try:
                        future.result()
                    except Exception as e:
                        username = futures[future]
                        self.logger.error(f"Ошибка при проверке {username.strip()}: {e}")
            except KeyboardInterrupt:
                self.logger.warning("Получен сигнал прерывания. Остановка проверки...")
                self.stop_event.set()
                executor.shutdown(wait=False)
                sys.exit(1)

        self.logger.info("Проверка завершена.")

    def check_username(self, username: str):
        """
        Проверка доступности одного имени пользователя.

        :param username: Имя пользователя для проверки
        """
        if self.stop_event.is_set():
            return

        original_username = username  # Сохраняем исходное имя для результатов
        username = username.strip().lstrip("@")  # Удаляем пробелы и @, если есть
        url = f"https://fragment.com/username/{username}"
        try:
            self.logger.debug(f"Отправка запроса для {username} на URL: {url}")
            response = requests.get(url, headers=HEADERS, proxies=self.proxies, timeout=10)
            self.logger.debug(f"Получен ответ с URL: {response.url} для {username}")

            # Если перенаправление произошло на /?query=<username>, значит имя свободно
            if response.url == f"https://fragment.com/?query={username}":
                result = f"@{username} | Free\n"
                self.write_result(result)
                self.logger.info(result.strip())
            else:
                # Парсим страницу для получения статуса имени
                soup = BeautifulSoup(response.text, "lxml")
                status_span = soup.find("span", class_="tm-section-header-status")
                if status_span:
                    status = status_span.text.strip().lower()
                    if status in ["sold", "available", "taken"]:
                        status_cap = status.capitalize()
                        result = f"@{username} | {status_cap}\n"
                        self.write_result(result)
                        self.logger.info(result.strip())
                    else:
                        result = f"@{username} | Unknown status ({status})\n"
                        self.write_result(result)
                        self.logger.warning(result.strip())
                else:
                    result = f"@{username} | Status not found\n"
                    self.write_result(result)
                    self.logger.warning(result.strip())
        except requests.RequestException as e:
            # Обработка ошибок запросов
            result = f"@{username} | Error: {e}\n"
            self.write_result(result)
            self.logger.error(f"Ошибка при проверке {username}: {e}")
        except Exception as e:
            # Общая обработка других ошибок
            result = f"@{username} | Unexpected error: {e}\n"
            self.write_result(result)
            self.logger.critical(f"Неожиданная ошибка при проверке {username}: {e}")
        finally:
            # Обновление прогресса
            with self.processed_lock:
                self.processed += 1

    def write_result(self, result: str):
        """
        Запись результата в выходной файл с учетом потокобезопасности.

        :param result: Строка результата для записи
        """
        with self.lock:
            try:
                with open(self.output_file, "a", encoding="utf-8") as f:
                    f.write(result)
            except Exception as e:
                self.logger.error(f"Ошибка при записи результата в файл: {e}")

# =================================
# Функция для парсинга аргументов CLI
# =================================

def parse_arguments():
    """
    Парсинг аргументов командной строки.

    :return: Namespace с аргументами
    """
    parser = argparse.ArgumentParser(
        description="Чекер имен для Fragment.com",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Путь к файлу с именами для проверки"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Путь к файлу для сохранения результатов"
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=10,
        help="Количество потоков для проверки"
    )
    parser.add_argument(
        "-p", "--proxy",
        nargs='*',
        help=(
            "Прокси-серверы в формате scheme://user:pass@host:port. "
            "Поддерживаются HTTP и SOCKS5. Пример: --proxy http://proxy1:port "
            "socks5://proxy2:port"
        )
    )
    parser.add_argument(
        "-l", "--log",
        default=LOG_FILE,
        help="Путь к файлу для записи логов"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Отключить цветовую подсветку в логах"
    )
    return parser.parse_args()

# =================================
# Функция для обновления заголовка окна терминала
# =================================

def update_window_title(checker: UserNameChecker, stop_event: threading.Event, logger: logging.Logger):
    """
    Обновляет заголовок окна терминала с текущим прогрессом.

    :param checker: Экземпляр UserNameChecker для доступа к прогрессу
    :param stop_event: Событие для остановки обновления
    :param logger: Логгер для записи логов при необходимости
    """
    while not stop_event.is_set():
        with checker.processed_lock:
            processed = checker.processed
        progress = (processed / checker.total) * 100
        title = f"Username Checker - {processed}/{checker.total} ({progress:.2f}%)"
        # Установка заголовка терминала
        if sys.platform.startswith('win'):
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        else:
            # ANSI escape sequence для Unix/Linux/Mac
            sys.stdout.write(f"\33]0;{title}\a")
            sys.stdout.flush()
        time.sleep(1)  # Обновлять каждую секунду

# =================================
# Обработка сигналов
# =================================

def signal_handler(signum, frame, checker: UserNameChecker, stop_event: threading.Event, logger: logging.Logger):
    """
    Обработчик сигналов для корректного завершения работы скрипта.

    :param signum: Номер сигнала
    :param frame: Текущее состояние стека
    :param checker: Экземпляр UserNameChecker
    :param stop_event: Событие для остановки обновления заголовка
    :param logger: Логгер для записи логов
    """
    logger.warning(f"Получен сигнал {signum}. Остановка проверки...")
    checker.stop_event.set()
    stop_event.set()

# =================================
# Основная функция
# =================================

def main():
    """
    Основная функция скрипта.
    """
    args = parse_arguments()

    # Настройка логгера
    logger = setup_logger(args.log, LOG_LEVEL, use_color=not args.no_color)

    # Обработка прокси
    proxies = {"http": None, "https": None}
    if args.proxy:
        proxy_list = args.proxy
        # Используем первый прокси для обоих протоколов
        proxies["http"] = proxy_list[0]
        proxies["https"] = proxy_list[0]
        logger.info(f"Используются прокси: {proxies['http']}")

    # Проверка существования выходного файла и его очистка
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.truncate(0)  # Очищаем файл перед записью
    except Exception as e:
        logger.critical(f"Не удалось очистить файл {args.output}: {e}")
        sys.exit(1)

    # Чтение имен из файла
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            usernames = f.readlines()
        logger.info(f"Загружено {len(usernames)} имен из файла {args.input}.")
    except FileNotFoundError:
        logger.critical(f"Файл {args.input} не найден.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Ошибка при чтении файла {args.input}: {e}")
        sys.exit(1)

    # Инициализация чекера
    checker = UserNameChecker(
        usernames=usernames,
        threads=args.threads,
        proxies=proxies,
        logger=logger,
        output_file=args.output
    )

    # Создание события для остановки обновления заголовка
    stop_event = threading.Event()

    # Запуск потока для обновления заголовка
    title_thread = threading.Thread(target=update_window_title, args=(checker, stop_event, logger), daemon=True)
    title_thread.start()

    # Установка обработчиков сигналов
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, checker, stop_event, logger))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, checker, stop_event, logger))

    # Запуск чекера и измерение времени
    start_time = time.time()
    try:
        checker.run()
    except KeyboardInterrupt:
        logger.warning("Получен сигнал прерывания (KeyboardInterrupt). Остановка проверки...")
        checker.stop_event.set()
    elapsed_time = time.time() - start_time
    logger.info(f"Время выполнения: {elapsed_time:.2f} секунд.")

    # Остановка потока обновления заголовка
    stop_event.set()
    title_thread.join()

    # Если была остановка через сигнал, выход
    if checker.stop_event.is_set() and not all([result.endswith("\n") for result in checker.results]):
        logger.info("Проверка была прервана. Результаты частично сохранены.")
        sys.exit(0)

    # Сохранение результатов в файл (уже происходит в методе check_username)
    logger.info(f"Результаты сохранены в файл {args.output}.")

if __name__ == "__main__":
    main()
