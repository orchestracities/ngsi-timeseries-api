# QuantumLeap の使用

まず、QuantumLeap とその補完サービスを稼動させる必要があります。手順については、
[インストール・マニュアル](../admin/installing.md)を参照してください。

次に、 興味のある履歴データを持つ
[エンティティ・タイプ](https://orioncontextbroker.docs.apiary.io/#introduction/specification/terminology)
ごとに、
[NGSIv2 サブスクリプション](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
を通じて Orion Context Broker を QuantumLeap に接続する必要があります。

Orion の専門家ではないのですか？問題はありません。QuantumLeap の API
を使用してサブスクリプションを作成できます。
ただし、サブスクリプションと通知の仕組みの基本を理解しておく必要がありますので、
[ドキュメント](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#ubscriptions)
を読む時間を取ってください 。

サブスクリプションがアクティブで正しく設定され、通知内のエンティティが NGSI
に準拠している限り、各エンティティ型の履歴データが QuantumLeap のデータベースに
追加されます。

サブスクリプションが削除された場合、またはそのステータスが変更された場合、
その後データは追加されません。 ただし、QuantumLeap のデータベースに格納されている
以前のデータは、QuantumLeap に格納されているデータを削除するために API
を使用して外部から削除されるまで保持されます。

したがって、要約すると、使用フローは次のようになります...

- 関心のあるエンティティ・タイプごとに Orion のサブスクリプションを作成します
- 通常どおり Orion にエンティティを挿入/更新します
- 履歴データは QuantumLeap のデータベースに保存されます。

各ステップの詳細を見てみましょう。

## Orion サブスクリプション <a name="orion-subscription"></a>

前述のように、Orion と QuantumLeap のリンクは、
作成する必要があるサブスクリプションによって確立されます。 したがって、NGSIv2
サブスクリプションのメカニズムがどのように機能するかを
よく理解することが重要です。これは
[Orionのドキュメント](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
の対応するセクションで詳しく説明されています。

サブスクリプションを作成するために、QuantumLeap は
[/subscribe で、ここ](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
にドキュメント化された API エンドポイントを提供します。

また、Orion
に直接アクセスして、好きなようにサブスクリプションを作成することもできます。
Orion-QuantumLeap リンクを確立するために Orion
で作成する必要があるサブスクリプションのペイロードの例を次に示します。

```json
    {
        "description": "Test subscription",
        "subject": {
            "entities": [
            {
                "idPattern": ".*",
                "type": "Room"
            }
            ],
            "condition": {
                "attrs": [
                "temperature"
                ]
            }
        },
        "notification": {
            "http": {
                "url": "http://quantumleap:8668/v2/notify"
            },
            "attrs": [
            "temperature"
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 5
    }
```

サブスクリプションから注目すべき重要なことは :

- 通知は完全な

[NGSI JSON エンティティ](http://docs.orioncontextbroker.apiary.io/#introduction/specification/json-attribute-representation)
の表現形式で行われなければなりません。
[簡略化されたエンティティ表現](http://docs.orioncontextbroker.apiary.io/#introduction/specification/simplified-entity-representation)
のような他の形式は、適切な変換を行うために QuantumLeap
が要求する属性型に関する情報が不足しているため、 QuantumLeap
によってサポートされていません。これは、`"attrsFormat": "keyValues"`
のようなオプションを使用しないことを意味します。

- `"url"` サブスクリプションのフィールドは、Orion

が通知を送信する場所を指定します。つまり、これは QuantumLeap の `/v2/notify`
エンドポイントでなければなりません。デフォルトでは、QuantumLeap はポート `8668`
で待機します。この URL は Orion のコンテナから解決できる必要があるため、Docker、
`/etc/hosts`、QuantumLeap が実行されているエンドポイントへの DNS
によい変換されないものや  *localhost* などを使用しないでください

- 必須ではありません が、サブスクリプションの `notification` 部分に、

`"metadata": ["dateCreated", "dateModified"]`
の部分を含めることを強くお勧めします。これは Orion に 属性の変更時刻を
通知に含めるように指示します。可能であれば、このタイムスタンプは
データベースの **タイム・インデックス** として使用されます。
詳細については、*タイム・インデックス* のセクションを参照してください。

- 以前のルールに従っているエンティティに対して、有効な NGSI

サブスクリプションを作成できます

## データの挿入

ここまでの説明で、通常、データを QuantumLeap に直接挿入しないことは明らかです。
Orion に挿入すると、Orion は QuantumLeap に通知します。Orion
での挿入と更新については、
[ドキュメント](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#issuing-commands-to-the-broker)
を参照してください。

サブスクリプションを作成する前に挿入が行われていれば問題ありません。
もちろん、サブスクリプションが作成された後に起こった更新の履歴レコードしか
取得できません。

Orion への挿入ペイロードの例は、前に示した "Test subscription"
の例に基づいて QuantumLeap への通知を生成します。

```json
{
    "id": "Room1",
    "type": "Room",
    "temperature": {
        "value": 24.2,
        "type": "Number",
        "metadata": {}
    },
    "pressure": {
        "value": 720,
        "type": "Number",
        "metadata": {}
    }
    "colour": {
        "value": "white",
        "type": "Text",
        "metadata": {}
    }
}
```

カスタムシナリオがあり、それでも QuantumLeap
に直接挿入したい場合は不可能ではありません。ただし、Orion
が通知で使用するものと同じペイロードを使用する必要があります。
また、あなた自身で発見しなければならない他の細部にも注意が必要です。
これは、共通のワーク・フローとはみなされないため、
完全にドキュメント化されていません。

### 属性データ型の変換

NGSI エンティティが属性に有効な NGSI 型を使用していることを確認する
必要があります。これらの型は、NGSI API の仕様セクションに記載されています。
下記の変換表の最初の欄を参照し、大文字を覚えておいてください。

下の表は、どの属性型がどの
[CrateDB](https://crate.io/docs/crate/reference/sql/data_types.html)
および
[TimescaleDB](https://www.postgresql.org/docs/current/datatype.html)
のデータ型に変換されるかを示しています 。

#### CrateDB (v4.x) 変換テーブル

| NGSI 型          | CrateDB 型          | 見解 |
| ------------------ |:-----------------------:| :-----------|
|Array               | [array(string)](https://crate.io/docs/crate/reference/sql/data_types.html#array)           | [Issue 36: 他のタイプの配列をサポートする](https://github.com/smartsdk/ngsi-timeseries-api/issues/36) |
|Boolean             | [boolean](https://crate.io/docs/crate/reference/sql/data_types.html#boolean)                 | - |
|DateTime            | [timestampz](https://crate.io/docs/crate/reference/en/4.3/general/ddl/data-types.html#timestamp-with-time-zone)                 | 'ISO8601'は 'DateTime'に相当するものとして使用できます |
|Integer             | [bigint](https://crate.io/docs/crate/reference/sql/data_types.html#numeric-types)                  | - |
|[geo:point](http://docs.orioncontextbroker.apiary.io/#introduction/specification/geospatial-properties-of-entities)            | [geo_point](https://crate.io/docs/crate/reference/sql/data_types.html#geo-point)               | **注意!** NGSI は "lat, long"の順番を使用しますが、Crateは、ポイントを[long, lat] 順に格納します |
|[geo:json](http://docs.orioncontextbroker.apiary.io/#introduction/specification/geospatial-properties-of-entities)            | [geo_shape](https://crate.io/docs/crate/reference/sql/data_types.html#geo-shape)               | - |
|Number              | [real](https://crate.io/docs/crate/reference/sql/data_types.html#numeric-types)                   |-|
|Text                | [text](https://crate.io/docs/crate/reference/sql/data_types.html#data-type-text)                  | 提供された NGSI 型がサポートされていないか間違っている場合、これはデフォルト型です |
|StructuredValue     | [object](https://crate.io/docs/crate/reference/sql/data_types.html#object)                  |-|

#### TimescaleDB (v12.x) 変換テーブル

| NGSI 型            | TimescaleDB 型          | 見解        |
| ------------------ |:-----------------------:| :-----------|
|Array               | [jsonb](https://www.postgresql.org/docs/current/datatype-json.html)           |  |
|Boolean             | [boolean](https://www.postgresql.org/docs/current/datatype-boolean.html)                 | - |
|DateTime            | [timestamp WITH TIME ZONE](https://www.postgresql.org/docs/current/datatype-datetime.html)                 | 'ISO8601' は 'DateTime' と同等のものとして使用できます |
|Integer             | [bigint](https://www.postgresql.org/docs/current/datatype-numeric.html#DATATYPE-INT)                  | - |
|[geo:point](http://docs.orioncontextbroker.apiary.io/#introduction/specification/geospatial-properties-of-entities)            | [geometry](https://postgis.net/docs/geometry.html)               | **注意!** NGSI は "lat, long" の順序を使用しますが、PostGIS/WGS84 はポイントを [long, lat] の順序で保存します |
|[geo:json](http://docs.orioncontextbroker.apiary.io/#introduction/specification/geospatial-properties-of-entities)            | [geometry](https://postgis.net/docs/geometry.html)               | - |
|Number              | [float](https://www.postgresql.org/docs/current/datatype-numeric.html#DATATYPE-FLOAT)                   |-|
|Text                | [text](https://www.postgresql.org/docs/current/datatype-character.html)                  | これは、提供されたNGSI 型がサポートされていないか間違っている場合のデフォルトのタイプです |
|StructuredValue     | [jsonb](https://www.postgresql.org/docs/current/datatype-json.html)                  |-|

受信した属性のいずれかの型が前のテーブルの **NGSI 型**の列に存在しない場合、
NGSI 型 (したがって SQL 型) は値から派生します。次のロジックを使用します:

```python
       if a_type not in NGSI
            type = Text
            if a_value is a list:
               type = Array
            elif a_value is not None and a_value is an Object:
                if a_type is 'Property' and a_value['@type'] is 'DateTime':
                    type = DateTime
                else:
                    type = StructuredValue
            elif a_value is int:
                type = Integer
            elif a_value is float:
                type = Number
            elif a_value is bool:
                type = Boolean
            elif a_value is an ISO DateTime:
                type = DateTime
```

### [タイム・インデックス](#timeindex)

時系列データベースの基本要素は**タイム・インデクス**です。あなたは疑問に
思うかもしれません...。それはどこに保存されていますか？ QuantumLeap は各通知の
*タイム・インデクス*を `time_index` と呼ばれる特別な列に保持します。

受信した通知の*タイム・インデクス*に使用される値は、次のポリシーに従って
定義されます。このポリシーでは、次の順序付けられたオプションのリストから
選択された最初の現在の有効な時間値を選択します。

1. カスタム **time index**。`Fiware-TimeIndex-Attribute` http ヘッダの値。
   このようなヘッダを含む通知には、
   [NGSI 仕様](http://fiware.github.io/specifications/ngsiv2/stable/)
   の *Subscriptions and Custom Notifications* セクションに詳述されているように、
   対応するサブスクリプションを `httpCustom` ブロックで作成する必要があることに
   注意してください。これは、通知ペイロードのカスタム属性を使用して
   *タイム・インデックス* のインジケータとして使用するように QL に指示する
   方法です

1. カスタム **time index** メタデータ。通知内のいずれかの属性メタデータ・
   セクションにある最新のカスタム・タイム・インデックス
   (`Fiware-TimeIndex-Attribute`の値) 属性値。サブスクリプションに関する
   詳細については、前のオプションを参照してください

1. **TimeInstant** 属性。
   [FIWARE IoT Agent のドキュメント](https://github.com/telefonicaid/iotagent-node-lib#the-timeinstant-element)
   で指定されているとおりです

1. **TimeInstant** メタデータ。通知内のいずれかの属性メタデータ・セクション
   にある最新の  `TimeInstant` 属性値。(繰り返しますが、
   [FIWARE IoT Agent のドキュメント](https://github.com/telefonicaid/iotagent-node-lib#the-timeinstant-element)
   を参照してください)

1. **timestamp** 属性

1. **timestamp** のメタデータ。通知内のいずれかの属性メタデータ・セクションに
   ある最新の `timestamp` 属性値。
   [FIWARE データ・モデルのドキュメント](https://fiware-datamodels.readthedocs.io/en/latest/guidelines/index.html#dynamic-attributes)
   で指定されているとおりです

1. **dateModified** 属性。
   [Orion サブスクリプションのセクション](#orion-subscription)
   に記載のとおり、これは Orion から通知された `"dateModified"` 値です

1. **dateModified** メタデータ。通知内のいずれかの属性メタデータ・セクションに
   ある最新の `"dateModified"` 属性値です

1. 最後に、上記のオプションのどれも存在しない場合、または見つかった値のどれも
   実際に `datetime` に変換できない場合、QL は**現在時刻** (通知受信時刻)
   を使用します

### 制約と制限

- 同じ名前で、大文字とは異なる2つのエンティティ型を持つことはできません。
  例 : `Preprocessor` と `preProcessor`。特定のエンティティの属性名についても
  同様です。すなわち、`hotSpot` 属性と `hotspot` 属性は、同じように扱われます。
  これらはまれなコーナー・ケースですが、これに留意する価値があります。
  最終的に、型と属性の正しい命名は、
  [ここ](http://fiware-datamodels.readthedocs.io/en/latest/guidelines/index.html)
  で説明する命名ガイドラインを遵守する必要があります

- 属性メタデータは依然として永続化されていません。
  [Issue 12](https://github.com/orchestracities/ngsi-timeseries-api/issues/12)
  を参照してください

- 最近導入された単一の通知における複数のデータのサポート
  ([PR 191](https://github.com/orchestracities/ngsi-timeseries-api/pull/191) を参照)
  が、依然として以下の制限が適用されます。単一のデータ・エンティティにエラーが
  あると、すべてのセットが無効になります。大きなメッセージサイズに対する最適化は
  ありません

- データは一貫していると仮定されます。つまり、エンティティ型の最初のデータ通知で
  属性に特定のデータ型のセットを使用する場合、次のデータ通知は一貫している必要が
  あります。そうしないと拒否されます。例えば。 エンティティ型 `car` の属性
  `speed` のデータ型が最初に `Number` に設定されている場合、後でそれを `Text`
  に設定することはできません

### QuantumLeap にデータを直接挿入

データを QuantumLeap に直接挿入するには、`http://localhost:8668/v2/notify` API
を使用します。つまり、新しい NGSI 通知の到着について QuantumLeap に通知します。

以下の例を検討してください :

```bash
$ curl http://localhost:8668/v2/notify -s -S -H 'Content-Type: application/json' -d @- <<EOF
{ 
    "subscriptionId": "5ce3dbb331dfg9h71aad5deeaa", 
    "data": [ 
        { 
            "id": "Room1", 
            "temperature": 
               { 
                 "value": "10", 
                 "type": "Number" 
               }, 
             "pressure": 
               { 
                 "value": "12", 
                 "type": "Number" 
               }, 
            "type": "Room" 
        } 
    ] 
}
```

データは QuantumLeap に正常に挿入されます。

## データの取得

QuantumLeap から履歴データを取得するには、
[ここ](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
で説明する API エンドポイントを使用します。可能性はたくさんありますが、
それらのすべてがまだ完全に実装されているわけではありません。

必要に応じて、データベースと直接対話できます。詳細は、ドキュメントの
[CrateDB](../admin/crate.md) または [Timescale](../admin/timescale.md)
セクションを参照してください。
この場合、あなたが知る必要があるのは、QuantumLeap が各エンティティ型ごとに
1つのテーブルを作成するということです。テーブル名には接頭辞 (et)
とエンティティ型の小文字のバージョンが含まれます。つまり、エンティティ型が
*AirQualityObserved* であれば、対応するテーブル名がエイリアスになります。
テーブル名には、定義されているスキーマも前に付ける必要があります。以下の
[マルチテナンシー](#multi-tenancy)のセクションを参照してください 。

最後に、[Grafana](https://grafana.com/) を使用してデータを視覚的に操作することが
できます。確認するために、ドキュメントの [Grafana](../admin/grafana.md)
をセクションを参照してください。

## データの削除

QuantumLeap から履歴データを削除する方法は2通りあります。

- 特定のエンティティのすべてのレコードを削除するには、この
  [/entities delete API エンドポイント](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
  を使用します

- 指定した型のすべてのエンティティのすべてのレコードを削除するには、この
  [/types delete API エンドポイント](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
  を使用します

フィルターを使用して、特定の時間間隔でレコードのみを削除します。

## マルチ・テナンシー<a name="multi-tenancy"></a>

QuantumLeap は、Orion が
[ここ](https://fiware-orion.readthedocs.io/en/master/user/multitenancy/index.html)
に記載されている  FIWARE ヘッダの使用と同様に、
異なるテナントの使用をサポートしています。

テナント・ヘッダ (`Fiware-Service` と `Fiware-ServicePath`)
の使用はオプションであることを思い出してください。データの挿入と取り出しは、
デフォルトではそれらなしで機能します。ただし、挿入にヘッダを使用する場合は、
データをクエリするときにヘッダを指定する必要があります。

QuantumLeap の場合、挿入時のヘッダは実際には
[Orion へのサブスクリプション](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
の作成時にクライアントによって使用され、また Orion にデータをプッシュする
ときにもデバイスによって使用されるべきです。前述のように、そのようなデータを
取得するには同じヘッダを使用する必要があります。

データベースと直接対話している場合、QuantumLeap は
[crate](https://crate.io/docs/crate/reference/en/latest/general/ddl/create-table.html?highlight=scheme#schemas)
または [timescale](https://www.postgresql.org/docs/current/ddl-schemas.html)
のデータベース・スキーマ
として特定のプレフィックスを付けて `FIWARE-Service` を使用することを知って
おく必要があります。こうすれば、`Fiware-Service: magic` ヘッダを使って `Room`
型のエンティティを挿入した場合、あなたのテーブルは `mtmagic.etroom` として
見つかるはずです。この情報は、ドキュメントの
[Grafana セクション](../admin/grafana.md)
で説明されているように、例えば Grafana データソースを設定している場合にも
役立ちます。

## ジオ・コーディング

これは、QuantumLeap のオプションで実験的な機能であり、
位置情報が履歴レコードに保存される方法を統一するのに役立ちます。

エンティティが `StructuredValue` 型と `address` という名前の属性を持って、
QuantumLeap に到達すると、QuantumLeap はこれを
[FIWARE データモデル](https://github.com/fiware/dataModels)
に通常見られるアドレス・フィールドとして解釈します。次に、エンティティに、
対応するジオ・タイプの `location` と呼ばれる属性を追加します。これは、
address が都市名、番地、郵便番号を含む完全な住所であれば、
それはポイントにマッピングされるため、生成された属性は `geo:point`
型になります。郵便番号がない場合、address は、(もしあれば)通りか、(もしあれば)
都市の境界か、または国境さえも表します。これらの場合、生成された location は
`geo:json` フォームのものであり、そのような形状の値を含みます。

警告：この機能は、[OpenStreetMap](https://www.openstreetmap.org) と Nominatim
サービスを使用します。そのため、
[著作権に関する注意](https://www.openstreetmap.org/copyright)や、
最も重要な使用ポリシーを認識する必要があります。
[API 使用ポリシー](https://operations.osmfoundation.org/policies/api/) と
[Nominatim 使用ポリシー](https://operations.osmfoundation.org/policies/nominatim/)
はこの無料サービスを悪用するべきではないので、
あなたのリクエストをキャッシュする必要があります。
キャッシュを使用して、ジオ・コーディングを有効にします。QuantumLeap は
そのために、[Redis](https://redis.io/) を使用します。

したがって、この機能を有効にするには、初期化時に、QuantumLeap
コンテナに環境変数 `USE_GEOCODING` を `True` に設定し、環境変数 `REDIS_HOST` と
`REDIS_PORT` をそれぞれ REDIS
インスタンスとそのアクセスポートの場所に設定する必要があります。 たとえば、
[docker-compose-dev.yml](https://raw.githubusercontent.com/orchestracities/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
を参照してください。
