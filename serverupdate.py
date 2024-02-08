"""
サーバーをアップデートするツール
"""

from com import getLogger
import os
from configmanager import ConfigManager
import logging
logger=logging.getLogger(__name__)

CL_Con=ConfigManager()
process_name_to_check = CL_Con.get("process_name_to_check")
process_path_to_start = CL_Con.get("process_path_to_start")

server_host = CL_Con.get("server_host")
server_port = int(CL_Con.get("server_port"))
rcon_password = CL_Con.get("rcon_password")

steamcmd_dir_path = CL_Con.get("steamcmd_dir_path")
repo_directory = CL_Con.get("repo_directory")

from palserver_monitor import worldsave_safe, worldupdate, git_commit

def main():
    worldsave_safe(server_host, server_port, rcon_password, process_name_to_check, process_path_to_start, True)
    logger.info("サーバー終了完了！！")

    worldupdate(steamcmd_dir_path, repo_directory,flag_manual=True)
    git_commit(repo_directory,"updated")

    logger.info("サーバーアップデート完了！！")

    os.system('PAUSE')

if __name__ == '__main__':
    main()