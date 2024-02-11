print_txt="""
パルワールドサーバーの管理プログラム

毎分プロセス監視して起動していなかったら起動する
30分ごとにワールドをzip化してコピーする
6時間ごとにワールドをシャットダウンしてアップデートがあったらアップデートして、zip化してコピーしてgit commitする(プロセス監視はこの間停止)
毎日6時に強制的にサーバーアップデートする(プロセス監視はこの間停止)
"""
from com import getLogger
import psutil
import subprocess
import mcrcon
import time
import subprocess
import os
import sys
import zipfile
from datetime import datetime, timedelta
import schedule
from pysteamcmdwrapper import SteamCMD, SteamCMDException
import keyboard
import traceback
import pyautogui as pgui
import threading
from configmanager import ConfigManager
import logging
import shutil
import codecs
import csv
import re
from pandas import read_csv
logger=logging.getLogger(__name__)

CL_Con=ConfigManager()

# C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer\PalServer.exe
process_path_to_start = CL_Con.get("process_path_to_start")
# PalServer.exe
process_name_to_check_list = ["PalServer.exe","PalServer-Win64-Test-Cmd.exe"]
# 127.0.0.1
server_host = "127.0.0.1"
# 25585
server_port = int(CL_Con.get("server_port"))
# password
rcon_password = CL_Con.get("rcon_password")
# C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer\Pal\Saved
zip_dir = os.path.join(os.path.dirname(process_path_to_start),"Pal","Saved")
# C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer
repo_directory = os.path.dirname(process_path_to_start)
# C:\Users\aaaaa\temp\steamcmd
steamcmd_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(repo_directory)))
# C:\Users\aaaaa\temp\steamcmd\steamcmd.exe
steamcmd_exe_path = os.path.join(steamcmd_dir_path,"steamcmd.exe")
#10
backup_max_age_days=int(CL_Con.get("backup_max_age_days"))
#True
if CL_Con.get("flag_reboot","True") in ["0","FALSE","False","false"]:
    flag_reboot=False
else:
    flag_reboot=True




#入退出管理(showplayers不具合のため、未使用)
joinstatuscsv_path=CL_Con.get("joinstatuscsv_path")

update_in_progress = False

# 前回ダウンを検知した時刻を格納する変数
last_down_time = None
# ダウンを検知した回数を格納する変数
down_count = 0
# ロールバックを行う閾値（秒）
rollback_threshold_seconds = 300  # 5分

#プロセスチェック
def is_process_running(process_name_list):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    for process in psutil.process_iter(['pid', 'name']):
        for process_name in process_name_list:
            if process.info['name'] == process_name:
                logger.debug(f"Process {process_name} is running (PID: {process.info['pid']})")
                return True
    logger.debug("No matching processes found")
    return False

# プロセス起動
def start_process(process_path):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    try:
        subprocess.Popen(process_path)
        logger.info(f"{process_path} を起動しました。")
    except Exception as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)

def unzip_directory(zip_filepath, extract_path):
    logger.debug("start: " + str(sys._getframe().f_code.co_name))
    try:
        # ZIPファイルを解凍
        with zipfile.ZipFile(zip_filepath, 'r') as zipf:
            zipf.extractall(extract_path)

        logger.info("ZIPファイルを解凍しました: " + extract_path)
        return 0
    except Exception as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1

def rollback_process(repo_directory, zip_filepath):
    # ロールバック処理
    try:
        # ロールバック先のディレクトリを作成
        rollback_directory = os.path.join(repo_directory, "rollback")
        os.makedirs(rollback_directory, exist_ok=True)

        # ZIPファイルを解凍
        result = unzip_directory(zip_filepath, rollback_directory)
        if result != 0:
            logger.error("ロールバック処理中にエラーが発生しました。")
            return

        # 解凍後のディレクトリを元のディレクトリにコピー
        for item in os.listdir(rollback_directory):
            item_path = os.path.join(rollback_directory, item)
            dest_path = os.path.join(repo_directory, item)
            if os.path.isdir(item_path):
                shutil.copytree(item_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copy2(item_path, dest_path)

        logger.info("ロールバックが完了しました。")
    except Exception as e:
        logger.error("ロールバック処理中にエラーが発生しました。")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)

