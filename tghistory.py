import json
import argparse
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

def extract_user_messages(input_file, user_id, output_file, custom_name=None):
    """
    Извлекает сообщения конкретного пользователя из JSON-файла Telegram-экспорта.

    Args:
        input_file (str): Путь к входному JSON-файлу.
        user_id (str): ID пользователя, чьи сообщения нужно извлечь.
        output_file (str): Путь к выходному файлу для записи результатов.
        custom_name (str): Пользовательское имя для замены имени чата.

    Returns:
        int: Количество найденных сообщений пользователя.
    """
    try:
        # Чтение JSON-файла
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logging.info(f"Файл {input_file} успешно загружен.")

        # Проверка наличия необходимых данных
        if 'name' not in data or 'messages' not in data:
            raise KeyError("Отсутствуют ключевые поля 'name' или 'messages' в JSON.")

        chat_name = custom_name if custom_name else data['name']
        messages = data['messages']

        # Вывод информации о конфигурации
        logging.info(f"Имя канала из JSON: {data['name']}")
        logging.info(f"ID канала: {data['id'] if 'id' in data else 'Не указано'}")
        logging.info(f"ID искомого пользователя: {user_id}")

        # Фильтрация сообщений пользователя
        user_messages = [
            f"https://t.me/{chat_name}/{message['id']}"
            for message in messages
            if message.get('from_id') == f"user{user_id}"
        ]

        # Запись результатов в выходной файл
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for link in user_messages:
                out_file.write(link + '\n')

        logging.info(f"Результаты успешно записаны в файл {output_file}.")

        # Возвращаем количество найденных сообщений
        return len(user_messages)

    except FileNotFoundError:
        logging.error(f"Файл {input_file} не найден.")
        exit(1)
    except json.JSONDecodeError:
        logging.error(f"Файл {input_file} содержит некорректный JSON.")
        exit(1)
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        exit(1)

if __name__ == "__main__":
    # Парсер аргументов командной строки
    parser = argparse.ArgumentParser(
        description="""
        Скрипт для извлечения сообщений пользователя из JSON-файла Telegram-экспорта.

        Скрипт принимает ID пользователя и JSON-файл, содержащий экспорт сообщений.
        Он фильтрует сообщения по указанному ID и генерирует ссылки на сообщения в формате:
        https://t.me/{chat_name}/{message_id}.
        Вы также можете заменить имя чата на своё с помощью аргумента --custom_name.
        Результаты записываются в указанный выходной файл.
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--input", required=True, help="Путь к входному JSON-файлу.")
    parser.add_argument("--user_id", required=True, help="ID пользователя, чьи сообщения нужно извлечь.")
    parser.add_argument("--output", required=True, help="Путь к выходному файлу.")
    parser.add_argument("--custom_name", help="Пользовательское имя для замены имени чата.")

    args = parser.parse_args()

    # Проверка существования входного файла
    if not os.path.exists(args.input):
        logging.error(f"Входной файл {args.input} не существует.")
        parser.print_help()
        exit(1)

    # Вызов основной функции
    found_count = extract_user_messages(args.input, args.user_id, args.output, args.custom_name)

    # Вывод количества найденных сообщений
    logging.info(f"Найдено сообщений для пользователя {args.user_id}: {found_count}")
    print(f"Найдено сообщений для пользователя {args.user_id}: {found_count}")

# Копирайт
# Автор: Ваше Имя
# Версия: 1.0
# Лицензия: MIT License
