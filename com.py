import os
import logging
from datetime import datetime
from logging import Formatter
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler

# 不要なロガーをレベル設定
logging.getLogger("werkzeug").setLevel(ERROR)
logging.getLogger("httpcore.http11").setLevel(ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(ERROR)
logging.getLogger("googleapiclient.discovery_cache").setLevel(ERROR)
logging.getLogger("googleapiclient.discovery").setLevel(ERROR)

# Trueで日付、Falseでdebugとinfoのログファイル名
# 起動しっぱなしはFalseにする
flag_datelog = False

# ストリームハンドラの設定
rich_handler = RichHandler(rich_tracebacks=True)
rich_handler.setLevel(INFO)
# rich_handler.setLevel(DEBUG)

# 日付の表示フォーマットを変更する
date_format = "%Y/%m/%d %H:%M:%S"
rich_handler.setFormatter(Formatter("%(asctime)s - %(message)s", datefmt=date_format))


# 保存先の有無チェック
if not os.path.isdir("./Log"):
    os.makedirs("./Log", exist_ok=True)

# ファイルハンドラの設定
if flag_datelog:
    file_handler = RotatingFileHandler(
        f"./Log/{datetime.now():%Y-%m-%d}.log",
        "a",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
    )
    file_handler.setLevel(DEBUG)
    file_handler.setFormatter(
        # Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s")
        Formatter(
            "%(asctime)s [%(levelname)s] %(name)s %(filename)s %(funcName)s %(lineno)d: %(message)s"
        )
    )

    # ルートロガーの設定
    logging.basicConfig(level=NOTSET, handlers=[rich_handler, file_handler])
else:
    file_handler_debug = RotatingFileHandler(
        f"./Log/debug.log", "a", maxBytes=10 * 1024 * 1024, backupCount=10
    )
    file_handler_debug.setLevel(DEBUG)
    file_handler_debug.setFormatter(
        # Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s")
        Formatter(
            "%(asctime)s [%(levelname)s] %(name)s %(filename)s %(funcName)s %(lineno)d: %(message)s"
        )
    )
    file_handler_info = RotatingFileHandler(
        f"./Log/info.log", "a", maxBytes=10 * 1024 * 1024, backupCount=10
    )
    file_handler_info.setLevel(INFO)
    file_handler_info.setFormatter(
        # Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s")
        Formatter(
            "%(asctime)s [%(levelname)s] %(name)s %(filename)s %(funcName)s %(lineno)d: %(message)s"
        )
    )
    # ルートロガーの設定
    logging.basicConfig(
        level=NOTSET, handlers=[rich_handler, file_handler_debug, file_handler_info]
    )


def log_decorator(logger):
    def _log_decorator(func):
        def wrapper(*args, **kwargs):
            local_args = locals()
            try:
                logger.debug(f"start: {func.__name__}  args: {str(local_args)}")
                return_val = func(*args, **kwargs)
                # logger.debug(f'  end: {func.__name__}  ret: {str(return_val)}')
                logger.debug(f"  end: {func.__name__}")
                return return_val
            except Exception as e:
                logger.exception(f"error: {func.__name__}")
                raise e

        return wrapper

    return _log_decorator