# プロセス監視
def processcheck(process_name_to_check_list, process_path_to_start,flag_first=False):
    try:
        global last_down_time, down_count

        logger.debug("start: " + str(sys._getframe().f_code.co_name))

        if update_in_progress:
            logger.info("アップデート中は処理をスキップします。")
            return 0

        if is_process_running(process_name_to_check_list):
            # logger.info(process_name_to_check+" は既に実行中です。")
            # プロセスが実行中の場合はリセット
            last_down_time = None
            down_count = 0
        else:
            if flag_first:
                start_process(process_path_to_start)
                return 0
            logger.warning("プロセスダウンを検知しました。")

            # 前回のダウン検知から一定時間以内に再度ダウン検知された場合
            if last_down_time and datetime.now() - last_down_time < timedelta(seconds=rollback_threshold_seconds):
                down_count += 1
            else:
                down_count = 1

            last_down_time = datetime.now()

            if down_count >= 2:
                logger.error("短時間に複数回プロセスダウンが検知されました。ロールバックを行います。\n現在未実装")
                # ロールバックのための処理を実行
                # rollback_process(repo_directory,zip_filepath)

                # ロールバック後にプロセスを再起動
                start_process(process_path_to_start)
            else:
                logger.info("再起動します。")
                git_commit(repo_directory, "crash!!")
                start_process(process_path_to_start)
    except:
        pass
    return 0


#rcon
def git_commit(repo_path, text="auto"):
    try:
        # 現在の日時を取得
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # カレントディレクトリを保存
        current_directory = os.getcwd()
        # リポジトリのディレクトリに移動
        os.chdir(repo_path)
        try:
            result = subprocess.run(['git', 'init'],capture_output=True)
            if result.stdout is not None:
                logger.debug(result.stdout)
            if result.stderr is not None:
                if len(result.stderr)>0:
                    logger.error(result.stderr)
            result = subprocess.run(['git', 'add', '-A'],capture_output=True)
            if result.stdout is not None:
                logger.debug(result.stdout)
            if result.stderr is not None:
                if len(result.stderr)>0:
                    logger.error(result.stderr)
            result = subprocess.run(['git', 'commit', '-m', timestamp + " " + text],capture_output=True, check=False, input="y\n", text=True)
            if result.stdout is not None:
                logger.debug(result.stdout)
            if result.stderr is not None:
                if len(result.stderr)>0:
                    logger.error(result.stderr)

            logger.info("コミットしました。: " + timestamp + " " + text)
            return 0
        except Exception as e:
            logger.info("エラー")
            errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
            logger.exception(e)
            return 1
        finally:
            # 元のディレクトリに戻る
            os.chdir(current_directory)
    except Exception as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1



def delete_old_backups(directory_path, max_age_days):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    try:
        # 現在の日時を取得
        current_datetime = datetime.now()

        # ディレクトリ内のファイルを取得
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]

        for file in files:
            file_path = os.path.join(directory_path, file)
            # ファイルの作成日時を取得
            created_time = datetime.fromtimestamp(os.path.getctime(file_path))

            # ファイルの年月日を比較
            if (current_datetime - created_time).days > max_age_days:
                # ファイルが10日以上前のものなら削除
                os.remove(file_path)
                logger.info("古いバックアップを削除しました: "+file_path)

        return 0
    except Exception as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1

def zip_directory(directory_path):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    # 現在の日時を取得
    current_datetime = datetime.now()
    # 日時をフォーマット
    timestamp = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    # zipファイルの名前を作成
    zip_filename = f"{timestamp}.zip"
    # 圧縮先のパスを作成
    zip_filepath = os.path.join(os.path.dirname(directory_path), zip_filename)
    
    try:
        # zipファイルを作成
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            # ディレクトリ内のファイルを追加
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, directory_path)
                    zipf.write(file_path, arcname=arcname)
        
        logger.info("ディレクトリを圧縮しました: "+zip_filepath)

        # 削除処理: 10日以上前のバックアップを削除
        delete_old_backups(directory_path, max_age_days=backup_max_age_days)
        return 0
    except Exception as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1

def kill_palserver(process_name_to_check_list):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    try:
        # タスクキルコマンドを実行
        for process_name_to_check in process_name_to_check_list:
            try:
                subprocess.run(["taskkill", "/IM", process_name_to_check, "/F"])
                logger.info(process_name_to_check+" をタスクキルしました。")
            except:pass
        return 0
    except subprocess.CalledProcessError as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1

