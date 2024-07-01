import random
from datetime import timedelta
from typing import Optional

import requests
from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler

from vk_wall_parser import VkParser
from utils import split_text_into_chunks, retry_on_exception, app_logger
from constants import (
    TG_BOT_TOKEN,
    TG_GROUP_ID,
    INTERVAL_HOURS,
    VK_GROUP_NAME,
    TG_ADMIN_ID,
    TG_MAX_TEXT,
    TG_MAX_CAPTION,
    AppState
)


async def send_posts(admin_chat_id: int, time_delta: timedelta):
    @retry_on_exception()
    async def _send_message():
        return await bot.send_message(
            chat_id=TG_GROUP_ID,
            text=post_body
        )

    @retry_on_exception()
    async def _send_media_group():
        return await bot.send_media_group(
            chat_id=TG_GROUP_ID,
            media=[InputMediaPhoto(media=data) for data in images_data],
            caption=post_body
        )

    @retry_on_exception()
    async def _send_reply_to_post():
        return await bot.send_message(
            chat_id=TG_GROUP_ID,
            reply_to_message_id=group_post.message_id,
            text=reply_to_post
        )

    @retry_on_exception()
    async def _posts_not_found():

        if not admin_chat_id:
            app_logger.critical('WRONG admin_chat_id!')
            return
        await bot.send_message(
            chat_id=admin_chat_id,
            text='Посты для обновления не обнаружены.'
        )

    app_logger.info("VK PARSER ENABLED")
    parser = VkParser(group_name=VK_GROUP_NAME)
    posts = parser.get_posts(time_delta=time_delta)
    if not posts:
        await _posts_not_found()
        app_logger.info('POSTS NOT FOUND.')
        return

    app_logger.info('Start sending posts to group')
    for post in posts[::-1]:
        post_body = f"{post.text}\n" \
               f"Posted:{post.date.strftime('%d-%m-%Y %H:%M')}\n" \
               f"by author:{post.author if post.author else VK_GROUP_NAME}"

        images_data = []
        images_comments = {}
        if post.images:
            for i, image in enumerate(post.images):
                image_data = requests.get(image.src).content
                images_data.append(image_data)
                if image.comments:
                    images_comments.update(
                        {
                            f'\nИзображение {i}': image.comments
                        }
                    )

        if images_comments:
            post_body += '\n'.join([f'{key}: {value}\n' for key, value in images_comments.items()])

        split_post_body = None

        max_chars = TG_MAX_TEXT
        if images_data:
            max_chars = TG_MAX_CAPTION

        if len(post_body) >= max_chars:
            split_post_body = split_text_into_chunks(post_body, max_chars, max_length_other=TG_MAX_TEXT)
            post_body = split_post_body[0]

        if not images_data:
            group_post = await _send_message()
        else:
            group_post = await _send_media_group()

        if split_post_body:
            if isinstance(group_post, tuple):
                group_post = group_post[0]
            for reply_to_post in split_post_body[1:]:
                await asyncio.sleep(1)
                await _send_reply_to_post()

        app_logger.info(f'Post {post.id} sent. Waiting.')
        await asyncio.sleep(2)

    app_logger.info('Done...')


async def send_posts_job(admin_chat_id: int, interval: int):
    while True:
        await asyncio.sleep(interval * 3600)
        await send_posts(admin_chat_id, timedelta(hours=interval))


async def start(update, context):
    await update.message.reply_text(f'Бот жив. Запущен: {AppState.STARTED}')


async def start_parsing(update: Optional[Update], context):
    if update.message.from_user.id != TG_ADMIN_ID:
        await update.message.reply_text(f'С вашего счёта списано: 0.{random.randint(1, 100)} USD\n'
                                        f'Свяжитесь с @OdinYkt')
        return

    if AppState.PARSING_ENABLED:
        await update.message.reply_text(f'Парсинг уже был активирован.')
        return
    AppState.PARSING_ENABLED = True
    if not AppState.ADMIN_CHAT_ID:
        AppState.ADMIN_CHAT_ID = update.effective_chat.id

    await update.message.reply_text(f'Бот запущен. Обновление постов каждые {INTERVAL_HOURS} часов.')

    asyncio.create_task(send_posts_job(AppState.ADMIN_CHAT_ID, int(INTERVAL_HOURS)))


async def force_send_posts(update, context):
    if update.message.from_user.id != TG_ADMIN_ID:
        await update.message.reply_text(f'С вашего счёта списано: 0.{random.randint(1, 100)} USD\n'
                                        f'Свяжитесь с @OdinYkt')
        return
    time_args = update.message.text[len("/force "):]
    try:
        days = int(time_args)
    except ValueError:
        await update.message.reply_text("Аргумент команды - количество дней. Введите команду корректно.")
    else:
        await update.message.reply_text(f"Принудительный скан постов за {days} дней")
        await send_posts(update, time_delta=timedelta(days=days))


def main():
    global bot
    bot = Bot(TG_BOT_TOKEN)
    application = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('start_parsing', start_parsing))
    application.add_handler(CommandHandler('force', force_send_posts))

    if AppState.PARSING_ENABLED:
        asyncio.create_task(
            send_posts_job(
                admin_chat_id=AppState.ADMIN_CHAT_ID,
                interval=int(INTERVAL_HOURS)
            )
        )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import asyncio
    main()
