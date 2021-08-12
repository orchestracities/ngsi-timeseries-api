# 健全性チェック

QuantumLeap のデプロイが完全で機能していることを確認するために、
これらの健全性チェック (Sanity Check) に従うことができます。

この手順では、localhost にマップされたポートを使用して、ローカルの Docker
ベースのデプロイを想定しています。もちろん、デプロイに合わせてサービスの IP
アドレスを更新する必要があります。

## 手動の健全性チェック

プロセスを手動で実行すると、フローに精通するのに役立ちます。お手伝いするために、
[この postman collection](https://raw.githubusercontent.com/smartsdk/smartsdk-recipes/master/recipes/tools/postman_collection.json)
で *Orion* と *QuantumLeap* のリクエストを使用することができます。
Postman を使用しない場合は、以下の同等の curl コマンドを使用できます。

1. *Orion のバージョン*を確認できますか?

  ```bash
  $ curl -X GET http://0.0.0.0:1026/version -H 'Accept: application/json'
  ```

  `200 OK` の返信ステータスを取得する必要があります。

1. *QuantumLeap のバージョン*を確認できますか？

  ```bash
  $ curl -X GET http://0.0.0.0:8668/version -H 'Accept: application/json'
  ```

  `200 OK` の返信ステータスを取得する必要があります。

1. "QuantumLeap Subscribe" を通して、Orion のサブスクリプションを作成

  ```bash
  $ curl -X POST \
  'http://0.0.0.0:8668/v2/subscribe?orionUrl=http://orion:1026/v2&quantumleapUrl=http://quantumleap:8668/v2&entityType=AirQualityObserved' \
  -H 'Accept: application/json'
  ```

  [AirQualityObserved](https://github.com/FIWARE/data-models/tree/master/specs/Environment/AirQualityObserved)
  型のエンティティの任意の属性の変更についてサブスクリプションを
  作成したばかりです。`201 Created` の返信ステータスを取得する必要があります。

1. Orion から次のようなサブスクリプションを取得を確認できますか？

  ```bash
  $ curl -X GET http://0.0.0.0:1026/v2/subscriptions \
  -H 'Accept: application/json'
  ```

  `200 OK` の返信ステータスを取得する必要があります。

1. Orion に AirQualityObserved のエンティティを挿入します。

  ```bash
  $ curl -X POST \
  'http://0.0.0.0:1026/v2/entities?options=keyValues' \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "air_quality_observer_be_001",
  "type": "AirQualityObserved",
  "address": {
  "streetAddress": "IJzerlaan",
  "postOfficeBoxNumber": "18",
  "addressLocality": "Antwerpen",
  "addressCountry": "BE"
  },
  "dateObserved": "2017-11-03T12:37:23.734827",
  "source": "http://testing.data.from.smartsdk",
  "precipitation": 0,
  "relativeHumidity": 0.54,
  "temperature": 12.2,
  "windDirection": 186,
  "windSpeed": 0.64,
  "airQualityLevel": "moderate",
  "airQualityIndex": 65,
  "reliability": 0.7,
  "CO": 500,
  "NO": 45,
  "NO2": 69,
  "NOx": 139,
  "SO2": 11,
  "CO_Level": "moderate",
  "refPointOfInterest": "null"
  }'
  ```

  `201 Created` の返信ステータスを取得する必要があります。

  これはサニティチェックであるため、簡略化のために `options=keyValues`
  を使用しています。実際にこのようなオプションを使用すると、
  [ユーザ・ガイド](../user/using.md#orion-subscription)
  で説明されているように変換機能が失われる可能性があります。

1. Orion の同じエンティティの降水値を更新します。

  ```bash
  $ curl -X PATCH \
  http://0.0.0.0:1026/v2/entities/air_quality_observer_be_001/attrs \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "precipitation": {
  "value": 100,
  "type": "Number"
  }
  }'
  ```

  `204 No Content` の返信ステータスを取得する必要があります。

1. 同じエンティティ (1T1E1A) の降水量の履歴記録を再度クエリします。

  ```bash
  $ curl -X GET \
  'http://0.0.0.0:8668/v2/entities/air_quality_observer_be_001/attrs/precipitation?type=AirQualityObserved' \
  -H 'Accept: application/json'
  ```

  `200 OK` の返信ステータスとレスポンス・ボディの履歴レコードを取得する
  必要があります。

1. 最後に、整理するために、作成したすべてのレコードを削除することができます。

    QuantumLeap からレコードを削除します

  ```bash
  $ curl -X DELETE http://0.0.0.0:8668/v2/types/AirQualityObserved
  ```

  Orion からエンティティを削除します

  ```bash
  $ curl -X DELETE \
  http://0.0.0.0:1026/v2/entities/air_quality_observer_be_001 \
  -H 'Accept: application/json'
  ```

  Orion からのサブスクリプションを削除します。`id` があなたのものに
  置き換えられます

  ```bash
  $ curl -X DELETE \
  http://0.0.0.0:1026/v2/subscriptions/5b3df2ae940fcc446763ef90 \
  -H 'Accept: application/json'
  ```

## 自動の健全性チェック

フローに精通していて、重要なサービスが正しく展開されているかどうかを素早く
チェックしたい場合は、コア・コンポーネント間の接続を正確にチェックする
統合テストを利用できます。

**重要 :** 貴重なデータを含む実稼働環境でこのスクリプトを実行することは
推奨されていません。テストで問題が起これば、ゴミ・データが残ったり、
データが失われたりする可能性があります。
常にそうであるように、自動化は慎重に使用してください。

[ここ](https://github.com/orchestracities/ngsi-timeseries-api/blob/master/src/tests/test_integration.py)
にテストスクリプトがあります。デプロイに応じて、設定する必要のある入力変数に
注意してください。これらは、コア・サービスを見つけるための URL を示します。
デフォルトでは、すべてのサービスはローカルの Docker ベースのデプロイで
実行されているものとみなされます。

次のように、コンテナ内でテストをすばやく実行できます。
もちろん、デプロイされたサービスを指すように、URLを調整する必要があります。
次の例では、Orion と QuantumLeap にテスト・コンテナによって、`192.0.0.1`
に到達可能であり、Orion と QuantumLeap は、デフォルトで、`orion` と
`quantumleap` エンドポイントで検索されます。なぜなら両方が同じ Docker
ネットワークにデプロイされているからです。

```bash
$ docker run -ti --rm -e ORION_URL="http://192.0.0.1:1026" -e QL_URL="http://192.0.0.1:8668" quantumleap pytest tests/test_integration.py
```

または、すべてのサービスが同じ Docker デプロイメントにあり、
そのサービスにアクセスできると仮定すると、同じネットワーク内でテスト・コンテナを
実行して、URL 内のサービス名を使用することができます。

```bash
$ docker run -ti --rm --network docker_default -e ORION_URL="http://orion:1026" -e QL_URL="http://quantumleap:8668" quantumleap pytest tests/test_integration.py
```
