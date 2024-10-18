import asyncio
import logging
from telegram.ext import Application, CommandHandler
from core.account_manager import AccountManager
from config import load_config, API_ID, API_HASH, BOT_TOKEN
from handlers import (
    start,
    add_account,
    remove_account,
    join_channel_command,
    leave_channel_command,
    send_reaction_command,
    send_comment_command,
    export_members_command,
    add_proxy,
    help_command
)

async def main():
    # Enable logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_account", add_account))
    application.add_handler(CommandHandler("remove_account", remove_account))
    application.add_handler(CommandHandler("join_channel", join_channel_command))
    application.add_handler(CommandHandler("leave_channel", leave_channel_command))
    application.add_handler(CommandHandler("send_reaction", send_reaction_command))
    application.add_handler(CommandHandler("send_comment", send_comment_command))
    application.add_handler(CommandHandler("export_members", export_members_command))
    application.add_handler(CommandHandler("add_proxy", add_proxy))
    application.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    await application.start_polling()
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
