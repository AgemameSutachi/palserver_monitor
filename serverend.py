"""
安全にシャットダウンするツール
"""

from com import getLogger
import os
import sys
from configmanager import ConfigManager
import logging
logger=logging.getLogger(__name__)

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

from palserver_monitor import worldsave_safe

def isnum(num):
    try:
        tmp=int(num)
        return 1
    except:
        return 0

def main():
    try:
        if len(sys.argv) > 2 and isnum(sys.argv[2]): # 確認：引数が3つ以上あるかどうか
            worldsave_safe(server_host, server_port, rcon_password, process_name_to_check_list, process_path_to_start, True, int(sys.argv[2]))
        else:
            worldsave_safe(server_host, server_port, rcon_password, process_name_to_check_list, process_path_to_start, True)
        logger.info("サーバー終了完了！！")
        if len(sys.argv) > 1 and sys.argv[1] == '1':
            logger.debug("exit 0")
            sys.exit(0)
        else:
            input("Press Enter to continue...")
    except:
        if len(sys.argv) > 1 and sys.argv[1] == '1':
            logger.debug("exit 1")
            sys.exit(1)
        else:
            input("Press Enter to continue...")
if __name__ == '__main__':
    main()