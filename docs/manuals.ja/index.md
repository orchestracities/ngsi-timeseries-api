# QuantumLeap

## 概要

QuantumLeapは、NGSI [FIWARE NGSIv2](http://docs.orioncontextbroker.apiary.io/#) を [ngsi-tsdb](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb/0.1)と呼ばれる[時系列データベース](https://en.wikipedia.org/wiki/Time_series_database)に格納することをサポートする API の最初の実装です。

最終的には、FIWARE の [FIWARE's Comet STH](https://fiware-sth-comet.readthedocs.io/en/latest/) と同様の目標を持っています。しかし、Comet は、まだ、NGSIv2 をサポートしていません。MongoDB と結びついており、開発された条件や制約のいくつかはもはや成り立ちません。それについて間違いないと言われています。これは、FIWARE NGSIv2 の履歴データにバックエンドとして異なる、時系列データベースを提供する新しい方法を探ることに過ぎません。

アイデアは、さまざま時系列データベースをサポートすることを望んでいることです。[InfluxDB](https://docs.influxdata.com/influxdb/), [RethinkDB](https://www.rethinkdb.com/docs/), [CrateDB](http://www.crate.io) のテストを開始しました。 しかし、私たちは、現在、次の利点のために、[CrateDB](http://www.crate.io) のトランスレータにその開発を集中させることを決めました。

- [コンテナ化されたデータベース・クラスタ](https://crate.io/docs/crate/guide/en/latest/deployment/containers/index.html)による容易なスケーラビリティ
- [ジオ・クエリー](https://crate.io/docs/crate/reference/en/latest/general/dql/geo.html)をサポート
- うまく動作する、[SQLライクの・クエリ言語](https://crate.io/docs/crate/reference/en/latest/sql/index.html)
- [Grafana](http://www.grafana.com) のような視覚化ツールとの[統合サポート](https://grafana.com/plugins/crate-datasource/installation)

## 一般的な使用法とその仕組み

QuantumLeap の一般的な使用シナリオは次のとおりです (イベントの番号付けに注意してください)...

![QL Architecture](rsrc/architecture.png)

**QuantumLeap** のアイデアはとても簡単です。[NGSiv2通知メカニズム](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#subscriptions)を利用することにより、クライアントは Orion サブスクリプション **(1)** を作成し、関心のあるエンティティの変更を QuantumLeap に通知します。これは、*QuantumLeap の API* を介して行うことも、*Orion* と直接やりとりすることもできます 。このプロセスの詳細は、[Orion ユーザ・マニュアルのサブスクリプション](user/index.md#orion-subscription)の部分で説明しています。

次に、たとえば、1つ以上の [IoT Agent](https://catalogue-server.fiware.org/enablers/backend-device-management-idas) によって管理される **IoT レイヤ**全体が、NGSI形式のデータをプッシュするなど、対象となるエンティティの新しい値が *[Orion Context Broker](https://fiware-orion.readthedocs.io)** **(2)** に到着します。その結果、通知は QuantumLeap の [/v2/notify](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb/0.1#/input/reporter.reporter.notify) エンドポイント **(3)** に届きます。

QuantumLeap の**レポーター**・サブモジュールは、受信した通知を解析して検証し、最終的に構成済みの **トランスレータ** にフィードします。トランスレータは最終的に、構成された時系列データベースクラスタに NGSI 情報を保持する責任があります。

現在の API には、クライアントが履歴データをクエリするための未処理および集約データ検索用 **(4)** のいくつかのエンドポイントが含まれています 。また、履歴レコードの削除もサポートしています。現在、すべてのエンドポイントが QuantumLeap で実装されているわけではありません。API の詳細については、[NGSI-TSDB specification](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb/0.1) の仕様を参照してください 。


データ **(5)** の視覚化のために、[Grafana](http://grafana.com/) にデータベース用のオープンソース・プラグインを補完していました。将来、QuantumLeap の API と直接対話するための grafana プラグインを想定しています。

## 詳細情報

- QuantumLeap のインストール方法については[管理者ガイド](admin/index.md)を参照してください
- QuantumLeap を使用して他の補完的なサービスに接続する方法については、使用方法の詳細は[ユーザ・マニュアル](user/index.md)を参照してください
- QuantumLeap の使用例については、[SmartSDK ガイド・ツアー](http://guided-tour-smartsdk.readthedocs.io/en/latest/)をご覧ください
