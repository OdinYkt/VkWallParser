import logging

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


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
    driver = setup_driver()

    driver.get('https://google.com')
    logging.info(driver.title)
