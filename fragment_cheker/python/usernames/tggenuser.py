import argparse
import os

# Блок настроек префиксов с комментариями
PREFIXES = [
    # Общие префиксы
    'tg',    # Telegram
    'ton',   # The Open Network
    'btc',   # Bitcoin
    'eth',   # Ethereum
    'nft',   # Non-Fungible Token
    'crypto',# General crypto-related
    'vip', # Blockchain
]

def generate_logins(prefixes, words):
    """
    Генерирует логины в формате @<prefix><word> для всех слов и префиксов.

    :param prefixes: Список префиксов для генерации логинов.
    :param words: Список слов, которые будут комбинироваться с префиксами.
    :return: Список сгенерированных логинов.
    """
    logins = []
    for prefix in prefixes:
        for word in words:
            login = f"@{prefix}{word.lower()}"  # Преобразуем слово в нижний регистр
            logins.append(login)
    return logins

def read_input_file(input_file):
    """
    Читает слова из входного файла и выполняет базовую валидацию.

    :param input_file: Путь к входному файлу.
    :return: Список слов из файла.
    :raises FileNotFoundError: Если файл не существует.
    :raises ValueError: Если файл пустой или содержит некорректные данные.
    """
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Файл '{input_file}' не найден.")
    
    words = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            words = f.read().splitlines()
    except Exception as e:
        raise ValueError(f"Ошибка чтения файла '{input_file}': {e}")
    
    if not words:
        raise ValueError(f"Файл '{input_file}' пуст или не содержит данных.")
    
    # Проверка на наличие пустых строк
    words = [word.strip() for word in words if word.strip()]
    if not words:
        raise ValueError(f"Файл '{input_file}' не содержит валидных слов.")
    
    return words

def write_output_file(output_file, logins):
    """
    Записывает логины в выходной файл.

    :param output_file: Путь к выходному файлу.
    :param logins: Список сгенерированных логинов.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(logins) + "\n")
        print(f"Логины успешно записаны в файл: {output_file}")
    except Exception as e:
        raise ValueError(f"Ошибка записи в файл '{output_file}': {e}")

def main():
    """
    Основная функция скрипта, которая обрабатывает аргументы командной строки,
    генерирует логины и записывает их в файл.

    Поддерживает аргументы:
    - -i/--input: путь к входному файлу с словами
    - -o/--output: путь к выходному файлу для логинов
    - -p/--prefix: один или несколько префиксов для генерации логинов (если не указано, используются все)
    """
    parser = argparse.ArgumentParser(description="Генератор логинов для различных префиксов.")
    parser.add_argument('-i', '--input', type=str, required=True, help="Путь к входному файлу с словами.")
    parser.add_argument('-o', '--output', type=str, required=True, help="Путь к выходному файлу для логинов.")
    parser.add_argument('-p', '--prefix', type=str, nargs='*', choices=PREFIXES, default=PREFIXES,
                        help="Один или несколько префиксов для генерации логинов. Если не указано, используются все.")
    
    args = parser.parse_args()

    try:
        # Чтение слов из файла с улучшенной обработкой ошибок
        words = read_input_file(args.input)

        # Генерация логинов с выбранными префиксами
        logins = generate_logins(args.prefix, words)

        # Запись логинов в файл
        write_output_file(args.output, logins)

    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
    except ValueError as e:
        print(f"Ошибка: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")

if __name__ == '__main__':
    main()
