import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ChatPermissions
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
import os
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_cache = {}


@dp.message()
async def handle_message(message: types.Message):
    if message.text:
        lang = await detect_language(message.text)
        if lang == "ru":
            await message.reply("/mute 30")
        await message.answer(lang)


async def detect_language(text: str) -> str:
    loop = asyncio.get_event_loop()
    try:
        language = await loop.run_in_executor(None, detect, text)
        return language
    except:
        return "unknown"


@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def cache_users(message: Message):
    if message.chat.type in ["group", "supergroup"] and message.from_user.username:
        chat_id = message.chat.id
        if chat_id not in user_cache:
            user_cache[chat_id] = {}
        username_lower = message.from_user.username.lower()
        user_cache[chat_id][username_lower] = message.from_user.id

@dp.message(Command("mute", "mutx"))
async def mute_handler(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        await message.reply("Тільки адміністратори можуть використовувати /mute.")
        return

    args = message.text.split()[1:]
    minutes = 30
    target_user_id = None
    target_username = None

    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username or "користувач_без_username"
    elif args and args[0].startswith('@'):
        username = args[0].lstrip('@').lower()
        chat_id = message.chat.id
        if chat_id in user_cache and username in user_cache[chat_id]:
            target_user_id = user_cache[chat_id][username]
            target_username = args[0].lstrip('@')
        else:
            await message.reply("Користувача не знайдено. Він повинен спочатку надіслати повідomлення в групі.")
            return
        
        args = args[1:]

    if not target_user_id:
        await message.reply("Використання: Відповісти на повідомлення з /mute [хвилини] або використати /mute @username [хвилини] (за замовчуванням 30 хвилин)")
        return

    if args:
        try:
            minutes = int(args[0])
        except ValueError:
            await message.reply("Невірне значення хвилин. Має бути ціле число.")
            return

    if message.chat.type == "supergroup":
        until_date = int(time.time()) + (minutes * 60)

        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_topics=False
        )

        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_user_id,
                permissions=permissions,
                until_date=until_date
            )
            await message.reply(f"✅ Користувача @{target_username} замьючено на {minutes} хвилин.")
        except Exception as e:
            await message.reply(f"❌ Помилка при мьюті користувача: {str(e)}")
    
    else:
        try:
            await message.reply(f"⚠️ У звичайних групах мьют не підтримується. \nКористувач @{target_username} отримав попередження на {minutes} хвилин.")
        except Exception as e:
            await message.reply(f"❌ Помилка: {str(e)}")

@dp.message(Command("unmute"))
async def unmute_handler(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        await message.reply("Тільки адміністратори можуть використовувати /unmute.")
        return

    args = message.text.split()[1:]
    target_user_id = None
    target_username = None

    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username or "користувач_без_username"
    elif args and args[0].startswith('@'):
        username = args[0].lstrip('@').lower()
        chat_id = message.chat.id
        if chat_id in user_cache and username in user_cache[chat_id]:
            target_user_id = user_cache[chat_id][username]
            target_username = args[0].lstrip('@')
        else:
            await message.reply("Користувача не знайдено. Він повинен спочатку надіслати повідомлення в групі.")
            return

    if not target_user_id:
        await message.reply("Використання: Відповісти на повідомлення з /unmute або використати /unmute @username")
        return

    if message.chat.type == "supergroup":
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False,
            can_manage_topics=False
        )

        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_user_id,
                permissions=permissions,
                until_date=0
            )
            await message.reply(f"✅ Користувача @{target_username} розмучено.")
        except Exception as e:
            await message.reply(f"❌ Помилка при розмуті користувача: {str(e)}")
    
    else:
        try:
            await message.reply(f"ℹ️ У звичайних групах мьют не підтримується, тому розмут не потрібний.")
        except Exception as e:
            await message.reply(f"❌ Помилка: {str(e)}")

@dp.message(Command("chat_type"))
async def chat_type_handler(message: Message):
    chat_type = message.chat.type
    chat_title = message.chat.title or "Особистий чат"
    
    if chat_type == "supergroup":
        response = f"🗂️ Це супергрупа: {chat_title}\n✅ Підтримується повний функціонал муту"
    elif chat_type == "group":
        response = f"👥 Це звичайна група: {chat_title}\n⚠️ Мьют не підтримується (тільки попередження)"
    else:
        response = f"💬 Це {chat_type}: {chat_title}\n❌ Команди не працюють"
    
    await message.reply(response)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())