# 構成

## 環境変数

QuantumLeap を構成するには、次の環境変数を使用できます:

| 変数               | 説明                       |
| -------------------|----------------------------|
| `CRATE_HOST`       | CrateDB ホスト             |
| `CRATE_PORT`       | CrateDB ポート             |
| `DEFAULT_LIMIT`    | クエリが取得できる最大行数 |
| `POSTGRES_HOST`    | PostgreSQL ホスト          |
| `POSTGRES_PORT`    | PostgreSQL ポート          |
| `POSTGRES_DB_NAME` | PostgreSQL デフォルト db   |
| `POSTGRES_DB_USER` | PostgreSQL ユーザ          |
| `POSTGRES_DB_PASS` | PostgreSQL パスワード      |
| `POSTGRES_USE_SSL` | `t` または `f` SSL 有効化  |
| `REDIS_HOST`       | Redis ホスト               |
| `REDIS_PORT`       | Redis ポート               |
| `USE_GEOCODING`    | `True` または `False` ジオコーディングの有効化または無効化 |
| `QL_CONFIG`        | テナント構成のパス名       |
| `LOGLEVEL`         | すべてのサービスのログ・レベルを定義 (`DEBUG`, `INFO`, `WARNING` , `ERROR`) |

## 異なるテナントごとのデータベースの選択

QuantumLeap は、さまざまな時系列データベースを使用して、NGSI データを
保持およびクエリできます。 現在、クエリ機能が Timescale でまだ利用
できませんが、[CrateDB][crate] と [Timescale][timescale] の両方が、
バックエンドとしてサポートされています。

設定が提供されない場合、QuantumLeap は CrateDB が使用するバックエンド
であると想定し、着信した NGSI データをすべて格納します。ただし、YAML
設定ファイルを使用して、特定のテナントに対して異なるバックエンドを構成
できます。この機能を使用するには、以下の環境変数を設定する必要が
あります :

* `QL_CONFIG`: QuantumLeap YAML 設定ファイルの絶対パス名。設定されて
  いない場合は、Crate バックエンドのみが使用可能なデフォルト構成が
  使用されます

YAML 設定ファイルは、どのテナントにどのバックエンドを使用するか、および
ファイルで明示的に言及されていない他のテナントに使用するデフォルトの
バックエンドを指定します。YAML 設定の例を次に示します :

    tenants:
        t1:
            backend: Timescale
        t2:
            backend: Crate
        t3:
            backend: Timescale

    default-backend: Crate

この構成では、テナント `t1` または `t3` に着信するすべての NGSI
エンティティは Timescale に格納されますが、テナント `t2` は Crate
を使用します。 `t1`, ` t2` または `t3` 以外のテナントは、デフォルトの
Crate バックエンドになります。




[crate]: ./crate.md
    "QuantumLeap Crate"
[timescale]: ./timescale.md
    "QuantumLeap Timescale"
