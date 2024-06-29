import locale
from datetime import datetime, timedelta, time, date
from enum import Enum
from functools import wraps

from constants import IS_LINUX

if IS_LINUX:
    from xvfbwrapper import Xvfb
    locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')
else:
    locale.setlocale(locale.LC_ALL, 'ru_RU')


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
            time=time.fromisoformat(get_correct_time(time_str))
        )

    def get_correct_time(time_str_: str):
        if len(time_str_) < 5:
            time_str_ = f'0{time_str_}'
        return time_str_

    today = datetime.today()
    time_str = date_str.split()[-1]
    if 'вчера' in date_str:
        return relative(1)
    if 'сегодня' in date_str:
        return relative(0)

    day_str = ' '.join(date_str.split()[:3])

    day_ = datetime.strptime(day_str, "%d %b в")
    time_ = datetime.strptime(time_str, "%H:%M")

    return datetime.combine(
        date=date(year=today.year, month=day_.month, day=day_.day),
        time=time_.time()
    )