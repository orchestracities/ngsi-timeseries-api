# コントリビューション

コントリビューションはプルリクエストの形でより歓迎します。

作業する[未解決の問題](https://github.com/orchestracities/ngsi-timeseries-api/issues)
の1つを選択するか、自分の必要に応じて拡張機能を提供することができます。
いずれにしても、事前に連絡を取り、コントリビューションが現在の開発状況と一致する
ことを確認することをお勧めします。

コントリビューションの手順 :

1. リポジトリをフォークし、ローカル開発環境にフォークをクローンします
1. コードへのモジュラー・コントリビューションを特定します。
   レビューを単純化するにはあまりにも多くのコントリビューションを避けます
1. "モジュラー・コントリビューション"に取り組むブランチをリポジトリに作成します
   - 異なる機能を取り組むための複数のコントリビューションについては、
   異なるブランチを作成してください
   - すべての新しい機能について、テストを提供します。テストをローカルで実行する
   方法を理解するには、root で `setup_dev_env.sh` と `run.sh`
   を参照してください
1. 完了したら、すべてのテストが合格であることを確認します
1. もしそうなら、私たちのリポジトリに対してプル・リクエストを作成します。
   失敗したテストでプル・リクエストをレビューすることはできません
1. レビューを待つ
   - 必要な変更を実装する
   - 承認まで繰り返す
1. 完了:) あなたのリポジトリ内のブランチを削除できます

最終的に、コントリビューション・ガイドは、FIWARE
が提案したガイドと一貫していなければなりません。
([ここ](https://github.com/Fiware/developmentGuidelines/blob/master/external_contributions.mediawiki)
をご覧ください)

## 開発のセットアップ

開発は今のところほとんどが *python3* に基づいており、
実際には初期段階にありますので、事態は確実に変わります。
今のところ、あなたは以下から始めることができます :

```bash
$ git clone https://github.com/smartsdk/ngsi-timeseries-api.git
cd ngsi-timeseries-api
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# if you want to test everything locally, you'll need to...
source setup_dev_env.sh
```

Gunicorn で QuantumLeap WSGI アプリを使用する方法の詳細:

```bash
$ cd ngsi-timeseries-api/src
gunicorn server.wsgi --config server/gconfig.py
```

セキュリティ設定:

### limit_request_line

```bash
--limit-request-line INT
4094
```

バイト単位の HTTP リクエスト・ラインの最大サイズ。このパラメータは、クライアントの HTTP リクエスト・
ラインの許容サイズを制限するために使用されます。

### limit_request_fields

```bash
--limit-request-fields INT
100
```

このパラメータは、DDOS 攻撃を防ぐために、リクエスト内のヘッダの数を制限するために使用されます。
limit_request_field_size と一緒に使用すると、より安全になります。 デフォルトでは、この値は 100
であり、32768 を超えることはできません。

### limit_request_field_size

```bash
--limit-request-field_size INT
8190
```

HTTP リクエスト・ヘッダ・フィールドの許容サイズを制限します。
値は正の数または0です。0に設定すると、ヘッダ・フィールドのサイズを無制限に設定できます。

[pytest](https://docs.pytest.org/en/latest/)
はテストフレームワークとして使用されますが、QuantumLeap
の機能のほとんどはコンポーネントの統合であるため、テスト・フォルダの
`docker-compose.yml` ファイルがテストのセットアップとして実行されます。
`.travis.yml` ファイルが表示されている場合は、それらのファイルがどのように
動作しているかが分かりますが、*pytest-docker* プラグインを調べる価値があります。

`requirements.txt` は、テストとプロダクションの間で分割する必要があります。
そのため、Docker のイメージは今のところ大規模です。

## リポジトリ構造

現在のプロジェクト・ツリー構造では、次のとおりです：

- `ngsi-timeseries-api`
  - `docs`: ドキュメント・ファイルを保持します
  - `docker`: プロジェクトのスコープのために Docker 関連のファイルを保持します
  - `experiments`: サンドボックスを使用して迅速な手動テストを行い、
    新しいテストケースを導き出します
  - `specification`: QL が実装する OpenAPI 定義を含みます
  - `src`: ソース・コード・フォルダー
    - `geocoding`: OSMと対話し、ジオ関連の処理を行うためのコードを保持します
    - `reporter`: 通知および API リクエストのレシーバーとして機能する
    モジュール。トランスレータにタスクをハンドリングする前に、それらを
    "解析/検証" します
    - `translators`: 各時系列データベースの特定のトランスレータ。
    下位レベルのデータベースの詳細とのやり取りを行います
    - `utils`: 住みやすい場所を探している共通の共有物
