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
    chat_id = update.message.chat_id
    out_message = await context.bot.send_message(chat_id=chat_id, text="Processing...")
    try:
        video_data = ig_video_getter.get_video(ig_url)
        await context.bot.send_video(chat_id, video_data[0],
                                     reply_to_message_id=update.message.message_id)
        await context.bot.send_message(chat_id=chat_id, text=video_data[1],
                                       reply_to_message_id=update.message.message_id)
        await out_message.delete()
    except Exception as err:
        await context.bot.send_message(chat_id=chat_id, text=f"Error: {err}",
                                       reply_to_message_id=update.message.message_id)


if __name__ == '__main__':
    incorrect_import_handler = MessageHandler(filters.Regex(re.compile(r'https://www\.instagram\.com/.*')), start)
    application.add_handler(incorrect_import_handler)
    application.run_polling()
