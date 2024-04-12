import os
import logging
from datetime import datetime
from logging import Formatter
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler
from chardet.universaldetector import UniversalDetector

# 不要なロガーをレベル設定
logging.getLogger("werkzeug").setLevel(ERROR)
logging.getLogger("httpcore.http11").setLevel(ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(ERROR)
logging.getLogger("googleapiclient.discovery_cache").setLevel(ERROR)
logging.getLogger("googleapiclient.discovery").setLevel(ERROR)
logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(ERROR)
logging.getLogger("WDM").setLevel(ERROR)
logging.getLogger("oauthlib.oauth1.rfc5849").setLevel(ERROR)
logging.getLogger("requests_oauthlib.oauth1_auth").setLevel(ERROR)

# Trueで日付、Falseでdebugとinfoのログファイル名
# 起動しっぱなしはFalseにする
flag_datelog = False
dir_path = "./Log"
log_encode = "utf-8"
# log_encode = "CP932"


def encode_detect(filepath):
    if not os.path.exists(filepath):
        return 1, ""
    try:
        try:
            detector = UniversalDetector()
            with open(filepath, "rb") as f:
                while True:
                    binary = f.readline()
                    if binary == b"":
                        break
                    detector.feed(binary)
                    if detector.done:
                        break
        finally:
            detector.close()
        # print("encoding:" + str(detector.result["encoding"]))
        if detector.result["encoding"] is None:
            return 0, "CP932"
        elif detector.result["encoding"] in ["utf-8", "UTF-8-SIG"]:
            return 0, "utf-8"
        elif detector.result["encoding"] in ["CP932", "SHIFT_JIS", "Windows-1254"]:
            return 0, "CP932"
        else:
            return 0, detector.result["encoding"]
    except:
        return 2, ""


def change_encode(filepath, after_encode):
    try:
        ret, before_encode = encode_detect(filepath)
        if ret == 1:
            # ファイルがない場合はそのまま返す
            return 1
        if before_encode == after_encode:
            # 再エンコードが不要な場合はそのまま返す
            return 0
        try:
            os.rename(filepath, filepath + "_bk")
        except:
            if os.path.exists(filepath):
                os.remove(filepath)
            # リネーム失敗時は削除して返す
            return 1
        if ret == 2:
            # エンコードの読み取り失敗時はリネームして返す
            return 1
        try:
            with open(filepath + "_bk", "r", encoding=before_encode) as f:
                txt = f.read()
            with open(filepath, "w", encoding=after_encode) as f:
                f.write(txt)
            os.remove(filepath + "_bk")
        except:
            if os.path.exists(filepath):
                os.remove(filepath)
            return 1
        return 0
    except:
        return 1


def log_main(flag_datelog, dir_path, log_encode):
    handlers = []

    # ストリームハンドラの設定
    rich_handler: RichHandler = RichHandler(rich_tracebacks=True)
    rich_handler.setLevel(INFO)
    rich_handler.setFormatter(Formatter("%(message)s"))
    handlers.append(rich_handler)

    # 保存先の有無チェック
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    # ファイルハンドラの設定
    if flag_datelog:
        logfile_path = f"{dir_path}/{datetime.now():%Y-%m-%d}.log"
        if os.path.exists(logfile_path):
            ret = change_encode(logfile_path, log_encode)
        file_handler = RotatingFileHandler(
            logfile_path,
            "a",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding=log_encode,
        )
        file_handler.setLevel(DEBUG)
        file_handler.setFormatter(
            # Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s")
            Formatter(
                "%(asctime)s [%(levelname)s] %(name)s %(filename)s %(funcName)s %(lineno)d: %(message)s"
            )
        )
        handlers.append(file_handler)

        # ルートロガーの設定
        logging.basicConfig(level=NOTSET, handlers=handlers)
    else:
        loggger_dic = {
            "0_debug": DEBUG,
            "1_info": INFO,
            "2_warning": WARNING,
            "3_error": ERROR,
        }
        for i in list(loggger_dic.keys()):
            logfile_path = f"{dir_path}/{i}.log"
            if os.path.exists(logfile_path):
                ret = change_encode(logfile_path, log_encode)
            logger_temp = RotatingFileHandler(
                logfile_path,
                "a",
                maxBytes=10 * 1024 * 1024,
                backupCount=10,
                encoding=log_encode,
            )
            logger_temp.setLevel(loggger_dic[i])
            logger_temp.setFormatter(
                # Formatter("%(asctime)s [%(levelname).4s] %(filename)s %(funcName)s %(lineno)d: %(message)s")
                Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s %(filename)s %(funcName)s %(lineno)d: %(message)s"
                )
            )
            handlers.append(logger_temp)

        # ルートロガーの設定
        logging.basicConfig(level=NOTSET, handlers=handlers)


def log_decorator(logger):
    def _log_decorator(func):
        def wrapper(*args, **kwargs):
            local_args = locals()
            try:
                logger.debug(f"start: {func.__name__}  args: {str(local_args)}")
                return_val = func(*args, **kwargs)
                # logger.debug(f"  end: {func.__name__}  ret: {str(return_val)}")
                logger.debug(f"  end: {func.__name__}")
                return return_val
            except Exception as e:
                logger.exception(f"error: {func.__name__}")
                raise e

        return wrapper

    return _log_decorator


log_main(flag_datelog, dir_path, log_encode)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.debug("テスト: debug")
    logger.info("テスト: info")
    logger.warning("テスト: warning")
    logger.error("テスト: error")
    logger.critical("テスト: critical")
    os.system("PAUSE")
