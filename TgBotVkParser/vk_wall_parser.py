import logging

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service


def setup_driver() -> WebDriver:
    logging.basicConfig(level=logging.INFO)
    service = Service(executable_path=ChromeDriverManager().install())
    return WebDriver(service=service)


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
