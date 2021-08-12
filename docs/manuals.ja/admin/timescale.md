# Timescale

[Timescale][timescale] は、NGSI エンティティの時系列を格納するバック
エンドとして QuantumLeap で使用できる時系列データベースの1つです。
[データベース選択のセクション][admin.db] で説明しているように、永続化
されるエンティティを所有するテナントに応じて、使用するストレージ・
バックエンド (Crate または Timescale) を実行時に動的に選択できます。
さらに、QuantumLeap には、Timescale バックエンドのセットアップを自動化
し、Crate から Timescale への移行スクリプトを生成するツールが付属して
います。詳細は、[データ移行のセクション][admin.dm]にあります。

## QuantumLeap Timescale DB のセットアップ

Timescale バックエンドの使用を開始するには、動作する PostgreSQL の
インストールが必要です。特に、QuantumLeap には、**Timescale および
PostGIS 拡張機能がすでにインストールされている PostgreSQL server 10
以上**が必要です。`timescale-container/test` の Docker ファイルを
使用して、QuantumLeap が接続できる Timescale サーバ・バックエンドを
すばやくスピンアップできますが、実稼働環境のデプロイでは、より洗練
されたセットアップが必要になる可能性があります。たとえば、高可用性の
ために PostgreSQL を構成。

Timescale が稼働したら、QuantumLeap DB をブートストラップする必要が
あり、Crate から一部のデータを移行することもできます。QuantumLeap
には、プロセスのほとんどのステップを自動化できる自己完結型の Python
スクリプトが付属しています。スクリプト・ファイルの名前は
`quantumleap-db-setup` で、`timescale-container` ディレクトリに
あります。次の3つのことを順番に実行します :

1. QuantumLeap データベースが存在しない場合は、ブートストラップします。
   QuantumLeap のデータベースを作成し、必要なすべての拡張子と最初の
   QuantumLeap ロールを追加します。指定された QuantumLeap DB が既に
   存在する場合、ブートストラップのフェーズはスキップされます

2. 指定された init ディレクトリで見つかった SQL スクリプトを実行
   します。デフォルトは `./ql-db-init` です。このディレクトリ・ツリー
   内の `.sql` ファイルをピックアップし、昇順のアルファベット順に
   各ファイルを実行し、エラーが発生した最初のファイルで停止します。
   その場合、スクリプトは終了します

3. 上記の init ディレクトリにあるデータ・ファイルをロードします。
   データ・ファイルは、init ディレクトリ・ツリーにある拡張子が
   `.csv` のファイルです。各データ・ファイルには、QuantumLeap
   データベースのテーブルにロードされる CSV 形式のレコードのリストが
   含まれている必要があります。`.csv` 拡張子のないファイル名は、
   データがロードされるテーブルの FQN であると見なされますが、
   列の仕様は、ファイル内にあると予想される CSV ヘッダの名前で
   指定されます。データ・ファイルはアルファベット順に順番に読み込まれ、
   エラーが発生した最初のファイルで停止します。その場合、スクリプトは
   終了します。  

(2) と (3) はデータの移行に最も関連しています (詳細については以下の
セクションで説明します) が、スクリプトは任意の SQL ステートメントを
実行するためにも使用できます。前述の Docker compose ファイルは、
Timescale コンテナ (PostGIS を使用) と、inittime として、
`timescale-container/test/ql-db-init` を使用してスクリプトを実行する
別のコンテナをスピンアップし、動作するTimescale DB、および、いくつかの
テーブル、テストデータを提供します。

## Timescale バックエンドの使用

新しく作成された QuantumLeap DB を含む Postgres + Timescale + PostGIS
サーバがあれば、QuantumLeap を DBサーバに接続する準備ができています。
そのためには、いくつかの環境変数を設定し、YAML ファイルを編集する必要が
あります。使用する環境変数は次のとおりです :

* `POSTGRES_HOST` : Timescale サーバのホスト名または IP アドレス。
  指定しない場合のデフォルトは `timescale` です
* `POSTGRES_PORT` : 接続するサーバのポート。デフォルトは `5432` です
* `POSTGRES_DB_NAME` : QuantumLeap DB の名前。デフォルトは
  `quantumleap` です
* `POSTGRES_DB_USER` : QuantumLeap が接続に使用する DB ユーザ。
  デフォルトは `quantumleap` です
* `POSTGRES_DB_PASS` : 上記のユーザのパスワード。デフォルトは `*` です
* `POSTGRES_USE_SSL` : QuantumLeap は SSL を使用して PostgreSQL に
  接続する必要がある場合、この変数を `true`, `yes`, `1`, `t` のいずれかに
  設定します。他の値を指定するか、変数を設定しなければ、プレーン TCP
  接続を使用します
* `QL_CONFIG` : QuantumLeap YAML 設定ファイルの絶対パス名。設定されて
  いない場合は、Crate バックエンドのみが使用可能なデフォルト構成が
  使用されます。バックエンドと YAML 設定を選択する方法の詳細については、
  [データベース選択のセクション][admin.db] を参照してください

[admin.db]: ./configuration.md
    "QuantumLeap Configuration"
[admin.dm]: ./dataMigration.md
    "QuantumLeap Data Migration"
[postgres]: https://www.postgresql.org
    "PostgreSQL Home"
[postgis]: https://postgis.net/
    "PostGIS Home"
[timescale]: https://www.timescale.com
    "Timescale Home"
