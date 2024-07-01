from tg_bot import main
from utils import app_logger
from constants import AppState


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        app_logger.info('Clearing state before shut down')
        AppState.clear_state()
        raise e
