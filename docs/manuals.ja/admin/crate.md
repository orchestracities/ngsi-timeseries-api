# CrateDB

[**CrateDB**](https://crate.io) は、NGSI データが保存される QuantumLeap
のデフォルトのバックエンドです。QL をバイパスしたい場合は、QL の API を
使用するだけでなく、受信した通知から QuantumLeap が保存したすべての
データをクエリするために CrateDB と直接対話することもできます。実装は
将来変更される可能性がある QL 実装の詳細に依存するため、これはもちろん
お勧めできません。

CrateDB は、多くのアプリケーションで使用するのが簡単なデータベース・バックエンドです。
現在、データの大部分はすでにジオタグ (geo-tagged) が付けられています。CrateDB は、
[geo_point](https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html#geo-point-data-type)
および [geo_shape](https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html#geo-shape-data-type)
タイプを使用して、さまざまな種類の地理情報を格納およびクエリするために使用できます。
これらを使用すると、地理的な場所、道路、形状、領域、およびその他のエンティティ
(geographical locations, ways, shapes, areas and other entities) を保存することが
できます。これらは、距離、封じ込め、交差点など (distance, containment,intersection
and so on) についてクエリできます。
現在、CrateDB は 2D 座標をサポートしていますが、
[3D 座標](https://tools.ietf.org/html/rfc7946#section-3.1)はサポートしていません。

[インストールガイド](./installing.md)に従った場合は、Docker コンテナ内ですぐに
使用できる CrateDB インスタンスがあります。
これとインタラクションする最も簡単な方法は、
[ここ](https://crate.io/docs/crate/guide/getting_started/connect/admin_ui.html)
で説明するように、管理インターフェースを使用することです。または、
[HTTP api](https://crate.io/docs/crate/getting-started/en/latest/first-use/query.html#the-cratedb-http-endpoint)
またはその
[サポートされているクライアント](https://crate.io/docs/crate/guide/getting_started/clients/index.html)
を使用できます。

CrateDB と操作する最も簡単な方法は、
[ここ](https://crate.io/docs/crate/guide/getting_started/connect/admin_ui.html)
で説明しているように、管理インターフェースを使用します。または、
[HTTP api](https://crate.io/docs/crate/getting-started/en/latest/first-use/query.html#the-cratedb-http-endpoint)
または
[サポートされているクライアント](https://crate.io/docs/crate/guide/getting_started/clients/index.html)
を使用できます。

CrateDB の詳細については、
[このドキュメント](https://crate.io/docs/crate/reference/)をご覧ください。
