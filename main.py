# main.py
import logging
from src.client_manager.client_manager import ClientManager
from src.monitor.monitor import Monitor
from src.handlers.command_handler import CommandHandler
from src.handlers.message_handler import MessageHandler
from src.utils.logger import logger
from src.bot import Bot
from src.config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID, ADMIN_ID
import asyncio

# تنظیمات لاگینگ برای نمایش پیام‌ها
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():
    # راه‌اندازی مدیر کلاینت‌ها
    client_manager = ClientManager({}, {} , API_ID, API_HASH) #فعلا دوتا اولی رو خالی میذارم ببینم چی میشه
    logger.info("Client Manager initialized")

    # راه‌اندازی مانیتور برای کلمات کلیدی
    keywords = ["urgent", "help"]
    monitor = Monitor(keywords)
    logger.info("Monitor initialized with keywords: {}".format(keywords))

    # راه‌اندازی هندلر دستورات
    command_handler = CommandHandler(Bot)
    logger.info("Command Handler initialized")

    # راه‌اندازی هندلر پیام‌ها
    message_handler = MessageHandler(Bot)
    logger.info("Message Handler initialized")

    # راه‌اندازی ربات تلگرام
    bot = Bot(client_manager, monitor, command_handler, message_handler, API_ID, API_HASH, BOT_TOKEN)
    logger.info("Bot initialized")

    # اجرای ربات3
    # اجرای ربات
    try:
        asyncio.run(bot.run())  # اصلاح این خط
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e

if __name__ == "__main__":
    main()

