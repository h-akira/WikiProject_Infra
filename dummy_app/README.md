# Wiki Project - Dummy Application

このディレクトリには、Wiki Projectの開発・テスト用のダミーアプリケーションが含まれています。

## 概要

このダミーアプリケーションは、実際のアプリケーションが開発されるまでの間、CloudFrontのオリジンとして使用するためのプレースホルダーです。シンプルな「Hello World」HTMLページを返すだけの最小限の実装です。

## 構成

- `template.yaml`: SAM テンプレート
- `samconfig.toml`: SAM設定ファイル
- `src/app.py`: Lambda関数（Hello World HTMLを返す）
- `src/requirements.txt`: Python依存関係（なし）

## デプロイ方法

### 前提条件

- AWS CLI がインストールされていること
- AWS SAM CLI がインストールされていること
- AWS認証情報が設定されていること

### デプロイコマンド

```bash
cd dummy_app

# ビルド
sam build

# デプロイ（samconfig.tomlの設定を使用）
sam deploy
```

### スタック名について

`samconfig.toml`および`config_sample.json`の`main.app_stack_name`に指定されているスタック名と一致させる必要があります。

デフォルト: `stack-dummy-app`

## 出力

このスタックは以下の出力をエクスポートします:

- `{StackName}-ApiUrl`: API GatewayのエンドポイントURL
- `{StackName}-ApiId`: API GatewayのID

これらは`stack-wiki-infra-main`スタック（CloudFront）から参照されます。

## 実際のアプリケーションへの置き換え

実際のアプリケーションが準備できたら、このダミーアプリケーションを削除し、実際のアプリケーションスタックに置き換えてください。

置き換え時の注意事項:
- スタック名は`config_sample.json`の設定と一致させること
- `{StackName}-ApiUrl`の出力（Export）を必ず含めること
- CloudFrontスタックを先にデプロイしている場合は、一度削除してから再デプロイすること
