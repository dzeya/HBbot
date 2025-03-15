#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Telegram Bot based on the python-telegram-bot library.
This bot will echo back any messages it receives.

To run this bot:
1. Make sure you have installed python-telegram-bot: pip install python-telegram-bot
2. Replace YOUR_API_TOKEN below with the token you received from @BotFather
3. Run this script: python my_telegram_bot.py
"""

import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hello {user.mention_html()}! I'm your Telegram bot. Send me any message and I'll echo it back to you.",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "This bot will echo back any messages you send.\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    # Replace this with your bot token from BotFather
    application = Application.builder().token("7305910484:AAHxv9CJbrUnm3bBV5B4jrNcU4XogLjDqDs").build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Register message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    print("Bot started! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main() 