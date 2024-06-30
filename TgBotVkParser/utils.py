import logging
import re

import asyncio
from datetime import datetime, timedelta, date
from functools import wraps
from typing import Optional

from telegram.error import RetryAfter, TimedOut

from constants import IS_LINUX

if IS_LINUX:
    from xvfbwrapper import Xvfb


def ONLY_LINUX(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if IS_LINUX:
            return func(*args, **kwargs)
    return _wrapper


class DisplayWrapper:
    def __init__(self):
        self.vdisplay = None
        self.init()

    @ONLY_LINUX
    def init(self):
        self.vdisplay = Xvfb()

    @ONLY_LINUX
    def start(self):
        self.vdisplay.start()

    @ONLY_LINUX
    def stop(self):
        self.vdisplay.stop()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


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


def split_text_into_chunks(text, max_length_first: int, max_length_other: Optional[int] = None):
    # Разделяем текст на предложения
    sentences = re.split(r'(?<=[.!?])(\s+|\n)', text)

    chunks = []
    current_chunk = ""

    if max_length_other is None:
        max_length_other = max_length_first

    cur_max_length = max_length_first
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            delimiter = sentences[i + 1]
        else:
            delimiter = ""

        if len(current_chunk) + len(sentence) + len(delimiter) > cur_max_length:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
            cur_max_length = max_length_other
        else:
            current_chunk += " " + sentence

    # Добавляем последний чанк
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def retry_on_exception(exception_type=(RetryAfter, TimedOut), n=5):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(n):
                try:
                    return await func(*args, **kwargs)
                except exception_type as e:
                    last_exception = e
                    logging.info(f'Не удалось отправить. Попытка #{attempt}\n'
                                 f'Отловлена ошибка: {str(e)}')
                    await asyncio.sleep(10)
            logging.error('Сообщение не отправлено!')
            raise last_exception
        return wrapper
    return decorator
