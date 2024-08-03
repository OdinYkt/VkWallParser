from functools import wraps

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

from TgBot.constants.common import IS_LINUX

if IS_LINUX:
    from xvfbwrapper import Xvfb


def ONLY_LINUX(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if IS_LINUX:
            return func(*args, **kwargs)
    return _wrapper


class WebDriverLinux:
    def __init__(self):
        self.vdisplay = None
        self.init()

    def _get_driver(self) -> WebDriver:
        options = Options()
        if IS_LINUX:
            options.add_argument("headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        return uc.Chrome(options=options, driver_executable_path=ChromeDriverManager().install())

    @ONLY_LINUX
    def init(self):
        self.vdisplay = Xvfb()

    @ONLY_LINUX
    def start(self):
        self.vdisplay.start()

    @ONLY_LINUX
    def stop(self):
        self.vdisplay.stop()

    def __enter__(self) -> WebDriver:
        self.start()
        return self._get_driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()