import asyncio
from datetime import datetime, timedelta

from telegram.ext import Application, JobQueue, CallbackContext

from source.utils.app_state import APP_STATE
from source.utils.common import app_logger
from source.constants import INTERVAL_HOURS, VK_GROUP_NAME
from source.vk_wall_parser import VkParser


async def restart_scheduler(application: Application):
    if APP_STATE.KEEP_SCHEDULER_ENABLED:
        app_logger.critical('Бот был перезапущен после перезапуска!')
        APP_STATE.LAST_RESTARTED = datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")
        await activate_scheduler(application.job_queue)
        return
    app_logger.critical('Бот запущен без предварительных параметров.')


async def activate_scheduler(job_queue: JobQueue):
    """
    Главный планировщик

    Note:
        * Интервал между запусками задается INTERVAL_HOURS
        * Гарантирована работа только одного экземпляра планировщика
        * Планировщик перезапускается при запуске бота, если включен параметр KEEP_SCHEDULER_ENABLED
    """
    app_logger.info('Активация планировщика')
    if APP_STATE.SCHEDULER_CREATED:
        app_logger.critical('Отказано. Попытка запустить второй планировщик.')
        return
    APP_STATE.SCHEDULER_CREATED = True

    job_queue.run_repeating(
        run_tasks,
        interval=INTERVAL_HOURS,
        first=10,
    )
    app_logger.info(f'Планировщик запущен c периодичностью {INTERVAL_HOURS} час')


async def run_tasks(context: CallbackContext):
    app_logger.info('Запуск задач...')
    await parser_post(timedelta(hours=INTERVAL_HOURS, minutes=5))
    app_logger.info(f'Работа окончена. Следующий запуск через {INTERVAL_HOURS}')


async def parser_post(time_delta: timedelta):
    from source.MasterBot import MasterBot
    app_logger.info(f"Vk parser enabled with delta: {time_delta}")
    parser = VkParser(group_name=VK_GROUP_NAME)

    posts = await asyncio.to_thread(parser.get_posts_sync, time_delta)
    if not posts:
        app_logger.info('POSTS NOT FOUND')
        return
    app_logger.info(f'Собрано {len(posts)} постов')

    master_bot = MasterBot()
    await master_bot.post_to_group(posts)
