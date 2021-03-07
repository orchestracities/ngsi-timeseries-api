# トラブルシューティング

期待どおりに動作しないものがありますか? 心配しないでください!
期待されることはそれが働かないことです :p。

次のセクションをチェックして、重要なステップを逃していないことを確認し、
該当するものがなければ、**バグ報告**に進みます。

## よくある質問

### 指示に従いましたが、何も起こりません

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

### データを取得できません

- テナントに正しい FIWARE ヘッダを使用していますか？

ドキュメントのマルチ・テナンシーのパートを参照してください。

- 使用しているエンドポイントは実装されていますか?

今はいくつかは実装されていないことに注意してください。
これらは API 仕様でフラグが立てられています。

- 間違っていた可能性のあるヒントについては、

返されたボディのメッセージを見てください。
リクエストに重要なパラメータがないかもしれません。

### エラーはありませんでしたが、ダッシュボードにデータが表示されません

データベースに十分なデータポイントがあること、および選択したタイムスライス
(grafana の右上隅) が実際にデータがある時間範囲をカバーしていることを確認
してください。

### CrateDB をバックエンドとして使用すると、3D 座標が機能しません

次のようなエラーを見つけた場合：

```bash
crate.client.exceptions.ProgrammingError: SQLActionException[ColumnValidationException: Validation failed for location: Cannot cast {"coordinates"=[51.716783624, 8.752131611, 23], "type"='Point'} to type geo_shape]
```

これは、[管理ドキュメント](../admin/crate.md)に記載されているとおり
CrateDB が 3D 座標をサポートしていないという事実に関連しています。

## バグ・レポート

バグは、github リポジトリの
[issues](https://github.com/orchestracities/ngsi-timeseries-api/issues)
の形で報告する必要があります。

重複した issues を報告する前に、既に報告された issues を見てください :)

できるだけ多くのコンテキスト情報を含め、理想的には次のものも含めます。

- 問題を引き起こした可能性のある挿入されたエンティティ。例えば :

  ```json
  {
      'id': 'MyEntityId',
      'type': 'MyEntityType',
      'attr1': 'blabla',
      ...
  }
  ```

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
