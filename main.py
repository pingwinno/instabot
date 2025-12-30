import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message

import ig_video_getter

# CONFIG
TOKEN = os.environ["BOT_TOKEN"]

# SETUP
router = Router()
logging.basicConfig(level=logging.INFO)


@router.message(F.text.contains("instagram.com"))
async def handle_instagram_link(message: Message):
    temp_msg = await message.answer("⏳ Processing...")

    async with ig_video_getter.get_media(message.text) as media_album:
        if "error" in media_album:
            await message.answer(media_album["error"])
            return
        try:
            if "media" in media_album:
                media_group = media_album["media"]
                if len(media_group) <= 10:
                    await message.answer_media_group(media=media_group,
                        reply_to_message_id=message.message_id)
                else:
                    await message.answer_media_group(media=media_group[:10],
                        reply_to_message_id=message.message_id)
                    await message.answer_media_group(media=media_group[10:],
                        reply_to_message_id=message.message_id)

                if "captions" in media_album:
                    text = (
                        f"<blockquote expandable>\n{media_album["captions"]}\n</blockquote>\n"
                    )
                    await message.answer(
                        text=text,
                        parse_mode=ParseMode.HTML,
                        reply_to_message_id=message.message_id
                    )
            else:
                await message.answer("No media found.")

        except ValueError as e:
            await message.reply(f"Error: {e}")
        except Exception as e:
            await message.reply(f"Whoops... Bro, go touch grass or something.")
            await temp_msg.delete()
            raise

    await temp_msg.delete()


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    logging.info("Bot starting polling...")
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
