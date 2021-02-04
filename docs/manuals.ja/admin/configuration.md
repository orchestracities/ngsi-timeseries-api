# 構成

## 環境変数

QuantumLeap を構成するには、次の環境変数を使用できます:

| 変数               | 説明                                                                                                  |
| -------------------|-------------------------------------------------------------------------------------------------------|
| `CRATE_HOST`       | CrateDB ホスト                                                                                        |
| `CRATE_PORT`       | CrateDB ポート                                                                                        |
| `DEFAULT_LIMIT`    | クエリが取得できる最大行数                                                                            |
| `KEEP_RAW_ENTITY`  | 元のエンティティ・データを保存するかどうか                                                            |
| `POSTGRES_HOST`    | PostgreSQL ホスト                                                                                     |
| `POSTGRES_PORT`    | PostgreSQL ポート                                                                                     |
| `POSTGRES_DB_NAME` | PostgreSQL デフォルト db                                                                              |
| `POSTGRES_DB_USER` | PostgreSQL ユーザ                                                                                     |
| `POSTGRES_DB_PASS` | PostgreSQL パスワード                                                                                 |
| `POSTGRES_USE_SSL` | `t` または `f` SSL 有効化                                                                             |
| `REDIS_HOST`       | Redis ホスト                                                                                          |
| `REDIS_PORT`       | Redis ポート                                                                                          |
| `USE_GEOCODING`    | `True` または `False` ジオコーディングの有効化または無効化                                            |
| `QL_CONFIG`        | テナント構成のパス名                                                                                  |
| `QL_DEFAULT_DB`    | デフォルト・バックエンド: `timescale` また `crate`                                                    |
| `CRATE_WAIT_ACTIVE_SHARDS` | 書き込み操作を続行するためにアクティブにする必要があるシャード・コピーの数を指定します。デフォルトは、`1` です。関連する [crate のドキュメント](https://crate.io/docs/crate/reference/en/4.3/sql/statements/create-table.html#write-wait-for-active-shards) を参照してください |
| `USE_FLASK`        | flask server (Dev のみ) または gunicorn を使用する場合は `True` または `False`。 デフォルトは `False` |
| `QL_CONFIG`        | テナント構成のパス名                                                                                  |
| `LOGLEVEL`         | すべてのサービスのログ・レベルを定義 (`DEBUG`, `INFO`, `WARNING` , `ERROR`)                           |

### 注意

* `DEFAULT_LIMIT`. この変数は、クエリ操作がデータベースからフェッチして
  クライアントに返すことができる行の上限 L を指定します。 実際の行数は、Lと
  クライアント指定の制限の最小値、またはクライアントが制限を指定しなかった
  場合は L になります。この変数を介して設定されていない場合、L はデフォルトで
  10,000になります。この変数は、クエリ・エンドポイントへの各 AP I呼び出しで
  読み込まれるため、動的に設定でき、後続のすべてのクエリ操作に影響します。
  設定する可変文字列値は整数に変換可能である必要があります。変換できない場合
  は、代わりにデフォルト値の10,000が使用されます。
* `KEEP_RAW_ENTITY`. true の場合、ノーティファイされた各エンティティは、対応
  するエンティティ・テーブルの追加の列に JSON として完全に保存されます。
  (これにより、テーブルに最大10倍のストレージが必要になる場合があります。)
  false の場合、JSON から表形式への変換が失敗した場合にのみ JSON が保存され
  ます (前述のとおり)。通常、これはノーティファイされたエンティティで発生
  します。以前にノーティファイされた属性が含まれ、そのタイプは以前とは
  異なります。この変数は、ノーティファイ・エンドポイントへの API 呼び出し
  ごとに読み込まれるため、動的に設定でき、後続のすべての挿入操作に影響します。
  次の (大文字と小文字を区別しない) 値はいずれも true として解釈されます:
  'true', 'yes', '1', 't', 'y'。それ以外は false と見なされます。これは、
  変数が設定されていない場合のデフォルト値でもあります。

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

```yaml
tenants:
    t1:
        backend: Timescale
    t2:
        backend: Crate
    t3:
        backend: Timescale

default-backend: Crate
```

この構成では、テナント `t1` または `t3` に着信するすべての NGSI
エンティティは Timescale に格納されますが、テナント `t2` は Crate
を使用します。 `t1`, `t2` または `t3` 以外のテナントは、デフォルトの
Crate バックエンドになります。

[crate]: ./crate.md
    "QuantumLeap Crate"
[timescale]: ./timescale.md
    "QuantumLeap Timescale"