def isNeedUpdate(interval_sec=10, retry_num=10, retry_interval_sec=10):
    def get_buildid_local(timeout_sec=10):
        result_locale = subprocess.run(
            [steamcmd_exe_path, "+force_install_dir " + repo_directory, "+login anonymous", "+app_status 2394010", "+quit"],
            stdout=subprocess.PIPE,
            encoding='utf-8',
            timeout=60
        )
        pattern = r"BuildID (\d+)"
        for _ in range(timeout_sec):
            time.sleep(1)
            match = re.search(pattern, result_locale.stdout)
            if match:
                build_id_locale = match.group(1)
                logger.debug("Locale BuildID:"+str(build_id_locale))
                return 1, build_id_locale
        return 0, ""

    def get_buildid_remote(timeout_sec=10):
        result_remote = subprocess.run(
            [steamcmd_exe_path, "+force_install_dir " + repo_directory, "+login anonymous", "+app_info_print 2394010", "+quit"],
            stdout=subprocess.PIPE,
            encoding='utf-8',
            timeout=60
        )
        pattern = r'"public"\s*{\s*"buildid"\s+"(\d+)"'
        for _ in range(timeout_sec):
            time.sleep(1)
            match = re.search(pattern, result_remote.stdout)
            if match:
                build_id_remote = match.group(1)
                logger.debug("Remote BuildID:"+str(build_id_remote))
                return 1, build_id_remote
        return 0, ""

    for _ in range(retry_num):
        flag_found_local, build_id_locale = get_buildid_local(interval_sec)
        if flag_found_local:
            break
        time.sleep(retry_interval_sec)

    for _ in range(retry_num):
        flag_found_remote, build_id_remote = get_buildid_remote(interval_sec)
        if flag_found_remote:
            break
        time.sleep(retry_interval_sec)

    if flag_found_local:
        if flag_found_remote:
            if build_id_locale == build_id_remote:
                logger.info("build_idが一致:"+str(build_id_locale)+" "+str(build_id_remote))
                return 0
            else:
                logger.info("build_idが不一致:"+str(build_id_locale)+" "+str(build_id_remote))
                return 1
        else:
            logger.warning("localは取得できたが、remoteは取得できず:"+str(build_id_locale))
            return 0
    else:
        if flag_found_remote:
            logger.warning("localは取得できず、remoteは取得できた:"+str(build_id_remote))
            return 0
        else:
            logger.error("local、remote両方取得できず")
            return 0

def worldsave_safe(host, port, password, process_name_to_check_list, process_path_to_start,flag_shutdown=False,time_shutdown_sec=60):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    logger.info("サーバーをダウンさせて、ワールドのコピーを取得し、コミットします。")
    global update_in_progress
    update_in_progress = True
    current_hour = datetime.now().hour

    try:
        if is_process_running(process_name_to_check_list):
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                command="Info"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)
            time.sleep(1)

            #ShowPlayersはバグって続きが取得できないのでコメントアウト
            # with mcrcon.MCRcon(host, password, port) as client:
            #     command="ShowPlayers"
            #     logger.info("Command sent: "+command)
            #     response = client.command(command)
            #     logger.info("Server response: "+response)
            # time.sleep(1)
            
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                command="Save"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)
            time.sleep(1)
            
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                if flag_shutdown:
                    # command="Shutdown 60 "
                    # command="Broadcast Shutdown has been scheduled for 60 seconds later."
                    command="Broadcast Shutdown_has_been_scheduled_for_"+str(time_shutdown_sec)+"_seconds_later."
                    #メンテナンスのため、60秒後にシャットダウンします。ログアウトしてください。"
                else:
                    # command="Shutdown 60 "
                    command="Broadcast Reboot_has_been_scheduled_for_"+str(time_shutdown_sec)+"_seconds_later."
                    #ワールド保存のため、60秒後に再起動します。ログアウトしてください。"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)

            if time_shutdown_sec<1:
                time.sleep(1)
            else:
                time.sleep(time_shutdown_sec)

            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                command="Save"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)
            time.sleep(1)
            
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                if flag_shutdown:
                    # command="Shutdown 10 メンテナンスのため、10秒後にシャットダウンします。ログアウトしてください。"
                    command="Shutdown 10 "
                else:
                    # command="Shutdown 10 ワールド保存のため、10秒後に再起動します。ログアウトしてください。"
                    command="Shutdown 10 "
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)

            for i in range(60):
                if not is_process_running(process_name_to_check_list):break
                time.sleep(1)
            else:
                #終了しないので、強制的に落とす
                kill_palserver(process_name_to_check_list)
                for i in range(60):
                    if not is_process_running(process_name_to_check_list):break
                    time.sleep(1)
                else:
                    #タスクキルでも落ちない場合
                    logger.info("タスクキルしても落とせなかったのでコミット等を行いません")
                    return 1
        zip_directory(zip_dir)
        git_commit(repo_directory)
        if flag_shutdown:
            return 0
        else:
            if current_hour == 6:
                logger.info("6時のため、サーバーアップデートを実施")
                worldupdate(steamcmd_dir_path, repo_directory)
                git_commit(repo_directory,"updated")
            else:
                logger.info("アップデートがあるか確認")
                if isNeedUpdate():
                    worldupdate(steamcmd_dir_path, repo_directory)
                    git_commit(repo_directory,"updated")
            start_process(process_path_to_start)
            return 0
    except Exception as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1
    finally:
        update_in_progress = False


