from datetime import datetime

from source.MasterBot import MasterBot
from source.utils.app_state import APP_STATE
from source.utils.common import app_logger


if __name__ == '__main__':
    app_logger.info('Запуск...')

    if not APP_STATE.FIRST_STARTED:
        APP_STATE.FIRST_STARTED = datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")
    APP_STATE.SCHEDULER_CREATED = False

    master_bot = MasterBot()
    master_bot.run_application()
