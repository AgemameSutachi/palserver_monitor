"""
安全にシャットダウンするツール
"""

from com import getLogger
import os
import sys
from configmanager import ConfigManager
import logging
logger=logging.getLogger(__name__)

CL_Con=ConfigManager()
process_name_to_check = CL_Con.get("process_name_to_check")
process_path_to_start = CL_Con.get("process_path_to_start")

server_host = CL_Con.get("server_host")
server_port = int(CL_Con.get("server_port"))
rcon_password = CL_Con.get("rcon_password")

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
            worldsave_safe(server_host, server_port, rcon_password, process_name_to_check, process_path_to_start, True, int(sys.argv[2]))
        else:
            worldsave_safe(server_host, server_port, rcon_password, process_name_to_check, process_path_to_start, True)
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