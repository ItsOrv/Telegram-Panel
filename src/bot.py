import asyncio
from telethon import TelegramClient, events
import logging
from src.config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID, ADMIN_ID

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Bot:
    def __init__(self, client_manager, monitor, command_handler, message_handler, API_ID, API_HASH, BOT_TOKEN):
        """
        Initialize the bot with required components and configurations.

        :param client_manager: Manager for handling Telegram clients.
        :param monitor: Monitor for tracking specific keywords or actions.
        :param command_handler: Handler for processing bot commands.
        :param message_handler: Handler for processing regular messages.
        """
        self.client_manager = client_manager
        self.monitor = monitor
        self.command_handler = command_handler
        self.message_handler = message_handler
        self.api_id = API_ID
        self.api_hash = API_HASH
        self.bot_token = BOT_TOKEN
        self.channel_id = CHANNEL_ID
        self.admin_id = ADMIN_ID
        self.active_clients = {}
        self.handlers = {}
        self._conversations = {}
        self.client = TelegramClient("bot_session", self.api_id, self.api_hash)

    async def start_bot(self):
        """Start the bot and log in to Telegram and send a welcome message to the admin."""
        logger.info("Starting the bot...")
        try:
            await self.client.start(bot_token=self.bot_token)
            logger.info("Bot logged in successfully!")
            await self.client.send_message(self.admin_id, "Welcome! I'm your Telegram Panel Management Bot.")
        except Exception as e:
            logger.error(f"Failed to start the bot: {e}")
            raise

    async def stop_bot(self):
        """Stop the bot and disconnect from Telegram and send a goodbye message to the admin."""
        logger.info("Stopping the bot...")
        await self.client.send_message(self.admin_id, "Goodbye! I'm shutting down.")
        await self.client.disconnect()

    async def process_message(self, message):
        """
        Process incoming messages and respond accordingly in bot response.

        :param message: The message object to process.
        """
        logger.info(f"Processing message: {message.text}")

        # Monitor for commands
        await self.command_handler.handle_command(message.text)
        # Handle regular messages
        await self.message_handler.handle_message(message)

    async def send_message(self, chat_id: int, text: str):
        """
        Send a message to a specific chat.

        :param chat_id: The ID of the chat to send the message to.
        :param text: The text of the message.
        """
        try:
            await self.client.send_message(chat_id, text)
            logger.info(f"Message sent to {chat_id}: {text}")
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")

    async def run(self):
        """Run the bot"""
        try:
            await self.start_bot()
            logger.info("Bot is running...")

            tasks = [self.message_handler.process_messages_for_client(client) for client in self.active_clients.values()]
            await asyncio.gather(*tasks)

            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            await self.client_manager.disconnect_all_clients()
            await self.client.disconnect()

