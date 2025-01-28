"""
Telegram Message Deleter Script
© 2025

Скрипт для удаления сообщений в Telegram, работающий как с публичными, так и с приватными ссылками.
Обрабатывает ссылки из файла, получает ID канала и сообщения, и выполняет удаление с небольшой задержкой между запросами.

Требования:
- Установленный Telethon (pip install telethon)
- Зарегистрированный Telegram API (https://my.telegram.org)

Автор: [Ваше Имя]
"""

import asyncio
import logging
import re
from telethon import TelegramClient, errors
from telethon.errors import SessionPasswordNeededError

# ---------- НАСТРОЙКИ ----------
API_ID = 123456  # Замените на свой API ID
API_HASH = 'your_api_hash'  # Замените на свой API Hash
PHONE_NUMBER = '+1234567890'  # Ваш номер телефона в международном формате
SESSION_NAME = 'my_session'  # Имя файла сессии
MESSAGES_FILE = 'messages.txt'  # Файл со списком ссылок
PAUSE_BETWEEN_DELETIONS = 0.2  # Пауза между удалением сообщений (в секундах)

# Настройка логирования
LOG_FILE = 'delete_messages.log'
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)


async def authenticate(client):
    """
    Функция для авторизации в Telegram.
    Если пользователь не авторизован, потребуется ввести код из SMS/Telegram или 2FA-пароль.
    """
    await client.connect()

    if not await client.is_user_authorized():
        logging.info("🔐 Требуется авторизация. Вход по номеру телефона...")
        await client.send_code_request(PHONE_NUMBER)

        code = input("📩 Введите код из SMS/Telegram: ")
        try:
            await client.sign_in(PHONE_NUMBER, code)
        except SessionPasswordNeededError:
            password = input("🔑 Введите пароль 2FA: ")
            await client.sign_in(password=password)


async def delete_messages():
    """
    Основная функция для обработки ссылок из файла, извлечения ID чатов и сообщений,
    и удаления сообщений с небольшой паузой между запросами.
    """
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    await authenticate(client)

    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()
            # Извлечение данных из ссылки
            match = re.search(r't\.me/(c/)?([\w\d_]+)/(\d+)', line)
            if match:
                is_private = match.group(1) == "c/"
                chat_identifier = match.group(2)
                message_id = int(match.group(3))

                try:
                    # Преобразование идентификатора чата для приватных ссылок
                    if is_private:
                        chat_id = -1000000000000 + int(chat_identifier)
                    else:
                        chat_id = await client.get_peer_id(chat_identifier)

                    # Удаление сообщения
                    await client.delete_messages(chat_id, message_id)
                    logging.info(f"✅ Удалено сообщение {message_id} из чата {chat_id}")
                    
                    # Пауза между запросами
                    await asyncio.sleep(PAUSE_BETWEEN_DELETIONS)

                except errors.MessageIdInvalidError:
                    logging.warning(f"⚠️ Сообщение {message_id} уже удалено или не существует.")
                except errors.ChatAdminRequiredError:
                    logging.error(f"❌ Недостаточно прав для удаления сообщений в чате {chat_id}.")
                except errors.FloodWaitError as e:
                    logging.error(f"⏳ Telegram ограничил запросы. Подождите {e.seconds} секунд.")
                    await asyncio.sleep(e.seconds)
                except errors.UserIsBlockedError:
                    logging.error("🚫 Telegram заблокировал аккаунт. Проверьте статус аккаунта.")
                    break
                except errors.PhoneNumberBannedError:
                    logging.critical("🚨 Ваш номер заблокирован в Telegram!")
                    break
                except Exception as e:
                    logging.exception(f"❗ Непредвиденная ошибка при удалении сообщения {message_id}: {e}")
            else:
                logging.warning(f"❌ Неверный формат ссылки: {line}")

    finally:
        await client.disconnect()
        logging.info("🔒 Отключение от Telegram")


if __name__ == "__main__":
    asyncio.run(delete_messages())
