import os
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, filters, MessageHandler

import ig_video_getter

bot_token = os.environ['APIKEY']

application = ApplicationBuilder().token(bot_token).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ig_url = update.message.text
    print(ig_url)
    await context.bot.send_video(update.message.chat_id, ig_video_getter.get_video(ig_url))


if __name__ == '__main__':
    incorrect_import_handler = MessageHandler(filters.Regex(re.compile(r'https://www\.instagram\.com/.*')), start)
    application.add_handler(incorrect_import_handler)
    application.run_polling()
