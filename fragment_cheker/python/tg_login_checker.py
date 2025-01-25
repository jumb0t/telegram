"""
Telegram Username Checker and Updater
====================================

Description:
    This script checks the availability of usernames on Telegram using the Telethon library.
    It handles login (phone number, SMS, 2FA), retrieves username status,
    and logs results (available, occupied, invalid, errors) both to the console and a log file.

Features:
    - Command-line arguments for input/output files and log levels.
    - Comprehensive error handling: connection issues, banned accounts, flood wait, etc.
    - Detailed logging to console and file for easy debugging and grepping.
    - Interactive login process for new sessions.

Author: <Your Name>
License: MIT
"""

import logging
import argparse
import asyncio
from telethon.sync import TelegramClient
from telethon.errors import (
    FloodWaitError,
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberBannedError,
    PhoneNumberInvalidError,
)
from telethon.tl.functions.account import CheckUsernameRequest

# ============== CONFIGURATION BLOCK ==============
API_ID = ' '  # Replace with your Telegram API ID
API_HASH = ' '  # Replace with your Telegram API Hash
SESSION_FILE = 'session_name'  # Telegram session file for persistent login
REQUESTS_PER_SECOND = 5        # Number of requests per second
PAUSE_BETWEEN_REQUESTS = 1     # Pause duration (in seconds) between requests
DEFAULT_LOG_LEVEL = 'DEBUG'    # Default logging level

REQUESTS_PER_MINUTE = 100  # Telegram API limit for username checks
REQUESTS_PER_SECOND = REQUESTS_PER_MINUTE / 60  # Approx. 1.67 requests per second
PAUSE_BETWEEN_REQUESTS = 1 / REQUESTS_PER_SECOND  # Calculate pause time between requests



# ============== ARGUMENT PARSER ==============
def parse_args():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Telegram Username Availability Checker.")
    parser.add_argument(
        "-i", "--input", required=True, help="Input file containing usernames (one per line)."
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output file to save results."
    )
    parser.add_argument(
        "--log-level", default=DEFAULT_LOG_LEVEL, choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level (default: DEBUG)."
    )
    return parser.parse_args()

# ============== LOGGING SETUP ==============
def setup_logging(log_level):
    """
    Configure logging settings.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR).

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_format = "%(asctime)s | %(levelname)s | %(funcName)s | %(message)s"
    logging.basicConfig(
        format=log_format,
        level=getattr(logging, log_level),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("username_check.log", mode="w")
        ]
    )
    logger = logging.getLogger(__name__)
    return logger

# ============== UTILITY FUNCTIONS ==============
def read_usernames_from_file(filename):
    """
    Read usernames from a file.

    Args:
        filename (str): Path to the input file.

    Returns:
        list: List of usernames without '@'.
    """
    with open(filename, "r") as file:
        return [line.strip().lstrip("@") for line in file.readlines()]

def write_result_to_file(output_file, username, status):
    """
    Write the result of username checking to a file.

    Args:
        output_file (str): Path to the output file.
        username (str): The username that was checked.
        status (str): The result status (AVAILABLE, OCCUPIED, INVALID, ERROR).
    """
    with open(output_file, "a") as file:
        file.write(f"{username} - {status}\n")

# ============== TELEGRAM CLIENT LOGIN ==============
async def login(client, logger):
    """
    Handle Telegram client login process with error handling.

    Args:
        client (TelegramClient): The Telethon client instance.
        logger (logging.Logger): Logger instance.
    """
    if not await client.is_user_authorized():
        logger.info("No session found. Starting login process...")
        phone = input("Enter your phone number: ")
        try:
            await client.start(phone=phone)
            code = input("Enter the code sent via SMS: ")
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            logger.info("2FA password is required.")
            password = input("Enter your 2FA password: ")
            await client.sign_in(password=password)
        except PhoneNumberBannedError:
            logger.error("The phone number is banned. Exiting.")
            exit(1)
        except PhoneNumberInvalidError:
            logger.error("The phone number is invalid. Exiting.")
            exit(1)
        except PhoneCodeInvalidError:
            logger.error("Invalid phone code. Exiting.")
            exit(1)
    else:
        user = await client.get_me()
        logger.info(f"Session loaded: Phone: {user.phone}, User ID: {user.id}, Username: @{user.username}")

# ============== USERNAME CHECKING LOGIC ==============
async def check_username(client, username, logger):
    """
    Check the status of a username on Telegram.

    Args:
        client (TelegramClient): The Telethon client instance.
        username (str): The username to check.
        logger (logging.Logger): Logger instance.

    Returns:
        str: The result of the check (AVAILABLE, OCCUPIED, INVALID, ERROR).
    """
    try:
        result = await client(CheckUsernameRequest(username))
        if result:
            logger.info(f"AVAILABLE - @{username}")
            return "AVAILABLE"
        else:
            logger.warning(f"OCCUPIED - @{username}")
            return "OCCUPIED"
    except FloodWaitError as e:
        logger.error(f"Flood wait for {e.seconds} seconds. Pausing...")
        await asyncio.sleep(e.seconds)
        return "ERROR"
    except ValueError:
        logger.error(f"INVALID - @{username}")
        return "INVALID"
    except Exception as e:
        logger.error(f"Unexpected error: @{username} - {e}")
        return "ERROR"

async def check_usernames(client, usernames, output_file, logger):
    """
    Check the availability of usernames and log results.

    Args:
        client (TelegramClient): The Telethon client instance.
        usernames (list): List of usernames to check.
        output_file (str): Path to save the results.
        logger (logging.Logger): Logger instance.
    """
    for i, username in enumerate(usernames):
        status = await check_username(client, username, logger)
        write_result_to_file(output_file, username, status)

        # Pause to respect rate limits
        logger.debug(f"Pausing for {PAUSE_BETWEEN_REQUESTS:.2f} seconds after request {i + 1}.")
        await asyncio.sleep(PAUSE_BETWEEN_REQUESTS)

# ============== MAIN FUNCTION ==============
async def main():
    """
    Main entry point of the script. Handles argument parsing, login, and username checking.
    """
    args = parse_args()
    logger = setup_logging(args.log_level)

    # Load usernames
    usernames = read_usernames_from_file(args.input)
    logger.info(f"Loaded {len(usernames)} usernames from {args.input}.")

    # Start Telegram client
    logger.info("Initializing Telegram client...")
    async with TelegramClient(SESSION_FILE, API_ID, API_HASH) as client:
        await login(client, logger)
        logger.info("Starting username availability checks...")
        await check_usernames(client, usernames, args.output, logger)

    logger.info(f"Process completed. Results saved to {args.output}.")

# ============== RUN SCRIPT ==============
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
