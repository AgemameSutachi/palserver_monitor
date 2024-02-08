import os
import configparser
import logging
logger = logging.getLogger(__name__)

default_config_dic={
    "process_name_to_check": "PalServer.exe",
    "process_path_to_start": "C:\\Users\\aaaaa\\steamcmd\\steamapps\\common\\PalServer\\PalServer.exe",
    "server_host":"127.0.0.1",
    "server_port":"25585",
    "rcon_password":"password",
    "zip_dir":"C:\\Users\\aaaaa\\steamcmd\\steamapps\\common\\PalServer\\Pal\\Saved",
    "repo_directory":"C:\\Users\\aaaaa\\steamcmd\\steamapps\\common\\PalServer",
    "steamcmd_dir_path":"C:\\Users\\aaaaa\\steamcmd",
    "steamcmd_exe_path":"C:\\Users\\aaaaa\\steamcmd\\steamcmd.exe",
    "backup_max_age_days":"10",
    "joinstatuscsv_path":"joinStatus.csv"
}

class ConfigManager():
    """設定ファイルを管理するクラス"""
    def __init__(self,config_path: str ="palserver_monitor.ini"):
        self.config_dic=default_config_dic
        self.config_path=config_path
        if not os.path.exists(config_path):
            logger.info("設定ファイルがないのでテンプレートを作成: "+self.config_path)
            self.config_generator()
        else:
            logger.info("設定ファイル読み込み: "+self.config_path)
        config_ini = configparser.ConfigParser()
        config_ini.read(config_path, encoding='cp932')
        read_default = config_ini['DEFAULT']
        for key in self.config_dic.keys():
            self.config_dic[key] = read_default.get(key,self.config_dic[key])
            logger.info(key+": "+str(self.config_dic[key]))

    def config_generator(self):
        try:
            config = configparser.ConfigParser()
            config['DEFAULT'] = default_config_dic
            with open(self.config_path, 'w',encoding='cp932') as configfile:
                config.write(configfile)
        except:
            logger.error("設定ファイル作成失敗: "+self.config_path)
            raise
    
    def get(self,key):
        return self.config_dic.get(key)