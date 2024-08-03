import os
from environs import Env

env = Env()
env.read_env()

IS_LINUX = True if not os.name == 'nt' else False

VK_GROUP_NAME = env.str('VK_GROUP_NAME')

TG_GROUP_ID = env.str("TG_GROUP_ID")
TG_TOKEN_BOT = env.str("TG_TOKEN_BOT")
ADMIN_TG_IDS = env.list('ADMIN_TG_IDS', [], subcast=int)

INTERVAL_HOURS = env.int("INTERVAL_HOURS")

PARSE_MODE = "HTML"
SLEEP_BEFORE_REPLY = 1
SLEEP_BETWEEN_POSTS = 2
SLEEP_WHEN_ERROR = 30

WRITE_TIMEOUT = 30

DEFAULT_STRFTIME = '%d/%m/%Y %H:%M:%S'
