import os
from dotenv import load_dotenv
load_dotenv()

IS_LINUX = True if not os.name == 'nt' else False

TG_MAX_TEXT = 4096
TG_MAX_CAPTION = 1024

VK_GROUP_NAME = os.getenv("VK_GROUP_NAME")

TG_GROUP_ID = os.getenv("TG_GROUP_ID")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_ADMIN_ID = int(os.getenv("TG_ADMIN_ID"))

INTERVAL_HOURS = os.getenv("INTERVAL_HOURS")

