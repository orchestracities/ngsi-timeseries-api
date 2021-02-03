# 使用ポート

以下の表は、通常、QuantumLeap で使用される各サービスのデフォルト・ポートを
まとめたものです。したがって、ファイアウォールの背後で実行する場合は、
対応するルールを含めるようにしてください。

| プロトコル        | ポート        | 説明       |
| -------------     |:-------------:| :-----|
|TCP| 1026|  Orion CB |
|TCP| 8668|  QuantumLeap の API |
|TCP| 3000|  Grafana |

参考情報 : 次のものは、一般的には外部に公開されるべきではなく、
クラスター内で使用されるべきです

| プロトコル        | ポート        | 説明       |
| -------------     |:-------------:| :-----|
|TCP                | 27017         |  Mongo データベース|
|TCP                | 4200          |  CrateDB 管理 UI |
|TCP                | 4300          |  CrateDB トランスポート・プロトコル |
|TCP                | 5432          |  PostgreSQL プロトコル |
|TCP                | 6379          |  Redisキャッシュ (ジオ・コーディングで使用) |

このリポジトリの
[docker-compose-dev.yml](https://raw.githubusercontent.com/orchestracities/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
ファイル (実際にはデプロイに使用したものはもちろんのこと) で公開されている
ポートをいつでも調べることができます。
