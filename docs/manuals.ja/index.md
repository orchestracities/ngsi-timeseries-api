# QuantumLeap

[![FIWARE Core Context Management](https://img.shields.io/badge/FIWARE-Core-233c68.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAVCAYAAAC33pUlAAAABHNCSVQICAgIfAhkiAAAA8NJREFUSEuVlUtIFlEUx+eO+j3Uz8wSLLJ3pBiBUljRu1WLCAKXbXpQEUFERSQF0aKVFAUVrSJalNXGgmphFEhQiZEIPQwKLbEUK7VvZrRvbr8zzjfNl4/swplz7rn/8z/33HtmRhn/MWzbXmloHVeG0a+VSmAXorXS+oehVD9+0zDN9mgk8n0sWtYnHo5tT9daH4BsM+THQC8naK02jCZ83/HlKaVSzBey1sm8BP9nnUpdjOfl/Qyzj5ust6cnO5FItJLoJqB6yJ4QuNcjVOohegpihshS4F6S7DTVVlNtFFxzNBa7kcaEwUGcbVnH8xOJD67WG9n1NILuKtOsQG9FngOc+lciic1iQ8uQGhJ1kVAKKXUs60RoQ5km93IfaREvuoFj7PZsy9rGXE9G/NhBsDOJ63Acp1J82eFU7OIVO1OxWGwpSU5hb0GqfMydMHYSdiMVnncNY5Vy3VbwRUEydvEaRxmAOSSqJMlJISTxS9YWTYLcg3B253xsPkc5lXk3XLlwrPLuDPKDqDIutzYaj3eweMkPeCCahO3+fEIF8SfLtg/5oI3Mh0ylKM4YRBaYzuBgPuRnBYD3mmhA1X5Aka8NKl4nNz7BaKTzSgsLCzWbvyo4eK9r15WwLKRAmmCXXDoA1kaG2F4jWFbgkxUnlcrB/xj5iHxFPiBN4JekY4nZ6ccOiQ87hgwhe+TOdogT1nfpgEDTvYAucIwHxBfNyhpGrR+F8x00WD33VCNTOr/Wd+9C51Ben7S0ZJUq3qZJ2OkZz+cL87ZfWuePlwRcHZjeUMxFwTrJZAJfSvyWZc1VgORTY8rBcubetdiOk+CO+jPOcCRTF+oZ0okUIyuQeSNL/lPrulg8flhmJHmE2gBpE9xrJNkwpN4rQIIyujGoELCQz8ggG38iGzjKkXufJ2Klun1iu65bnJub2yut3xbEK3UvsDEInCmvA6YjMeE1bCn8F9JBe1eAnS2JksmkIlEDfi8R46kkEkMWdqOv+AvS9rcp2bvk8OAESvgox7h4aWNMLd32jSMLvuwDAwORSE7Oe3ZRKrFwvYGrPOBJ2nZ20Op/mqKNzgraOTPt6Bnx5citUINIczX/jUw3xGL2+ia8KAvsvp0ePoL5hXkXO5YvQYSFAiqcJX8E/gyX8QUvv8eh9XUq3h7mE9tLJoNKqnhHXmCO+dtJ4ybSkH1jc9XRaHTMz1tATBe2UEkeAdKu/zWIkUbZxD+veLxEQhhUFmbnvOezsJrk+zmqMo6vIL2OXzPvQ8v7dgtpoQnkF/LP8Ruu9zXdJHg4igAAAABJRU5ErkJgggA=)](https://www.fiware.org/developers/catalogue/)
[![](https://img.shields.io/badge/tag-fiware-orange.svg?logo=stackoverflow)](https://stackoverflow.com/questions/tagged/fiware)

## 概要

QuantumLeapは、NGSI [FIWARE NGSIv2](http://docs.orioncontextbroker.apiary.io/#)
を [ngsi-tsdb](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)と呼ばれる
[時系列データベース](https://en.wikipedia.org/wiki/Time_series_database)
に格納することをサポートする API の最初の実装です。

最終的には、FIWARE の
[FIWARE's STH Comet](https://fiware-sth-comet.readthedocs.io/en/latest/)
と同様の目標を持っています。
しかし、Comet は、まだ、NGSIv2 をサポートしていません。MongoDB
と結びついており、開発された条件や制約のいくつかはもはや成り立ちません。
それについて間違いないと言われています。これは、FIWARE NGSIv2
の履歴データにバックエンドとして異なる、
時系列データベースを提供する新しい方法を探ることに過ぎません。

アイデアは、さまざま時系列データベースをサポートすることを望んでいることです。
[InfluxDB](https://docs.influxdata.com/influxdb/),
[RethinkDB](https://www.rethinkdb.com/docs/),
[CrateDB](http://www.crate.io) のテストを開始しました。
しかし、私たちは、現在、次の利点のために、[CrateDB](http://www.crate.io)
のトランスレータにその開発を集中させることを決めました :

- [コンテナ化されたデータベース・クラスタ](https://crate.io/docs/crate/guide/en/latest/deployment/containers/index.html)
  による容易なスケーラビリティ
- [ジオ・クエリー](https://crate.io/docs/crate/reference/en/latest/general/dql/geo.html)
  をサポート
- うまく動作する、
  [SQLライクの・クエリ言語](https://crate.io/docs/crate/reference/en/latest/sql/index.html)
- [Grafana](http://www.grafana.com) のような視覚化ツールとの
  [統合サポート](https://grafana.com/plugins/crate-datasource/installation)

## 一般的な使用法とその仕組み

QuantumLeap の一般的な使用シナリオは次のとおりです
(イベントの番号付けに注意してください)...

![QL Architecture](../manuals/rsrc/architecture.png)

**QuantumLeap** のアイデアはとても簡単です。
[NGSiv2通知メカニズム](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#subscriptions)
を利用することにより、クライアントは Orion サブスクリプション **(1)** を作成し、
関心のあるエンティティの変更を QuantumLeap に通知します。
これは、*QuantumLeap の API* を介して行うことも、*Orion*
と直接やりとりすることもできます 。このプロセスの詳細は、
[Orion ユーザ・マニュアルのサブスクリプション](user/index.md#orion-subscription)
の部分で説明しています。

次に、たとえば、1つ以上の
[IoT Agent](https://catalogue-server.fiware.org/enablers/backend-device-management-idas)
によって管理される **IoT レイヤ**全体が、NGSI形式のデータをプッシュするなど、
対象となるエンティティの新しい値が
*[Orion Context Broker](https://fiware-orion.readthedocs.io)** **(2)**
に到着します。その結果、通知は
QuantumLeap の [/v2/notify](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
エンドポイント **(3)** に届きます。

QuantumLeap の**レポーター**・サブモジュールは、受信した通知を解析して検証し、
最終的に構成済みの **トランスレータ** にフィードします。
トランスレータは最終的に、構成された時系列データベースクラスタに NGSI
情報を保持する責任があります。

現在の API には、クライアントが履歴データをクエリするための未処理および
集約データ検索用 **(4)** のいくつかのエンドポイントが含まれています。
また、履歴レコードの削除もサポートしています。現在、すべてのエンドポイントが
QuantumLeap で実装されているわけではありません。API の詳細については、
[NGSI-TSDB specification](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
の仕様を参照してください 。


データ **(5)** の視覚化のために、[Grafana](http://grafana.com/)
にデータベース用のオープンソース・プラグインを補完していました。
将来、QuantumLeap の API と直接対話するための grafana
プラグインを想定しています。

## 詳細情報

- QuantumLeap のインストール方法については[管理者ガイド](admin/index.md)
  を参照してください
- QuantumLeap を使用して他の補完的なサービスに接続する方法については、
  使用方法の詳細は[ユーザ・マニュアル](user/index.md)を参照してください
- QuantumLeap の使用例については、
  [SmartSDK ガイド・ツアー](http://guided-tour-smartsdk.readthedocs.io/en/latest/)
  をご覧ください
