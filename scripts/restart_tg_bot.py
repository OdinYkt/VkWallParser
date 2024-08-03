import time
import subprocess
from pathlib import Path


SLEEP_BETWEEN_TRY = 60
WAITING_TIMEOUT = 50 * 60

SYSTEMCTL = '/bin/systemctl'
SERVICE_NAME = 'YOUR_SERVICE'    # tg_bot.service


def wait_restart():
    waited = 0
    lock_file_path = Path(__file__).parent / '.LOCK_RESTART'

    while lock_file_path.exists() and waited < WAITING_TIMEOUT:
        time.sleep(SLEEP_BETWEEN_TRY)
        waited += SLEEP_BETWEEN_TRY

    subprocess.run([SYSTEMCTL, 'restart', SERVICE_NAME])


if __name__ == '__main__':
    wait_restart()
