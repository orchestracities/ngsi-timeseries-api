# QuantumLeap

[![FIWARE Core Context Management](https://img.shields.io/badge/FIWARE-Core-233c68.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAVCAYAAAC33pUlAAAABHNCSVQICAgIfAhkiAAAA8NJREFUSEuVlUtIFlEUx+eO+j3Uz8wSLLJ3pBiBUljRu1WLCAKXbXpQEUFERSQF0aKVFAUVrSJalNXGgmphFEhQiZEIPQwKLbEUK7VvZrRvbr8zzjfNl4/swplz7rn/8z/33HtmRhn/MWzbXmloHVeG0a+VSmAXorXS+oehVD9+0zDN9mgk8n0sWtYnHo5tT9daH4BsM+THQC8naK02jCZ83/HlKaVSzBey1sm8BP9nnUpdjOfl/Qyzj5ust6cnO5FItJLoJqB6yJ4QuNcjVOohegpihshS4F6S7DTVVlNtFFxzNBa7kcaEwUGcbVnH8xOJD67WG9n1NILuKtOsQG9FngOc+lciic1iQ8uQGhJ1kVAKKXUs60RoQ5km93IfaREvuoFj7PZsy9rGXE9G/NhBsDOJ63Acp1J82eFU7OIVO1OxWGwpSU5hb0GqfMydMHYSdiMVnncNY5Vy3VbwRUEydvEaRxmAOSSqJMlJISTxS9YWTYLcg3B253xsPkc5lXk3XLlwrPLuDPKDqDIutzYaj3eweMkPeCCahO3+fEIF8SfLtg/5oI3Mh0ylKM4YRBaYzuBgPuRnBYD3mmhA1X5Aka8NKl4nNz7BaKTzSgsLCzWbvyo4eK9r15WwLKRAmmCXXDoA1kaG2F4jWFbgkxUnlcrB/xj5iHxFPiBN4JekY4nZ6ccOiQ87hgwhe+TOdogT1nfpgEDTvYAucIwHxBfNyhpGrR+F8x00WD33VCNTOr/Wd+9C51Ben7S0ZJUq3qZJ2OkZz+cL87ZfWuePlwRcHZjeUMxFwTrJZAJfSvyWZc1VgORTY8rBcubetdiOk+CO+jPOcCRTF+oZ0okUIyuQeSNL/lPrulg8flhmJHmE2gBpE9xrJNkwpN4rQIIyujGoELCQz8ggG38iGzjKkXufJ2Klun1iu65bnJub2yut3xbEK3UvsDEInCmvA6YjMeE1bCn8F9JBe1eAnS2JksmkIlEDfi8R46kkEkMWdqOv+AvS9rcp2bvk8OAESvgox7h4aWNMLd32jSMLvuwDAwORSE7Oe3ZRKrFwvYGrPOBJ2nZ20Op/mqKNzgraOTPt6Bnx5citUINIczX/jUw3xGL2+ia8KAvsvp0ePoL5hXkXO5YvQYSFAiqcJX8E/gyX8QUvv8eh9XUq3h7mE9tLJoNKqnhHXmCO+dtJ4ybSkH1jc9XRaHTMz1tATBe2UEkeAdKu/zWIkUbZxD+veLxEQhhUFmbnvOezsJrk+zmqMo6vIL2OXzPvQ8v7dgtpoQnkF/LP8Ruu9zXdJHg4igAAAABJRU5ErkJgggA=)](https://www.fiware.org/developers/catalogue/)
[![stackoverflow](https://img.shields.io/badge/tag-fiware-orange.svg?logo=stackoverflow)](https://stackoverflow.com/questions/tagged/fiware)

## 概要

QuantumLeap は、[NGSI v2][ngsi-spec] 時空間データを保存、クエリ、および
取得するための REST サービスです。QuantumLeap は、NGSI の半構造化データ
を表形式に変換して [time-series database][tsdb] に保存し、各データベース
のレコードを時間インデックスに関連付け、NGSI データに存在する場合は
地球上の場所に関連付けます。REST クライアントは、時間範囲と空間演算子を
使用してエンティティ・セットをフィルタリングすることにより、NGSI
エンティティを取得できます。クライアントの観点から、これらのクエリは
データベースのテーブルではなく NGSI エンティティで定義されることに
注意してください。ただし、REST インターフェイスを介して使用できるクエリ
機能は非常に基本的であり、最も複雑なクエリでは通常、クライアントが
データベースを直接使用する必要があります。

QuantumLeap が実装する NGSI-TSDB と呼ばれるREST
[API specification][ql-spec] は、NGSI 仕様自体に可能な限り近い、NGSI
エンティティの時系列のストレージ、クエリ、および取得にデータベースに
依存しない REST インターフェイスを提供することを目的として定義されて
います。したがって、NGSI-TSDB は、時系列データにアクセスするための統一
された、FIWARE 開発者にとって使い慣れた、メカニズムを提供し、QuantumLeap
などのサービスを実装して複数のデータベース・バックエンドを透過的に
サポートします。実際、現在 QuantumLeap はバックエンド・データベースとして
[CrateDB][crate] と [Timescale][timescale] の両方をサポートしています。

### STH Comet との関係

QuantumLeap と FIWARE [STH Comet][comet] は同様の目標を共有しますが、
Comet は複数のデータベース・バックエンドをサポートせず (MongoDB
のみが利用可能)、NGSI v2 もサポートしません。Comet 自体は素晴らしい
ソフトウェアですが、開発のきっかけとなったニーズと仮定のいくつかはもはや
最新のものではありません。QuantumLeap は、特定のデータベース・バックエンド
にコミットせずに、FIWARE エコシステムで履歴データを利用できる代替方法の
調査として始まりました。

## オペレーション

通常、QuantumLeap は、Context Broker, [Orion][orion] で事前に設定された
NGSI 通知を介して、FIWARE IoT Agent レイヤーから間接的に NGSI エンティティ
の形式で IoT データを取得します。(読者は、[NGSI specification][ngsi-spec]
の *Notification Messages* および *Subscriptions* セクションで説明されて
いる NGSI パブリッシュ/サブスクライブのメカニズムに精通していると想定
します) 前述のように、着信した NGSI エンティティはデータベースに変換され、
構成された時系列データベースのバックエンドの1つ (通常はデータベース・
クラスタ) に記録および保存されます。しばしば、QuantumLeap がデータベースに
保存する時系列データを視覚化するために、[Grafana][grafana] などの視覚化
ツールもデプロイされます。以下の図は、一般的な QuantumLeap デプロイ・
シナリオでのこれらのシステム間の関係と相互作用を示しています。

![QL Architecture](../manuals/rsrc/architecture.png)

QuantumLeap が Orion からデータを受信するために、クライアントは Orion
 でサブスクリプションを作成し、変更が発生したときに通知するエンティティを
指定します。この図は、クライアントが QuantumLeap **(1)** で
サブスクリプションを直接作成していることを示しています。これは、
クライアントのサブスクリプションを Orion に単に転送する QuantumLeap REST
API の便利なエンドポイントです。(サブスクリプションの設定の詳細については、
QuantumLeap マニュアルの [Orion Subscription][ql-man.sub] セクションを
ご覧ください。)

この時点から、[IoT レイヤーのエージェント][fw-catalogue] が Context Broker
**(2)** にデータをプッシュするとき、データがクライアントのサブスクリプション
によって特定されたエンティティに関係する場合、Orion は、NGSI エンティティを
QuantumLeap の [通知のエンドポイントに][ql-spec] **(3)** に POST することに
より、データを QuantumLeap に転送します。

QuantumLeap の **Reporter** コンポーネントは、POST されたデータを解析および
検証します。さらに、ジオコーディングが設定されている場合、**Reporter** は
**Geocoder** コンポーネントを呼び出して、通知されたエンティティの位置表現を
調整します。これには、[OpenStreetMap][osm] (OSM) で地理情報を検索することが
含まれます 最後に、**Reporter** は、検証および調整された NGSI エンティティを
**Translator** コンポーネントに渡します。**Translator** は、NGSI
エンティティを表形式に変換し、それらを時系列レコードとしてデータベースに
保持します。サポートされている各データベースバックエンドに対応する
**Translator** コンポーネントがあります。以下のセクションを参照してください。
[設定][ql-man.db-sel] に応じて、**Reporter** は使用する **Translator** を
選択します。

クライアントが REST API にクエリして NGSI エンティティ **(4)** を取得すると、
**Reporter** および **Translator** が相互作用して、Web クエリを空間および
時間句を含む SQL クエリに変換し、データベースを取得します。それらを記録し、
最終的にクライアントに返される NSGI エンティティの時系列に変換します。
前述のように、REST インターフェイスで使用できるクエリ機能は非常に基本的です。
QuantumLeap は、時間範囲、[NGSI 仕様][ngsi-spec]で定義された地理的クエリ、
および平均などの単純な集計関数によるフィルタリングをサポートします。
それ以外に、QuantumLeap は履歴レコードの削除もサポートしていますが、
現時点では NGSI-TSDB 仕様を**完全に実装していない**ことに注意してください。
詳細については、REST API [仕様][ql-spec]を参照してください。

最後に、図は、Webクライアント**(5)** の時系列を視覚化するために、
データベースに直接クエリする Grafana を示しています。原則として、
データベースの代わりに QuantumLeap REST API をクエリする Grafana プラグインを
開発できます。これにより、QuantumLeap 内部から可視化ツールが保護されます。
実際に、(それほど遠くない！) 将来、そのようなプラグインを開発する計画が
あります。

## データベース・バックエンド

QuantumLeap 設計の指針の1つは、複数の時系列データベースを使用できることです。
この設計上の選択は、現在の状況によってはデータベース製品が他の製品よりも
適している可能性があるという事実によって正当化されます。現在、QuantumLeap
は [CrateDB][crate] と [Timescale][timescale] の両方で使用できます。
[InfluxDB][influx] および [RethinkDB][rethink] の実験的サポートも利用
できますが、これら2つのバックエンドの開発が停滞しているため、現時点では
使用できません。

このマニュアルの [データベースの選択][ql-man.db-sel] セクションでは、
利用可能なデータベース・バックエンドのいずれかを使用するように QuantumLeap
を構成する方法について説明しています。

### CrateDB バックエンド

[CrateDB][crate] はデフォルトのバックエンドです。
[containerisation][crate-doc.cont] に適した shared-nothing アーキテクチャに
より、スケーリングが容易です。そのため、Kubernetes などを使用して、
コンテナ化された CrateDB データベース・クラスタを比較的簡単に管理できます。
さらに、CrateDB は [SQL][crate-doc.sql] を使用してデータをクエリし、一時的
および[地理的クエリ][crate-doc.geo] の組み込み拡張機能を使用します。また、
Grafana には、CrateDB に保存されている時系列を視覚化するために使用できる
[プラグイン][grafana.pg] が付属しています。

### Timescale バックエンド

[Timescale][timescale] は、NGSI エンティティの時系列を格納するバックエンド
として QuantumLeap で使用できる別の時系列データベースです。実際、
QuantumLeap は、地理的特徴 (GeoJSON または NGSI Simple Location Format
 としてエンコード)、構造化タイプ、配列など、NGSI エンティティの Timescale
への保存を完全にサポートしています。

QuantumLeap は、既存の `notify` 通知エンドポイントを使用して NGSI
エンティティを Timescale に保存します。Timescale のバックエンドは、
[PostgreSQL][postgres] で構成され、Timescale と [PostGIS] [postgis]
拡張の両方が有効になっています :

    -------------------------
    | Timescale     PostGIS |          ---------------
    | --------------------- |  <-----  | QuantumLeap |-----O notify
    |       Postgres        |          ---------------
    -------------------------

PostgreSQL は確固たる、テスト済みのオープンソース・データベースであり、その
PostGIS 拡張機能は高度な空間機能の優れたサポートを提供しますが、Timescale
拡張機能は時系列データをかなり強力にサポートします。NGSI エンティティを
表形式に変換するメカニズムは、いくつかの改善を除いて、Crate バックエンドと
ほぼ同じです。

* NGSI 配列は、Crate バックエンドの文字列のフラット配列ではなく、
  インデックス化およびクエリ可能な JSONとして保存されます
* GeoJSON および NGSI Simple Location Format 属性は、インデックスおよび
  クエリが可能な空間データとして保存されます。Crate バックエンドでは、
  空間属性の完全なサポートはまだ不完全です

QuantumLeap ソースベースの `test_timescale_insert.py` ファイルには、
NGSI データが Timescale に保存される方法の非常に多くの例が含まれています。

#### 注: データのクエリと取得

現時点では、QuantumLeap は、Crate バックエンドで利用可能な QuantumLeap REST
API を介したデータのクエリまたは取得を**実装していません**。つまり、
現在のところ、データにアクセスする唯一の方法は、Timescale DB に直接クエリを
実行することです。ただし、今後の QuantumLeap メジャー・リリースでは、
REST API を介したデータのクエリと取得が計画されています。

## 関連情報

* [管理者ガイド][ql-man.admin]は、QuantumLeap をインストールして実行する方法
  を説明しています
* [ユーザ・マニュアル][ql-man.user]では、その使用方法と他の補完的なサービスへ
  の接続方法について詳しく説明しています
* [FIWARE Time Series][ql-tut] は、QuantumLeap のセットアップと使用方法を学ぶ
  ための完全なステップ・バイ・ステップの実践的チュートリアルです
* [SmartSDK ガイド・ツアー][smartsdk.tour]には、FIWARE クラウドでの
  QuantumLeap の使用に関するセクションがあります

[comet]: https://fiware-sth-comet.readthedocs.io/en/latest/
    "FIWARE STH Comet Manual"
[crate]: http://www.crate.io
    "CrateDB Home"
[crate-doc.cont]: https://crate.io/docs/crate/guide/en/latest/deployment/containers/
    "CrateDB Containers"
[crate-doc.geo]: https://crate.io/docs/crate/reference/en/latest/general/dql/geo.html
    "CrateDB Geo-search"
[crate-doc.sql]: https://crate.io/docs/crate/reference/en/latest/sql/index.html
    "CrateDB SQL"
[fw-catalogue]: https://www.fiware.org/developers/catalogue/
    "FIWARE Catalogue"
[grafana]: http://www.grafana.com
    "Grafana Home"
[grafana.pg]: http://docs.grafana.org/features/datasources/postgres/
    "Grafana PostgreSQL Data Source"
[ngsi-spec]: https://fiware.github.io/specifications/ngsiv2/stable/
    "FIWARE-NGSI v2 Specification"
[orion]: https://fiware-orion.readthedocs.io
    "Orion Context Broker Home"
[osm]: https://www.openstreetmap.org
    "OpenStreeMap Home"
[postgres]: https://www.postgresql.org
    "PostgreSQL Home"
[postgis]: https://postgis.net/
    "PostGIS Home"
[ql-man.admin]: ./admin/installing.md
    "QuantumLeap - Admin Guide"
[ql-man.db-sel]: ./admin/configuration.md
    "QuantumLeap - Configuration"
[ql-man.sub]: ./user/using.md#orion-subscription
    "QuantumLeap - Orion Subscription"
[ql-man.user]: ./user/using.md
    "QuantumLeap - User Manual"
[ql-spec]: https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb
    "NGSI-TSDB Specification"
[ql-tut]: https://fiware-tutorials.readthedocs.io/en/latest/time-series-data/
    "FIWARE Tutorials - Time Series Data"
[rethink]: https://www.rethinkdb.com/
    "RethinkDB Home"
[smartsdk.tour]: http://guided-tour-smartsdk.readthedocs.io/en/latest/
    "SmartSDK Guided Tour"
[timescale]: https://www.timescale.com
    "Timescale Home"
[tsdb]: https://en.wikipedia.org/wiki/Time_series_database
    "Wikipedia - Time series database"
