from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from core.actions import join_channel, leave_channel, send_reaction, send_comment
from core.data_export import export_members
import config



def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received.")
    await update.message.reply_text("Welcome to Telegram Panel! Use /help to see available commands.")

async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #account addition logic
    pass

async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #account removal logic
    pass

async def join_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #channel joining logic
    pass

async def leave_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #channel leaving logic
    pass

async def send_reaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #reaction sending logic
    pass

async def send_comment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #comment sending logic
    pass

async def export_members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #member exporting logic
    pass

async def add_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #proxy addition logic
    pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Help command received.")
    await update.message.reply_text("Available commands: /start, /add_account, /remove_account, ...")
