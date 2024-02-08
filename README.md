# パルワールドサーバー管理プログラム

このプログラムは、パルワールドサーバーの運用をサポートするための管理ツールです。以下に、主な機能と使用法を示します。

時間ができ次第、readmeやiniは改善する予定です。

## 注意点

- windowsです
- gitリポジトリが設定のrepo_directoryに作成してある前提です
- rconが有効化されていることが前提です
- rconがあまり安定していません
- steamcmdもあまり安定していません

## 機能

1. **プロセス監視と自動起動**
   - プログラムは毎分、実行中のプロセスを監視し、サーバープロセスが停止している場合は自動的に起動します。

2. **ワールドの自動バックアップ**
   - 30分ごとに、ワールドデータをzip形式で圧縮し、別の場所にコピーします。

3. **サーバーアップデートと自動コミット**
   - 6時間ごとに、サーバーをシャットダウンし、アップデートがあれば適用します。その後、ワールドデータをzip化して別の場所にコピーし、Gitにコミットします。この間、プロセス監視は一時停止します。

4. **強制的なサーバーアップデート**
   - 毎日6時に、サーバーを強制的にアップデートします。この間もプロセス監視は停止します。

## 使用法

1. dist/palserver_monitor.iniを確認し、必要に応じて調整します。
2. dist/palserver_monitor.exeを実行すると、自動的にサーバーの監視と必要なアクションが開始されます。

## その他使用方法

1. dist/serverend.exeはサーバーを手動終了するプログラムです。
2. dist/serverupdate.exeはサーバーを手動アップデートするプログラムです。

## 設定

プログラムの設定は、`dist/palserver_monitor.ini`ファイルを編集することで可能です。設定ファイルには以下の項目が含まれます。

- process_name_to_check = PalServer.exe
  - プロセス名チェックに使用するexe名
- process_path_to_start = C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer\PalServer.exe
  - プロセスダウン等を検知したときに起動するプログラム
- server_host = 127.0.0.1
  - ホストip(自分しか想定していないので、変更しないでください)
- server_port = 25585
  - サーバーのrconポート
- rcon_password = password
  - rconのパスワード(AdminPasswordに設定した項目)
- zip_dir = C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer\Pal\Saved
  - 30分ごとにzip化して保存するディレクトリ
- repo_directory = C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer
  - git initしてある前提のディレクトリ
- steamcmd_dir_path = C:\Users\aaaaa\temp\steamcmd
  - steamcmdがあるディレクトリ
- steamcmd_exe_path = C:\Users\aaaaa\temp\steamcmd\steamcmd.exe
  - steamcmdのフルパス
- backup_max_age_days = 10
  - どのくらいの日数zipファイルを保存しておくか
