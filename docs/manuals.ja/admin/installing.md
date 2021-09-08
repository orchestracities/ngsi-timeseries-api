# Installing

現在のところ、QuantumLeap の唯一の積極的にサポートされている
ディストリビューションは Docker をベースとしています。
ただし、ソースからビルドしてインストールすることはできますが、現時点では、
そのようなインストールについてのガイダンスは提供していません。

Docker をインストールする必要がある場合は、
[Docker のインストール](https://docs.docker.com/engine/installation/)
を参照してください。
動作することを確認するには、次のコマンドが正常に実行できる必要があります...

```bash
docker --version
```

いくつかのケースでは、 [docker-compose](https://docs.docker.com/compose/)
が必要となります。
[インストールのドキュメント](https://docs.docker.com/compose/install/)
を確認してください。動作することを確認するには、
次のコマンドが正常に実行できる必要があります...

```bash
docker-compose --version
```

QuantumLeap の Docker イメージは、
[https://hub.docker.com/r/orchestracities/quantumleap/](https://hub.docker.com/r/orchestracities/quantumleap/)
でホストされています。

今、あなたのシナリオに応じて、さまざまな展開オプションがあります。
以下のセクションを参照してください。インストール後、
[サニティ・チェック](check.md)を行うことで、
すべてが期待どおりに動作していることを確認できます。

## 単一のホストにQuantumLeapを展開してローカルテストを行う

[典型的なシナリオ](../index.md)のすべてのコンポーネントをすぐに素早く展開して、
QuantumLeap の実験をできるだけ早く開始するには、以下の手順に従ってください 。

**重要:** 本番環境ではこのアプローチを使用しないでください。

[このdocker-compose.yml](https://raw.githubusercontent.com/orchestracities/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
ファイルのコピーをダウンロードするか、またはローカル作成してください。
その後、起動してください :

```bash
# same path were you have placed the docker-compose-dev.yml
$ docker-compose -f docker-compose-dev.yml up -d
```

しばらくして、すべてのコンテナが起動していることを確認します :

```bash
$ docker ps
CONTAINER ID        IMAGE                  COMMAND                  CREATED             STATUS                   PORTS                                                           NAMES
8cf0b544868d        orchestracities/quantumleap   "/bin/sh -c 'python …"   2 minutes ago       Up 2 minutes             0.0.0.0:8668->8668/tcp                                          docker_quantumleap_1
aa09dbcb8500        fiware/orion:1.13.0    "/usr/bin/contextBro…"   2 minutes ago       Up 2 minutes (healthy)   0.0.0.0:1026->1026/tcp                                          docker_orion_1
32709dbc5701        grafana/grafana        "/run.sh"                2 minutes ago       Up 2 minutes             0.0.0.0:3000->3000/tcp                                          docker_grafana_1
ed9f8a60b6e8        crate:1.0.5            "/docker-entrypoint.…"   2 minutes ago       Up 2 minutes             0.0.0.0:4200->4200/tcp, 0.0.0.0:4300->4300/tcp, 5432-5532/tcp   docker_crate_1
76de9d756b7d        mongo:3.2              "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes             0.0.0.0:27017->27017/tcp                                        docker_mongo_1
92e2129fec9b        redis                  "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes             0.0.0.0:6379->6379/tcp                                          docker_redis_1
```

これで、[ユーザ・マニュアル](../user/using.md)の指示に従って
QuantumLeap を使用する準備が整いました。

あなたが実験を終えたら、解体することを忘れないでください。

```bash
# same path were you have placed the docker-compose-dev.yml
$ docker-compose -f docker-compose-dev.yml down -v
```

## Docker Swarm クラスタ上で HA に QuantumLeap をデプロイ

Docker Swarm Cluster 上のサービスとして HA　に QuantumLeap
サービスをデプロイするには、
[このリポジトリ](https://smartsdk-recipes.readthedocs.io/en/latest/data-management/quantumleap/readme/)
の指示に従います。

ここでは、**QuantumLeap** だけでなく、通常は展開シナリオの一部を構成する
補完的なサービスを展開する方法について説明します。

## 外部サービスインスタンスを再利用する QuantumLeap のデプロイ

すでに Orion をどこか別の場所で動かしていて、QuantumLeap
だけを展開したいのであれば、前のセクションで説明したように進めることができます。
しかし、実行の前に、`docker-compose.yml` ファイルから、`orion:` と
`mongo:` services の完全な定義を削除します。また、他のサービスの`depends_on:`
セクションで、それらへの参照を削除する必要があります。

同様に、*grafana* を使用したくない場合は、そのサービス定義も削除できます。
最終的には、最小機能の QuantumLeap のために必要なサービスは、Quantumleap
と時系列データベース (一般的な場合、`crate`)のみです。

またセットアップを完了するために、QuantumLeap を実行する必要が場合は、
単に以下を実行するだけです :

```bash
docker run -d -p 8668:8668 -e "CRATE_HOST=http://your_crate_location" orchestracities/quantumleap
```

環境変数 `CRATE_HOST` は、QuantumLeap に CrateDB に到達する場所を通知するので、
CrateDB が実行されている到達可能なホスト名を指定する必要があります。
デフォルトでは、QuantumLeap は ポート `4200` をホスト名に追加します。
もちろん、`-e` で必要な環境変数を追加することもできます。
他のオプションについては、
[docker run reference](https://docs.docker.com/engine/reference/run/)
を参照してください。

## Kubernetes への QuantumLeap のデプロイ

QuantumLeap サービスを Kubernetes にデプロイするには、
[このリポジトリ](https://smartsdk-recipes.readthedocs.io/en/latest/data-management/quantumleap/readme/)
の Helm チャートを活用できます。

特に、以下のコンポーネントをデプロイする必要があります:

* [CrateDB](https://github.com/orchestracities/charts/tree/master/charts/crate)
* [オプション/代替] Timescale - これについては、[Patroni Helm Chart](https://github.com/helm/charts/tree/master/incubator/patroni)
  を参照してください
* [QuantumLeap](https://github.com/orchestracities/charts/tree/master/charts/quantumleap)

## FIWARE Releases の互換性

現在のバージョンの QuantumLeap は、FIWARE release `6.3.1`
以上で互換性があります。FIWARE releases の詳細は
[こちら](https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Releases_and_Sprints_numbering,_with_mapping_to_calendar_dates)
をご覧ください。
Generic Enabler と外部依存関係の QL がどのバージョンで使用され、
テストされているかを確認するには、展開に使用される
[docker-compose-dev.yml](https://raw.githubusercontent.com/orchestracities/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
ファイルをチェックアウトします。
