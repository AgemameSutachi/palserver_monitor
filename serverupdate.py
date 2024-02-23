"""
サーバーをアップデートするツール
"""

from com import log_decorator
from configmanager import ConfigManager
import logging
import ssl
import certifi

# from slackapi import textpost, imagepost, imagepost_from_url

logger = logging.getLogger(__name__)
ssl_context = ssl.create_default_context(cafile=certifi.where())
import os

default_config_dic={
    # "process_name_to_check": "PalServer.exe",
    "process_path_to_start": "C:\\Users\\aaaaa\\steamcmd\\steamapps\\common\\PalServer\\PalServer.exe",
    # "server_host":"127.0.0.1",
    "server_port":"25585",
    "rcon_password":"password",
    # "zip_dir":"C:\\Users\\aaaaa\\steamcmd\\steamapps\\common\\PalServer\\Pal\\Saved",
    # "repo_directory":"C:\\Users\\aaaaa\\steamcmd\\steamapps\\common\\PalServer",
    # "steamcmd_dir_path":"C:\\Users\\aaaaa\\steamcmd",
    # "steamcmd_exe_path":"C:\\Users\\aaaaa\\steamcmd\\steamcmd.exe",
    "backup_max_age_days":"10",
    # "joinstatuscsv_path":"joinStatus.csv",
    "flag_reboot":True,
}

Cl_Con = ConfigManager(
    default_dic=default_config_dic, config_path="./palserver_monitor.ini", encoding="cp932"
)
# C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer\PalServer.exe
process_path_to_start = Cl_Con.get("process_path_to_start")
# PalServer.exe
process_name_to_check_list = ["PalServer.exe","PalServer-Win64-Test-Cmd.exe"]
# 127.0.0.1
server_host = "127.0.0.1"
# 25585
server_port = int(Cl_Con.get("server_port"))
# password
rcon_password = Cl_Con.get("rcon_password")
# C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer\Pal\Saved
zip_dir = os.path.join(os.path.dirname(process_path_to_start),"Pal","Saved")
# C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer
repo_directory = os.path.dirname(process_path_to_start)
# C:\Users\aaaaa\temp\steamcmd
steamcmd_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(repo_directory)))
# C:\Users\aaaaa\temp\steamcmd\steamcmd.exe
steamcmd_exe_path = os.path.join(steamcmd_dir_path,"steamcmd.exe")
#10
backup_max_age_days=int(Cl_Con.get("backup_max_age_days"))
#True
if Cl_Con.get("flag_reboot","True") in ["0","FALSE","False","false"]:
    flag_reboot=False
else:
    flag_reboot=True

from palserver_monitor import worldsave_safe, worldupdate, git_commit

def main():
    worldsave_safe(server_host, server_port, rcon_password, process_name_to_check_list, process_path_to_start, True)
    logger.info("サーバー終了完了！！")

    worldupdate(steamcmd_dir_path, repo_directory,flag_manual=True)
    git_commit(repo_directory,"updated")

    logger.info("サーバーアップデート完了！！")

    os.system('PAUSE')

if __name__ == '__main__':
    main()