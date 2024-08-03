import pickle

from source.utils.common import app_logger
from source.paths import paths


class _AppState:
    # Тут создать, чтобы знать какие есть переменные
    # инициализация в load_state
    FIRST_STARTED = None
    LAST_RESTARTED = None

    KEEP_SCHEDULER_ENABLED = None
    SCHEDULER_CREATED = None

    def __init__(self):
        self.load_state()

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        self.save_state()

    def get_state(self):
        return self.__dict__['_state']

    def clear_state(self):
        app_logger.info('Параметры состояния очищены')
        paths.state_file.unlink(True)
        self.load_state()

    def save_state(self):
        with open(str(paths.state_file), 'wb') as f:
            pickle.dump(self.__dict__, f)

    def load_state(self):
        if paths.state_file.exists():
            with open(str(paths.state_file), 'rb') as f:
                state = pickle.load(f)
                self.__dict__.update(state)
            app_logger.info(f'Состояние загружено: {self.__dict__}')
        else:
            self.FIRST_STARTED = None
            self.LAST_RESTARTED = None

            self.KEEP_SCHEDULER_ENABLED = False
            self.SCHEDULER_CREATED = False

            app_logger.debug(f'Состояние не обнаружено. Дефолтное: {self.__dict__}')


APP_STATE = _AppState()
