# CrateDB

[**CrateDB**](https://crate.io) は、NGSI データが保存される QuantumLeap
のデフォルトのバックエンドです。QL をバイパスしたい場合は、QL の API を
使用するだけでなく、受信した通知から QuantumLeap が保存したすべての
データをクエリするために CrateDB と直接対話することもできます。実装は
将来変更される可能性がある QL 実装の詳細に依存するため、これはもちろん
お勧めできません。

[インストールガイド](./index.md)に従った場合は、Docker コンテナ内ですぐに
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
