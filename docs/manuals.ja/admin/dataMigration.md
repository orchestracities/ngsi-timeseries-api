# Data Migration (データ・マイグレーション)

QuantumLeap へのデータの移行を支援するいくつかのツールが利用可能です。

## QuantumLeap Crate からTimescale への移行

QuantumLeap は、QuantumLeap CrateDB データベースから QuantumLeap
Timescale データベースへのテーブルの移行を支援する自己完結型の Python
スクリプトを提供します。 スクリプトは `timescale-container`
ディレクトリにあり、 `crate-exporter.py` と呼ばれます。指定された
Crate テーブルの行をエクスポートし、`stdout` で、そのデータを Timescale
にインポートするために必要なすべての SQL ステートメントを生成します。
これらには、必要に応じて PostgreSQL で対応するスキーマ、テーブル、
ハイパーテーブルを作成することが含まれます。スクリプトは DDL
ステートメントを生成することに注意してください。実行すると、Crate
テーブルに格納された行に対応する NGSI エンティティを見ると QuantumLeap
Timescale バックエンドが生成したものとまったく同じテーブル構造になります。

以下に使用例を示します :

    $ python crate-exporter.py --schema mtyoutenant --table etdevice \
        > mtyoutenant.etdevice-import.sql

ここでは、Crate table `mtyoutenant.etdevice` のすべての行をエクスポート
します。生成されたファイルには、テーブルを再作成してデータを Timescale
に挿入するためのすべての SQL ステートメントが含まれています。
[Timescale section][ts-admin] で説明されているように、Timescale で
QuantumLeap DB をブートストラップするときにデータが自動的に移行される
ように、このファイルを `quantumleap-db-setup` スクリプトの init
ディレクトリに置くことができます。

デフォルトでは、スクリプトは Crate テーブルのすべての行をエクスポート
しますが、次のように、`--query` 引数を使用してクエリを指定し、目的の
サブセットのみを選択することもできます。

    $ python crate-exporter.py --schema mtyoutenant --table etdevice --query \
        "SELECT * FROM mtyoutenant.etdevice where time_index > '2019-04-15';"

[ts-admin]: ./timescale.md
    "QuantumLeap Timescale"
