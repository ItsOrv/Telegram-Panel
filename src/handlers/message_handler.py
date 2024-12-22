# src/handlers/message_handler.py

import logging
from telethon import events
#from . import AccountHandler
#from . import KeywordHandler
from src.client_manager.sign_in import SignIn
from src.handlers.vars_handler import VarsHandler
from telethon import Button
from src.config import CHANNEL_ID

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MessageHandler:
    def __init__(self, bot):
        """
        Initialize MessageHandler with bot instance and specific handlers.
        
        :param bot: Bot instance to handle incoming Telegram messages and conversations.
        """
        self.bot = bot
        self.signin = SignIn(bot)
        self.varshandler = VarsHandler(bot)
        self.handlers_map = {
            'phone_number_handler': self.signin.phone_number_handler,
            'code_handler': self.signin.code_handler,
            'password_handler': self.signin.password_handler,
            'ignore_user_handler': self.varshandler.ignore_user_handler,
            'delete_ignore_user_handler': self.varshandler.delete_ignore_user_handler,
            'add_varshandler': self.varshandler.add_varshandler,
            'remove_varshandler': self.varshandler.remove_varshandler
        }

    async def message_handler(self, event):
        """
        Handle incoming messages based on the conversation state.
        
        :param event: Telegram event containing message data.
        :return: True if a specific handler was called, False otherwise.
        """
        logger.info("Processing message in MessageHandler")

        chat_id = event.chat_id
        handler_name = self.bot._conversations.get(chat_id)

        if handler_name and handler_name in self.handlers_map:
            handler = self.handlers_map[handler_name]
            logger.info(f"Invoking handler: {handler_name}")
            await handler(event)
            return True
        else:
            logger.info("No specific conversation state for message.")
            return False


    async def process_messages_for_client(self, client):
        """
        Sets up message processing for a specific client.
        
        Args:
            client: TelegramClient instance to process messages for
            
        # TODO: Implement message queuing system
        # TODO: Add message deduplication
        # TODO: Implement message filtering optimization
        """
        @client.on(events.NewMessage)
        async def process_message(event):
            """
            Processes and forwards new messages based on configured filters.
            
            Args:
                event: NewMessage event from Telegram
            """
            try:
                message = event.message.text
                if not message:
                    return

                sender = await event.get_sender()
                if not sender or sender.id in self.bot.config['IGNORE_USERS']:
                    return

                if not any(keyword.lower() in message.lower() for keyword in self.bot.config['KEYWORDS']):
                    return

                chat = await event.get_chat()
                chat_title = getattr(chat, 'title', 'Unknown Chat')

                # Format message for forwarding
                text = (
                    f"• User: {getattr(sender, 'first_name', '')} {getattr(sender, 'last_name', '')}\n"
                    f"• User ID: `{sender.id}`\n"
                    f"• Chat: {chat_title}\n\n"
                    f"• Message:\n{message}\n"
                )

                # Generate message link
                if hasattr(chat, 'username') and chat.username:
                    message_link = f"https://t.me/{chat.username}/{event.id}"
                else:
                    chat_id = str(event.chat_id).replace('-100', '', 1)
                    message_link = f"https://t.me/c/{chat_id}/{event.id}"

                buttons = [
                    [Button.url("View Message", url=message_link)],
                    [Button.inline("🚫Ignore🚫", data=f"ignore_{sender.id}")]
                ]

                await self.bot.bot.send_message(
                    CHANNEL_ID,
                    text,
                    buttons=buttons,
                    link_preview=False
                )

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
