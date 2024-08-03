import asyncio
import json
from typing import List

import requests
from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, Application, MessageHandler, filters
from telegram.constants import MessageLimit

from source.paths import paths
from source.utils.WrappedHTTPXRequest import WrappedHTTPXRequest

from source.tasks import restart_scheduler, activate_scheduler
from source.utils.app_state import APP_STATE
from source.utils.common import app_logger, Singleton, split_text_into_chunks
from source.constants import (
    TG_TOKEN_BOT,
    SLEEP_BETWEEN_POSTS,
    PARSE_MODE,
    INTERVAL_HOURS,
    ADMIN_TG_IDS,
    WRITE_TIMEOUT,
    DEFAULT_STRFTIME, VK_GROUP_NAME, TG_GROUP_ID,
)
from source.vk_wall_parser import VkPost

ADMINS = filters.User(ADMIN_TG_IDS)


class MasterBot(metaclass=Singleton):
    __application = None

    def __init__(self):
        self.bot = Bot(TG_TOKEN_BOT, request=WrappedHTTPXRequest(write_timeout=WRITE_TIMEOUT))

    def run_application(self):
        self.__init_application()
        self.__application.run_polling(allowed_updates=Update.ALL_TYPES)

    def __init_application(self):
        self.__application = ApplicationBuilder() \
            .request(WrappedHTTPXRequest(write_timeout=WRITE_TIMEOUT)) \
            .token(TG_TOKEN_BOT) \
            .concurrent_updates(True) \
            .post_init(self.post_init) \
            .build()

        # # # USERS # # #
        self.__application.add_handler(
            CommandHandler(
                command='start',
                callback=self.start
            )
        )

        # # # ADMINS # # #
        self.__application.add_handler(
            CommandHandler(
                command='enable_parsing',
                callback=self.enable_parsing,
                filters=ADMINS
            )
        )

        self.__application.add_handler(
            CommandHandler(
                command='get_logs',
                callback=self.get_logs,
                filters=ADMINS
            )
        )

    @staticmethod
    async def post_init(application: Application):
        await restart_scheduler(application)

    async def start(self, update: Update, context):
        await update.message.reply_text('Бот активен.\n'
                                        f'Запущен: {APP_STATE.FIRST_STARTED}.\n'
                                        f'Последний перезапуск: {APP_STATE.LAST_RESTARTED}')

    async def enable_parsing(self, update: Update, context):
        if APP_STATE.KEEP_SCHEDULER_ENABLED:
            await update.message.reply_text(f'Планировщик уже был запущен')
            return

        APP_STATE.KEEP_SCHEDULER_ENABLED = True

        await update.message.reply_text(f'Запуск планировщика. Обновление постов каждые {INTERVAL_HOURS} часов.')
        await activate_scheduler(context.job_queue)

    async def get_logs(self, update: Update, context):
        text = update.effective_message.text
        split = text.split()
        count_logs = ' '.join(split[1:]) if len(split) > 1 else None

        if not count_logs:
            count_logs = 3

        for log_path in paths.get_last_logs(count_logs):
            await update.message.reply_document(log_path)

    async def post_to_group(self, posts: List[VkPost]):
        app_logger.info('Start sending posts to group')
        for post in posts[::-1]:
            post_body = post.text

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

            max_chars = MessageLimit.MAX_TEXT_LENGTH
            if images_data:
                max_chars = MessageLimit.CAPTION_LENGTH

            if len(post_body) >= max_chars:
                split_post_body = split_text_into_chunks(
                    text=post_body,
                    max_length_first=max_chars,
                    max_length_other=MessageLimit.MAX_TEXT_LENGTH,
                    by_words=True
                )
                post_body = split_post_body[0]

            if not images_data:
                group_post = await self.bot.send_message(
                    chat_id=TG_GROUP_ID,
                    text=post_body
                )
            else:
                group_post = await self.bot.send_media_group(
                    chat_id=TG_GROUP_ID,
                    media=[InputMediaPhoto(media=data) for data in images_data],
                    caption=post_body
                )

            if split_post_body:
                if isinstance(group_post, tuple):
                    group_post = group_post[0]
                for reply_to_post in split_post_body[1:]:
                    await asyncio.sleep(SLEEP_BETWEEN_POSTS)
                    await self.bot.send_message(
                        chat_id=TG_GROUP_ID,
                        reply_to_message_id=group_post.message_id,
                        text=reply_to_post
                    )

            app_logger.info(f'Post {post.id} sent. Waiting.')
            await asyncio.sleep(SLEEP_BETWEEN_POSTS)

        app_logger.info('Done...')
