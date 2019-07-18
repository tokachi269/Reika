# Reika
[![Build Status](https://travis-ci.org/takana-v/reika-python.svg?branch=master)](https://travis-ci.org/takana-v/reika-python)

saki7氏の[Reika](https://github.com/SETNAHQ/Reika)をpythonで実装

## 概要

steamワークショップのURLが張られると、URL先の情報を取得し表示

## 導入

以下のURLから招待できます。
https://discordapp.com/api/oauth2/authorize?client_id=596897770728849418&permissions=313344&scope=bot

招待が終わったら次のコマンドを実行してください。  
（サーバー管理者のみ可能）
`r/set-gameid (gameid)`

例（Cities:Skylines）`r/set-gameid 255710`
ストアのURLよりゲームIDを確認してください。
https://store.steampowered.com/app/255710/Cities_Skylines/

## フォーク元からの大きな変更点

### 検索機能の実装

`s/ word`で[steamワークショップ](https://steamcommunity.com/app/255710/workshop/)での検索結果を表示
`s/author word`で作者名で絞込可能

### ワークショップ以外のページに対応

スクリーンショット、作品、動画のページではサブスクライブの代わりにgood数を表示


コードに修正（改善）すべき点を見つけた場合はPull RequestやIssuesから報告をお願いします。