def worldsave_nodown(host, port, password):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    logger.info("サーバーをダウンさせずにワールドのコピーを取得します。")
    if not update_in_progress:
        try:
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                command="Info"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)
            time.sleep(1)
            
            #ShowPlayersはバグって続きが取得できないのでコメントアウト
            # with mcrcon.MCRcon(host, password, port) as client:
            #     command="ShowPlayers"
            #     logger.info("Command sent: "+command)
            #     response = client.command(command)
            #     logger.info("Server response: "+response)
            # time.sleep(1)
            
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                command="Save"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)
            time.sleep(2)

            zip_directory(zip_dir)
            return 0
        except mcrcon.MCRconException as e:
            logger.info("エラー")
            errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
            logger.exception(e)
            return 1

def worldsave_hour(host, port, password, process_name_to_check_list, process_path_to_start):
    try:
        logger.debug("start: "+str(sys._getframe().f_code.co_name))
        current_hour = datetime.now().hour
        if current_hour % 6 != 0:  # 0時、6時、12時、18時の場合はスキップ
            worldsave_nodown(host, port, password)
        else:
            worldsave_safe(host, port, password, process_name_to_check_list, process_path_to_start)
    except:pass

def worldsave_half_hour(host, port, password):
    try:
        logger.debug("start: "+str(sys._getframe().f_code.co_name))
        worldsave_nodown(host, port, password)
    except:pass

