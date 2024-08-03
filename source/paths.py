from datetime import datetime
from pathlib import Path
from typing import List


class _Paths:
    _root = Path(__file__).parents[2]   # корневая папка запуска бота

    STATE_FILE_NAME = ".app_state"      # глобальное состояние

    @property
    def root(self) -> Path:
        return self._root

    @property
    def tg_bot(self) -> Path:
        return self.root / 'source'

    @property
    def main_py(self) -> Path:
        return self.tg_bot / 'main.py'

    @property
    def logs(self) -> Path:
        return self.root / '.logs'

    @property
    def state_file(self) -> Path:
        return self.root / self.STATE_FILE_NAME

    def get_new_log_file(self):
        if not self.logs.exists():
            self.logs.mkdir()
        return self.logs / f'parser_log_{datetime.utcnow().strftime("%d_%m_%Y_h%H_m%M_s%S")}.log'

    def get_last_logs(self, count: int) -> List[Path]:
        return sorted(self.logs.glob('*.log'), key=lambda x: x.stat().st_ctime, reverse=True)[:count]


paths = _Paths()
