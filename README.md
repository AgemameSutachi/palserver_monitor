# パルワールドサーバー管理プログラム

このプログラムは、パルワールドサーバーの運用をサポートするための管理ツールです。以下に、主な機能と使用法を示します。

時間ができ次第、readmeは改善する予定です。

## 注意点

- windowsです
- gitのパスが通っていることが前提です
- rconが有効化されていることが前提です
- rconがあまり安定していません
- steamcmdもあまり安定していません

## 機能

1. **プロセス監視と自動起動**
   - プログラムは毎分、パルワールドのプロセスを監視し、プロセスが停止している場合は自動的に起動させます。

2. **ワールドの自動バックアップ**
   - 30分ごとに、アップデートを取得できたらシャットダウンして適用します。その後、ワールドデータをzip形式で圧縮コピーし、全体をGitにコミットします。その後、サーバーを再起動します。この間、プロセス監視は一時停止します。
   - 30分ごとに、アップデートを取得できなかったら、ワールドデータをzip形式で圧縮コピーのみします。

3. **強制的なサーバーアップデート**
   - 毎日6時に、サーバーをシャットダウンし、強制的にアップデートします。その後、ワールドデータをzip形式で圧縮コピーし、全体をGitにコミットします。この間、プロセス監視は一時停止します。

## 使用法

1. dist/palserver_monitor.iniを確認し、必要に応じて調整します。
2. dist/palserver_monitor.exeを実行すると、自動的にサーバーの監視と必要なアクションが開始されます。
3. "q"ボタンを長押しでプログラムを終了できます(終了しない場合はctrl+cで強制終了してください)

## その他使用方法

1. dist/serverend.exeはサーバーを手動終了するプログラムです。
2. dist/serverupdate.exeはサーバーを手動アップデートするプログラムです。

## ワールドデータがバグで消えてしまった場合の復帰方法

- zipファイルを使用して復帰させる("C:/Users/aaaaa/steamcmd/steamapps/common/PalServer/Pal/Saved")
- gitから復帰させる(C:/Users/aaaaa/steamcmd/steamapps/common/PalServer")

## 設定

プログラムの設定は、`dist/palserver_monitor.ini`ファイルを編集することで可能です。設定ファイルには以下の項目が含まれます。

- process_path_to_start = C:\Users\aaaaa\temp\steamcmd\steamapps\common\PalServer\PalServer.exe
  - プロセスダウン等を検知したときに起動するプログラム(パルワールドのexeを指定)
- server_port = 25585
  - サーバーのrconポート
- rcon_password = password
  - rconのパスワード(AdminPasswordに設定した項目)
- backup_max_age_days = 10
  - どのくらいの日数zipファイルを保存しておくか
- flag_reboot
  - 毎日6時に再起動するかどうか(Falseにしてもアップデートを検出したら再起動します)
