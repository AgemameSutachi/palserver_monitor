import os
import logging
from datetime import datetime
from logging import Formatter
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler
import sys

# ストリームハンドラの設定
rich_handler = RichHandler(rich_tracebacks=True)
rich_handler.setLevel(INFO)
rich_handler.setFormatter(Formatter("%(message)s"))

# 保存先の有無チェック
if not os.path.isdir('./Log'):
    os.makedirs('./Log', exist_ok=True)

# カスタムファイルハンドラの設定
class MyRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename=None, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=0):
        if filename is None:
            filename = self.get_log_filename()
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.current_date = datetime.now().date()

    def shouldRollover(self, record):
        return datetime.now().date() != self.current_date

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        self.baseFilename = self.get_log_filename()
        self.mode = 'w'
        self.stream = self._open()

    def get_log_filename(self):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Log')
        return os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")

    def get_log_filename(self):
        log_dir = os.path.join(os.getcwd(), 'Log')  # PyInstaller用のパスを利用
        return os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")


# ファイルハンドラの初期化
file_handler = MyRotatingFileHandler(
    maxBytes=1000000, backupCount=10
)

# ルートロガーの設定
logging.basicConfig(level=NOTSET, handlers=[rich_handler, file_handler])

def getLogger():
    return logging.getLogger(__name__)
