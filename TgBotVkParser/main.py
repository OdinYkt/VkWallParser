from datetime import datetime

from tg_bot import main
from utils import app_logger
from constants import AppState


if __name__ == '__main__':
    try:
        AppState.LAST_RESTARTED = datetime.utcnow().strftime("%d-%m-%Y %H:%M")
        if not AppState.STARTED:
            AppState.STARTED = datetime.utcnow().strftime("%d-%m-%Y %H:%M")
        main()
    except KeyboardInterrupt as e:
        app_logger.info('Clearing state before shut down')
        AppState.clear_state()
        raise e