# アップデート処理
def worldupdate(steamcmd_dir_path, repo_directory,flag_manual=False):
    logger.debug("start: " + str(sys._getframe().f_code.co_name))
    try:
        # カレントディレクトリを保存
        current_directory = os.getcwd()
        # SteamCMDのディレクトリに移動
        os.chdir(steamcmd_dir_path)

        # SteamCMDコマンドを実行し、標準出力と標準エラー出力を取得
        if flag_manual:
            result = subprocess.run(
                [steamcmd_exe_path, "+force_install_dir " + repo_directory, "+login anonymous", "+app_update 2394010 validate", "+quit"],
                encoding='utf-8'
            )
        else:
            result = subprocess.run(
                [steamcmd_exe_path, "+force_install_dir " + repo_directory, "+login anonymous", "+app_update 2394010 validate", "+quit"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            # 標準出力と標準エラー出力をログに記録
            if result.stdout is not None:
                logger.debug(result.stdout)
            if result.stderr is not None:
                if len(result.stderr)>0:
                    logger.error(result.stderr)

        # エラーチェック
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)

        logger.info("アップデートが完了しました。")
        return 0
    except subprocess.CalledProcessError as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1
    finally:
        # 元の作業ディレクトリに戻る
        os.chdir(current_directory)



#ライブラリでのアップデート(未使用)
def worldupdate2(steamcmd_dir_path, repo_directory):
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    try:
        # カレントディレクトリを保存
        current_directory = os.getcwd()
        # SteamCMDのディレクトリに移動
        os.chdir(steamcmd_dir_path)

        s = SteamCMD(steamcmd_dir_path)
        s.app_update(2394010,os.path.join(os.getcwd(),repo_directory),validate=True)

        logger.info("アップデートが完了しました。")
        return 0
    except Exception as e:
        logger.info("エラー")
        errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
        logger.exception(e)
        return 1
    finally:
        # 元の作業ディレクトリに戻る
        os.chdir(current_directory)


def joinstatuscsv_read():
    #ShowPlayersはバグって続きが取得できないのでコメントアウト
    # name,playeruid,steamid
    # aa,bb,cc
    # dd,ee,ff
    #[{'name': 'aa', 'playeruid': 'bb', 'steamid': 'cc'}, {'name': 'dd', 'playeruid': 'ee', 'steamid': 'ff'}]
    data = []
    with codecs.open(joinstatuscsv_path, 'r', encoding='shiftjis') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            data.append(row)

    return data

def joinstatuscsv_write(data, header=['name', 'playeruid', 'steamid']):
    #ShowPlayersはバグって続きが取得できないのでコメントアウト
    # data_to_write = [
    #     {'name': 'aa', 'playeruid': 'bb', 'steamid': 'cc'},
    #     {'name': 'dd', 'playeruid': 'ee', 'steamid': 'ff'}
    # ]
    with codecs.open(joinstatuscsv_path, 'w', encoding='shiftjis') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        
        # ヘッダーを書き込む
        writer.writeheader()

        # データを書き込む
        for row in data:
            writer.writerow(row)


# def joinstatus_check(txt):
#     joinstatuscsv_path
#     with open(joinstatuscsv_path,mode="r") as f:
#         reader = csv.reader(f)
#         l = [row for row in reader]
#     self.default_setting_path=path
#     if not os.path.exists(path):
#         with open(path, 'w', encoding="cp932",newline="") as f:
#             writer = csv.writer(f,delimiter=",")
#             writer.writerow(["key","value","detail"])
#         logger.warning("デフォルト設定ファイルがないため、作成しました。: "+path)
#     df=read_csv(path, sep=",", skipinitialspace=True, encoding="cp932")
#     #key,value,detail
#     default_ini_dic=dict(zip(df["key"], df["value"]))
#     default_detail_dic=dict(zip(df["key"], df["detail"]))
#     return default_ini_dic, default_detail_dic

def joinstatus_display(host, password, port):
    """入退出状況を表示する"""
    #ShowPlayersはバグって続きが取得できないのでコメントアウト
    logger.debug("start: " + str(sys._getframe().f_code.co_name))
    # try:
    #     with mcrcon.MCRcon(host, password, port) as client:
    #         command="ShowPlayers"
    #         logger.info("Command sent: "+command)
    #         response = client.command(command)
    #         logger.info("Server response: "+response)

    #         command="Broadcast joined:"
    #         left:
    #         logger.info("Command sent: "+command)
    #         response = client.command(command)
    #         logger.info("Server response: "+response)

def worldsave(host, port, password, process_name_to_check_list, process_path_to_start,flag_shutdown=False,time_shutdown_sec=60,flag_reboot=True):
    """6時は再起動するが、他はアップデートがある場合のみ再起動する"""
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    global update_in_progress
    current_hour = datetime.now().hour

    if (current_hour==6 and flag_reboot) or isNeedUpdate():
        #6時かつrebootフラグon、もしくはアップデートありのため、アップデートして再起動
        if current_hour==6:logger.info("6時のため、サーバーアップデートを実施")
        else:logger.info("アップデートありのため、サーバーアップデートを実施")
        update_in_progress = True
        try:
            if is_process_running(process_name_to_check_list):
                with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                    command="Info"
                    logger.info("Command sent: "+command)
                    response = client.command(command)
                    logger.info("Server response: "+response)
                time.sleep(1)

                #ShowPlayersはバグって続きが取得できないのでコメントアウト
                # with mcrcon.MCRcon(host, password, port) as client:
                #     command="ShowPlayers"
                #     logger.info("Command sent: "+command)
                #     response = client.command(command)
                #     logger.info("Server response: "+response)
                # time.sleep(1)
                
                with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                    command="Save"
                    logger.info("Command sent: "+command)
                    response = client.command(command)
                    logger.info("Server response: "+response)
                time.sleep(1)
                
                with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                    if flag_shutdown:
                        command="Broadcast Shutdown_has_been_scheduled_for_"+str(time_shutdown_sec)+"_seconds_later."
                        #メンテナンスのため、60秒後にシャットダウンします。ログアウトしてください。"
                    else:
                        command="Broadcast Reboot_has_been_scheduled_for_"+str(time_shutdown_sec)+"_seconds_later."
                        #ワールド保存のため、60秒後に再起動します。ログアウトしてください。"
                    logger.info("Command sent: "+command)
                    response = client.command(command)
                    logger.info("Server response: "+response)

                if time_shutdown_sec<1:
                    time.sleep(1)
                else:
                    time.sleep(time_shutdown_sec)

                with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                    command="Save"
                    logger.info("Command sent: "+command)
                    response = client.command(command)
                    logger.info("Server response: "+response)
                time.sleep(1)
                
                with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                    if flag_shutdown:
                        # command="Shutdown 10 メンテナンスのため、10秒後にシャットダウンします。ログアウトしてください。"
                        command="Shutdown 10 "
                    else:
                        # command="Shutdown 10 ワールド保存のため、10秒後に再起動します。ログアウトしてください。"
                        command="Shutdown 10 "
                    logger.info("Command sent: "+command)
                    response = client.command(command)
                    logger.info("Server response: "+response)

                for i in range(60):
                    if not is_process_running(process_name_to_check_list):break
                    time.sleep(1)
                else:
                    #終了しないので、強制的に落とす
                    kill_palserver(process_name_to_check_list)
                    for i in range(60):
                        if not is_process_running(process_name_to_check_list):break
                        time.sleep(1)
                    else:
                        #タスクキルでも落ちない場合
                        logger.info("タスクキルしても落とせなかったのでコミット等を行いません")
                        return 1
            zip_directory(zip_dir)
            git_commit(repo_directory)
            worldupdate(steamcmd_dir_path, repo_directory)
            git_commit(repo_directory,"updated")
            start_process(process_path_to_start)
            return 0
        except Exception as e:
            logger.info("エラー")
            errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
            logger.exception(e)
            return 1
        finally:
            update_in_progress = False
    else:
        #アップデートなしか、取得できないため、再起動しない
        logger.info("サーバーをダウンさせずにワールドのコピーを取得します。")
        try:
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                command="Info"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)
            time.sleep(1)
            
            #ShowPlayersはバグって続きが取得できないのでコメントアウト
            # with mcrcon.MCRcon(host, password, port) as client:
            #     command="ShowPlayers"
            #     logger.info("Command sent: "+command)
            #     response = client.command(command)
            #     logger.info("Server response: "+response)
            # time.sleep(1)
            
            with mcrcon.MCRcon(host, password, port,timeout=60) as client:
                command="Save"
                logger.info("Command sent: "+command)
                response = client.command(command)
                logger.info("Server response: "+response)
            time.sleep(2)

            zip_directory(zip_dir)
            return 0
        except mcrcon.MCRconException as e:
            logger.info("エラー")
            errortxt = ", ".join(list(traceback.TracebackException.from_exception(e).format()))
            logger.exception(e)
            return 1


