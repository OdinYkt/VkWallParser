import logging
import os
from functools import wraps

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

IS_LINUX = True if not os.name == 'nt' else False

if IS_LINUX:
    from xvfbwrapper import Xvfb


def RUN_FOR_LINUX(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if IS_LINUX:
            return func(*args, **kwargs)
    return _wrapper


class DisplayWrapper:
    def __init__(self):
        self.vdisplay = None
        self.init()

    @RUN_FOR_LINUX
    def init(self):
        self.vdisplay = Xvfb()

    @RUN_FOR_LINUX
    def start(self):
        self.vdisplay.start()

    @RUN_FOR_LINUX
    def stop(self):
        self.vdisplay.stop()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def setup_driver() -> WebDriver:
    logging.basicConfig(level=logging.INFO)
    service = Service(executable_path=ChromeDriverManager().install())
    options = Options()
    options.add_argument("headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return WebDriver(service=service, options=options)


# # Определим датакласс для хранения данных постов
# @dataclass
# class Post:
#     id: int
#     date: datetime.datetime
#     text: str
#     images: List[str] = field(default_factory=list)


if __name__ == "__main__":
    with DisplayWrapper():
        driver = setup_driver()

        driver.get('https://google.com')
        logging.info(driver.title)
