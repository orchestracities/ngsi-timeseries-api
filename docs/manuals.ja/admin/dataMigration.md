# Data-Migration-Tool (データ・マイグレーション・ツール)

Data-Migration-Tool は、[STH-Comet](https://github.com/telefonicaid/fiware-sth-comet)
に格納されているデータを
[QuantumLeap](https://github.com/smartsdk/ngsi-timeseries-api)
データベースに自動的に移行するように設計されています。データ移行後、QuantumLeap の
[API](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb/0.2)
を使用してデータにアクセスできます。

このツールは [Eclipse](https://www.eclipse.org/) を使用して
[Java](https://en.wikipedia.org/wiki/Java_(software_platform))
で開発されています。 Python スクリプトを使用して
[MongoDB](https://github.com/mongodb/mongo)
内のデータを
[CrateDB](https://github.com/crate/crate)
と互換性があるように変換します。

ツールは[こちら](https://github.com/Data-Migration-Tool/STH-to-QuantumLeap)
から入手できます。

ツールのユーザ・ガイドは、
[こちら](https://github.com/Data-Migration-Tool/STH-to-QuantumLeap/blob/master/docs/manuals/README.md)
から入手できます。
