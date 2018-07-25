# Grafana

[**Grafana**](https://grafana.com/) は、永続化されたデータのグラフィックを表示するために使用できる強力な視覚化ツールです。

Grafana は、[Crate](./crate.md) データベースからデータを読み込むために、[Grafana Datasource Plugin for CrateDB](https://grafana.com/plugins/crate-datasource) を活用しています。

[インストール・ガイド](./index.md)に従った場合は、前述のプラグインが既にインストールされている状態で、Docker コンテナで既に Grafana が実行されています。

今のところ、Crate のデータ・ソースは1つのテーブルに限定され、Quantum leap はエンティティ型ごとに1つのテーブルを作成します。したがって、エンティティ型ごとに1つのデータソースを作成する必要があります。これがあなたの問題または制限である場合は、[quantumleap のレポで問題 (issue) をオープン](https://github.com/smartsdk/ngsi-timeseries-api/issues)し、回避する方法を見てみましょう。

## データソースの設定

デプロイされた Grafana インスタンス (たとえば、http://localhost:3000) を調べてください。既定の資格情報を変更しなかった場合は `admin` で、ユーザーとパスワードの両方として使用します。

*Add data source* に移動して、次のようにして必要なフィールドに入力します :

- **Name** : データソースに必要な名前です。エンティティ型、つまり、接続先のテーブルの後に名前を付けることをお勧めします
- **Type** : `Crate` を使用します。`Crate` が表示されない場合は、[トラブルシューティング](../user/troubleshooting.md)を参照してください
- **Url** : Cratedb がデプロイされた完全な URL
- **Access** : すべてをローカルに展開する場合に `direct` を使用します。[HA deployment](./index.md) の場合のようにプロキシの背後に Crate を配備する場合、`proxy` オプションを選択してください
- **Schema** :テーブルが定義されているスキーマ。デフォルトでは、Crate で `doc` を使用しますが、マルチ・テナンシーのヘッダーを使用している場合は、エンティティ型のテナントによってスキーマが定義されます。詳細は、 [マルチ・テナンシーのセクション](../user/index.md#multi-tenancy)を確認してください。
- **Table** : エンティティのテーブルの名前です。テーブル名がどのように定義されているかを知るには、[データ検索](../user/index.md) のセクションを参照してください
- **Time column** : タイム・インデックスとして使用される列の名前です。デフォルトでは、[タイム・インデックス](../user/index.md) のセクションで説明したように、'time_index' があります。

次の図は、*yourentity* というエンティティタイプのデータソース設定の例を示しています :

![alt text](../rsrc/crate_datasource.png "Configuring the DataSource")

## グラフ内のデータソースの使用

データソースをセットアップしたら、さまざまな視覚化ウィジェットで使用することができます。

以下は、Crate データソースを使用したグラフの例です。データソース (この場合は、CrateDB) の選択、および *from* フィールドのテーブルの指定に注意してください。テーブルは *schema.tablename* として参照されていることに注意してください。たとえば、*doc.etairqualityobserved* です。

![alt text](../rsrc/graph_example.png "Using the DataSource in your Graph")
