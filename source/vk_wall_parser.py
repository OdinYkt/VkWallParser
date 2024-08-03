import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from waiting import wait, TimeoutExpired
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common import NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from constants import VK_GROUP_NAME, IS_LINUX
from source.utils.WebDriverLinux import WebDriverLinux
from source.utils.common import app_logger, parse_vk_datetime


def setup_driver() -> WebDriver:
    service = Service(executable_path=ChromeDriverManager().install())
    options = Options()
    if IS_LINUX:
        options.add_argument("headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})

    return WebDriver(service=service, options=options)


@dataclass
class Image:
    src: str
    comments: Optional[str] = None


@dataclass
class VkPost:
    id: str
    date: datetime
    text: str
    images: List[Image] = field(default_factory=list)

    author: Optional[str] = None


class PostElement:
    def __init__(self, post_element: WebElement):
        self.element = post_element

    def get_data(self) -> VkPost:
        self.focus()
        self.close_notification()
        return VkPost(
            id=self.id,
            date=self.time,
            text=self.text,
            author=self.author,
            images=self.images,
        )

    def click_show_more(self):
        def get_element():
            try:
                return self.element.find_element(By.CLASS_NAME, "PostTextMore__content")
            except NoSuchElementException:
                pass

        def is_closed():
            return bool(get_element().text)

        try_counter = 0
        while is_closed() and try_counter < 10:
            try:
                get_element().click()
            except (ElementNotInteractableException, ElementClickInterceptedException):
                app_logger.error(f"Error while clicking 'Show more'. Try:#{try_counter}")
            try_counter += 1

    def focus(self):
        self.element.parent.execute_script("arguments[0].scrollIntoView(true);", self.element)

    def is_notification_displayed(self):
        def get_element():
            try:
                return self.element.parent.find_element(By.CLASS_NAME, "UnauthActionBox__close")
            except NoSuchElementException:
                pass
        try:
            wait(
                get_element,
                timeout_seconds=0.5
            )
        except TimeoutExpired:
            return False
        return True

    def close_notification(self):
        try_counter = 0
        while self.is_notification_displayed() or try_counter > 10:
            try:
                self.element.parent.find_element(By.CLASS_NAME, "UnauthActionBox__close").click()
            except (NoSuchElementException, ElementNotInteractableException):
                app_logger.error(f"Error while closing notification. Try:#{try_counter}")
                try_counter += 1

    def is_images_attached(self) -> bool:
        def get_element():
            try:
                return self.element.parent.find_element(By.CLASS_NAME, "PhotoPrimaryAttachment")
            except NoSuchElementException:
                pass
        if get_element():
            return True
        return False

    @property
    def _header(self) -> Tuple[WebElement, Optional[WebElement]]:
        return self.element.find_elements(By.CLASS_NAME, "PostHeaderSubtitle__item")    # type: ignore

    @property
    def id(self) -> str:
        return self.element.get_attribute("id")

    @property
    def time(self) -> datetime:
        try:
            rel_time_str = self.element.find_element(By.CLASS_NAME, "rel_date").get_attribute("time")
        except (NoSuchElementException, TypeError):
            pass
        else:
            if rel_time_str:
                return datetime.fromtimestamp(int(rel_time_str))

        try:
            datetime_str = self._header[0].text
            return parse_vk_datetime(datetime_str)
        except Exception as e:
            app_logger.error(str(e))

        return datetime.now()

    @property
    def author(self) -> Optional[str]:
        try:
            return self._header[1].text
        except IndexError:
            return None

    @property
    def text(self) -> str:
        def get_text():
            return self.element.find_element(By.CLASS_NAME, "wall_post_text").text

        if get_text().endswith("Show more"):
            self.click_show_more()
        return get_text()

    @property
    def images(self) -> Optional[List[Image]]:
        if not self.is_images_attached():
            return None
        if one_element := self.element.find_elements(By.CLASS_NAME, "PhotoPrimaryAttachment__imageElement"):
            return [Image(src=one_element[0].get_attribute('src'))]

        images = []

        image_elements = self.element.find_elements(By.CLASS_NAME, "MediaGrid__thumb")

        for image_element in image_elements:
            src = image_element.find_element(By.CLASS_NAME, "MediaGrid__imageElement").get_attribute('src')
            comments = image_element.find_element(By.CLASS_NAME, "MediaGrid__interactive").get_attribute('aria-label')
            images.append(
                Image(
                    src=src,
                    comments=comments[len('фотография'):].strip() if comments else None
                )
            )

        return images


class PostCollector:
    def __init__(self, url: str, driver: WebDriver):
        self.driver = setup_driver()
        self.driver.get(url)

        self._current_element = 0
        self.wall_element = self.driver.find_element(By.ID, "page_wall_posts")

    def close_driver(self):
        self.driver.close()

    def all_posts(self):
        return self.wall_element.find_elements(By.CLASS_NAME, "post")

    def get_current_element(self):
        while True:
            try:
                return self.all_posts()[self._current_element]
            except IndexError:
                self.driver.execute_script("javascript:window.scrollBy(500,550)")

    def __iter__(self):
        while True:
            yield PostElement(post_element=self.get_current_element()).get_data()
            self._current_element += 1


class VkParser:
    vk_base_url = "https://vk.com/"

    def __init__(self, group_name: str):
        self.group_name = group_name
        self.now = datetime.now()

    def get_posts_sync(self, time_delta: timedelta) -> List[VkPost]:
        return self._collect_posts(time_delta)

    def _collect_posts(self, time_delta: timedelta) -> List[VkPost]:
        posts = []

        with WebDriverLinux() as driver:
            post_collector = PostCollector(
                url=self.vk_base_url+self.group_name,
                driver=driver
            )
            for post in post_collector:
                if abs(post.date - self.now) > time_delta:
                    app_logger.info(f"Post doesn't match (id='{post.id}' time='{post.date}')")
                    app_logger.info(f"Collected : {len(posts)} posts")

                    post_collector.close_driver()
                    return posts
                app_logger.info(f"Post {post} collected")
                posts.append(post)


if __name__ == "__main__":
    parser = VkParser(group_name=VK_GROUP_NAME)
    parsed_posts = parser.get_posts_sync(time_delta=timedelta(days=1))
