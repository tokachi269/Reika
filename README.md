# Reika

saki7氏の[Reika](https://github.com/SETNAHQ/Reika)をpythonで実装

## 概要

steamワークショップのURLが張られると、URL先の情報を取得し表示

## 導入

Botを起動し、招待が終わったら次のコマンドを実行してください。  
（サーバー管理者のみ可能）
`r/set-gameid (gameid)`

例（Cities:Skylines）`r/set-gameid 255710`
ストアのURLよりゲームIDを確認してください。
https://store.steampowered.com/app/255710/Cities_Skylines/

## フォーク元からの大きな変更点

### 検索機能の実装

`s/ word`でsteamワークショップでの検索結果を表示

コードに修正（改善）すべき点を見つけた場合はPull RequestやIssuesから報告をお願いします。
