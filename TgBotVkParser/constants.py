import os
import pickle
from pathlib import Path
from datetime import datetime

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


class _AppState:
    FILE_PATH = Path('.app_state')

    def __init__(self):
        self.__dict__['_state'] = {
            'ADMIN_CHAT_ID': None,
            'PARSING_ENABLED': False,
            'STARTED': datetime.utcnow().strftime("%d-%m-%Y %H:%M")
        }
        self.load_state()

    def __getattr__(self, name):
        return self.__dict__['_state'][name]

    def __setattr__(self, name, value):
        self.__dict__['_state'][name] = value
        self.save_state()

    def clear_state(self):
        self.FILE_PATH.unlink(True)

    def save_state(self):
        with open(str(self.FILE_PATH), 'wb') as f:
            pickle.dump(self.__dict__, f)

    def load_state(self):
        if self.FILE_PATH.exists():
            with open(str(self.FILE_PATH), 'rb') as f:
                state = pickle.load(f)
                self.__dict__.update(state)


AppState = _AppState()