def main():
    logger.debug("start: "+str(sys._getframe().f_code.co_name))
    logger.info(print_txt)
    logger.info("キーボードで 'q' が押されたら終了")

    #初回起動チェック
    processcheck(process_name_to_check_list, process_path_to_start,True)

    # 1分ごとに実行
    schedule.every().minute.at(":30").do(lambda: processcheck(process_name_to_check_list, process_path_to_start))
    
    # 30分ごとに実行
    # アップデートがあるならアップデートして再起動
    # 6時は強制アップデート
    # schedule.every().hour.at(":00").do(lambda: worldsave_hour(server_host, server_port, rcon_password, process_name_to_check, process_path_to_start))
    # schedule.every().hour.at(":10").do(lambda: worldsave_half_hour(server_host, server_port, rcon_password))
    # schedule.every().hour.at(":20").do(lambda: worldsave_half_hour(server_host, server_port, rcon_password))
    # schedule.every().hour.at(":30").do(lambda: worldsave_half_hour(server_host, server_port, rcon_password))
    # schedule.every().hour.at(":40").do(lambda: worldsave_half_hour(server_host, server_port, rcon_password))
    # schedule.every().hour.at(":50").do(lambda: worldsave_half_hour(server_host, server_port, rcon_password))
    schedule.every().hour.at(":00").do(lambda: worldsave(server_host, server_port, rcon_password, process_name_to_check_list, process_path_to_start,flag_shutdown=False,time_shutdown_sec=60,flag_reboot=flag_reboot))
    schedule.every().hour.at(":30").do(lambda: worldsave(server_host, server_port, rcon_password, process_name_to_check_list, process_path_to_start,flag_shutdown=False,time_shutdown_sec=60,flag_reboot=flag_reboot))
    

    while True:
        schedule.run_pending()
        if keyboard.is_pressed('q'):
            logger.info("終了します。")
            break
        time.sleep(1)



if __name__ == '__main__':
    main()
