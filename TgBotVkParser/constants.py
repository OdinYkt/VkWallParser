import os
from dotenv import load_dotenv
load_dotenv()

IS_LINUX = True if not os.name == 'nt' else False
VK_GROUP_NAME = os.getenv("VK_GROUP_NAME")