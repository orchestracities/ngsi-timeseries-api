# トラブルシューティング

期待どおりに動作しないものがありますか? 心配しないでください!
期待されることはそれが働かないことです :p。

次のセクションをチェックして、重要なステップを逃していないことを確認し、
該当するものがなければ、**バグ報告**に進みます。

## よくある質問

#### 指示に従いましたが、何も起こりません

データがデータベースに保存されていない場合は、
バグを報告する前に次の質問をしてください。

- 挿入するエンティティ型のサブスクリプションを作成しましたか?

サブスクリプションは NGSIv2 で、"keyValues" オプションはありませんか?
[Orion Subscriptions Docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
を確認してください。

- サブスクリプションの "条件" にリストされている属性を挿入/更新していますか?

つまり、Orion は挿入/更新の通知をトリガーしますか?


- Orion のサブスクリプションにクエリと、そのようなサブスクリプションが

表示されますか？その "last_success" はいつですか?

- サブスクリプションの *notify_url* フィールドに QuantumLeap

の場所が表示されていますが、これは、コンテナ化された Orion の解決可能な URL
ですか? 詳細については、[利用](./index.md)のセクションを参照してください。


- ファイアウォールの背後にあるさまざまなコンポーネントを実行していますか?

もしそうなら、対応するポートを開きましたか?
[ポート](../admin/ports.md)のセクションを参照してください。

#### データを取得できません

- テナントに正しい FIWARE ヘッダを使用していますか？

ドキュメントのマルチ・テナンシーのパートを参照してください。

- 使用しているエンドポイントは実装されていますか?

今はいくつかは実装されていないことに注意してください。
これらは API 仕様でフラグが立てられています。

- 間違っていた可能性のあるヒントについては、

返されたボディのメッセージを見てください。
リクエストに重要なパラメータがないかもしれません。


#### Grafana では CrateDB Datasource は利用できません

デフォルトでは、QuantumLeap レシピは、CrateDB のプラグインがすでにインストールされている Grafana をデプロイします。

[Grafana セクション](../admin/grafana.md)で説明されているように
データソースを作成中にオプションとして CrateDB が表示されない場合は、Grafana
コンテナがインターネット接続に失敗したか、
プラグインのダウンロードとインストールに失敗したか、または プラグインを
インストールする必要がある外部 Grafana インスタンスを使用しています。

CrateDB のデータソース・プラグインのドキュメントはここで、一般的に、Grafana
プラグインのインストールに関するドキュメントは
[ここ](http://docs.grafana.org/plugins/installation/)です。

## バグ・レポート

バグは、github リポジトリの
[issues](https://github.com/smartsdk/ngsi-timeseries-api/issues)
の形で報告する必要があります。

繰り返される issues を報告する前に、既に報告された issues を見てください :)

できるだけ多くのコンテキスト情報を含め、理想的には次のものも含めます。

- 問題を引き起こした可能性のある挿入されたエンティティ。例えば :

        {
            'id': 'MyEntityId',
            'type': 'MyEntityType',
            'attr1': 'blabla',
            ...
        }

- あなたが作成したサブスクリプションのペイロード。Orionのドキュメントの

[このセクション](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
を参照してください。

- QuantumLeap コンテナのログ

Swarm にサービスとして、QuantumLeap を展開した場合は、
[docker logs command](https://docs.docker.com/engine/reference/commandline/logs/#options)
または
[docker service logs](https://docs.docker.com/engine/reference/commandline/service_logs/)
を使用してログを取得できます。最初のケースでは、`docker ps -a`
を使用してコンテナ id を検出できます。2番目のケースでは、`docker service ls`
を使ってサービス名を探します。
