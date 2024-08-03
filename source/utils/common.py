import re
import sys
import asyncio
import logging
import hashlib
import threading
import traceback
from datetime import datetime, timedelta, date

from typing import Optional, List

from telegram.error import RetryAfter, TimedOut

from source.constants.paths import paths
from source.constants.common import DEBUG_MODE, SLEEP_WHEN_ERROR


def setup_logger():
    logger = logging.getLogger('TgBotParser')
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    console_handler.setLevel(console_level)

    file_handler = logging.FileHandler(str(paths.get_new_log_file()), encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s|%(name)s:%(module)s:%(thread)d|%(levelname)s| %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    if DEBUG_MODE:
        logger.critical('DEBUG MODE ENABLED')
    return logger


app_logger = setup_logger()


def retry_on_exception(retries: int = 5, delay: int = SLEEP_WHEN_ERROR):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except RetryAfter as e:
                    last_exception = e
                    app_logger.info(f'Не удалось отправить. Попытка #{attempt}\n'
                                    f'Отловлена ошибка: {str(last_exception)}')
                    await asyncio.sleep(delay)
                except TimedOut:
                    app_logger.info('Отловлена ошибка: Timed out')
                    break
            else:
                logging.error('Сообщение не отправлено!')
                raise last_exception
        return wrapper
    return decorator


# некорректно работает, если в тексте есть предложения больше, чем максимальная длина
# разбивать по словам? у нас ограничение в 1024 | 4096 знаков -> нет смысла
def split_text_into_chunks(
        text: str,
        max_length_first: int,
        max_length_other: Optional[int] = None,
        by_words: bool = False
) -> List[str]:
    if by_words:
        sentences = re.split(r'(\s*?[.!?]\s*|\n)', text)  # Сохраняем разделители
    else:
        sentences = re.split(r'(\n\n)', text)

    chunks = []
    current_chunk = ""

    if max_length_other is None:
        max_length_other = max_length_first

    cur_max_length = max_length_first
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        delimiter = sentences[i + 1] if i + 1 < len(sentences) else ""

        if len(current_chunk) + len(sentence) + len(delimiter) >= cur_max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                cur_max_length = max_length_other
            current_chunk = sentence + delimiter
        else:
            current_chunk += sentence + delimiter

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def parse_vk_datetime(date_str: str) -> datetime:
    def relative(days: int) -> datetime:
        return datetime.combine(
            date=today - timedelta(days=days),
            time=datetime.strptime(get_correct_time(time_str), "%H:%M %p").time()
        )

    def get_correct_time(time_str_: str):
        if len(time_str_) < 5:
            time_str_ = f'0{time_str_}'
        return time_str_

    today = datetime.today()
    time_str = ' '.join(date_str.split()[-2:]).upper()
    if 'today' in date_str:
        return relative(0)
    if 'yesterday' in date_str:
        return relative(1)

    day_str = ' '.join(date_str.split()[:3])

    day_ = datetime.strptime(day_str, "%d %b at")
    time_ = datetime.strptime(time_str, "%H:%M %p")

    return datetime.combine(
        date=date(year=today.year, month=day_.month, day=day_.day),
        time=time_.time()
    )
