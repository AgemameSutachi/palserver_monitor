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
# class MyRotatingFileHandler(RotatingFileHandler):
#     def __init__(self, filename=None, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=0):
#         if filename is None:
#             filename = self.get_log_filename()
#         super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
#         self.current_date = datetime.now().date()

#     def shouldRollover(self, record):
#         return datetime.now().date() != self.current_date

#     def doRollover(self):
#         if self.stream:
#             self.stream.close()
#             self.stream = None
#         self.baseFilename = self.get_log_filename()
#         self.mode = 'w'
#         self.stream = self._open()

#     def get_log_filename(self):
#         log_dir = os.path.join(os.getcwd(), 'Log')  # PyInstaller用のパスを利用
#         return os.path.join(log_dir, f"{datetime.now():%Y-%m-%d}.log")


# # ファイルハンドラの初期化
# file_handler = MyRotatingFileHandler(
#     maxBytes=1000000, backupCount=10
# )
# file_handler.setLevel(DEBUG)
# file_handler.setFormatter(
#     # Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s")
#     Formatter("%(asctime)s [%(levelname)s] %(filename)s %(funcName)s %(lineno)d: %(message)s")
# )

debug_handler = RotatingFileHandler("./Log/debug.log", "a", maxBytes=1000000, backupCount=10)
debug_handler.setLevel(DEBUG)
debug_handler.setFormatter(Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s"))

# INFO ログ用のハンドラとフォーマッター
info_handler = RotatingFileHandler("./Log/info.log", "a", maxBytes=1000000, backupCount=10)
info_handler.setLevel(INFO)
info_handler.setFormatter(Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s"))

# ルートロガーの設定
logging.basicConfig(level=NOTSET, handlers=[rich_handler, debug_handler,info_handler])

def getLogger():
    return logging.getLogger(__name__)
