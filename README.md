# Wiki Project Infrastructure CDK

AWS CDK (Python)によるWiki Projectのインフラストラクチャ定義です。

## 構成

```
WikiProject_Infra/
├── stacks/
│   ├── cognito_stack.py         # Cognito User Pool & Client
│   ├── dsql_stack.py            # Aurora DSQL Cluster
│   └── main_stack.py            # S3 + CloudFront
├── app.py                       # CDKアプリケーションエントリーポイント
├── buildspec.yml                # CodeBuild用ビルド仕様
├── config.json                  # 設定ファイル（環境変数、リソース名など）
├── config_sample.json           # 設定ファイルサンプル（CodeBuildで使用）
├── cdk.json                     # CDK設定
└── requirements.txt             # Python依存関係
```

## セットアップ

### 前提条件

- Python 3.11以上
- Node.js（CDK CLI用）
- AWS CLI設定済み（`aws configure`または`~/.aws/credentials`）
- AWS_PROFILE=wikiの設定（本プロジェクトでは`wiki`プロファイルを使用）

### 1. CDK CLIのインストール

```bash
npm install -g aws-cdk
cdk --version
```

### 2. Python仮想環境の作成と有効化

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate.bat
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. CDK Bootstrap（初回のみ）

CDKを初めて使用する環境では、`cdk bootstrap`を実行する必要があります。

#### 推奨：カスタムポリシーを使用（セキュリティ重視）

まず、最小権限のカスタムポリシーをデプロイします：

```bash
cd /Users/hakira/Programs/wambda-develop/WikiProject_Infra/init

AWS_PROFILE=wiki aws cloudformation deploy \
  --template-file cfn-execution-policies.yaml \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

次に、カスタムポリシーを使用してCDK bootstrapを実行します：

```bash
# ポリシーARNを動的に取得
POLICY_ARN=$(AWS_PROFILE=wiki aws cloudformation describe-stacks \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`PolicyArn`].OutputValue' \
  --output text)

# Bootstrap実行
AWS_PROFILE=wiki cdk bootstrap \
  --cloudformation-execution-policies ${POLICY_ARN} \
  --region ap-northeast-1
```

**注意**: `cdk bootstrap`は、CDKが使用するS3バケット、ECRリポジトリ、CloudFormation Execution Role等を作成します。環境（アカウント+リージョン）ごとに1回だけ実行すればOKです。

詳細は → **[init/README.md](init/README.md)**

### 5. config.jsonの設定値を編集

```json
{
  "account": null,
  "region": "ap-northeast-1",
  "cognito": {
    "user_pool_name": "user-pool-wiki-common",
    "client_name": "client-wiki-common",
    "ssm_prefix": "/Cognito"
  },
  "dashboard": {
    "domain_name": "dashboard.wiki.h-akira.net",
    "acm_certificate_arn": "arn:aws:acm:us-east-1:XXXXXXXXXXXX:certificate/...",
    "s3_bucket_name": "s3-wiki-dashboard-contents",
    "api_gateway": {
      "domain_name": "XXXXXXXXXX.execute-api.ap-northeast-1.amazonaws.com",
      "stage_name": "stage-01"
    },
    "codebuild": {
      "codestar_connection_arn": "arn:aws:codeconnections:...",
      "backend": {
        "project_name": "build-wiki-dashboard-backend",
        "github_owner": "h-akira",
        "github_repo": "WikiDashboardProject_Backend",
        "branch": "main"
      },
      "frontend": {
        "project_name": "build-wiki-dashboard-frontend",
        "github_owner": "h-akira",
        "github_repo": "WikiDashboardProject_Frontend",
        "branch": "main"
      }
    }
  }
}
```

## デプロイ

### 全スタックの確認

```bash
cdk ls
```

出力例:
```
stack-wiki-infra-cognito
stack-wiki-infra-dsql
stack-wiki-infra-main
```

### CloudFormationテンプレートの生成

```bash
cdk synth
```

### 個別スタックのデプロイ

```bash
# Cognitoスタック
AWS_PROFILE=wiki cdk deploy stack-wiki-infra-cognito

# DSQLスタック
AWS_PROFILE=wiki cdk deploy stack-wiki-infra-dsql

# Mainスタック
AWS_PROFILE=wiki cdk deploy stack-wiki-infra-main

# 全スタック一括デプロイ
AWS_PROFILE=wiki cdk deploy --all
```

### スタックの削除

```bash
AWS_PROFILE=wiki cdk destroy stack-wiki-infra-main
AWS_PROFILE=wiki cdk destroy stack-wiki-infra-dsql
AWS_PROFILE=wiki cdk destroy stack-wiki-infra-cognito
```

## CodeBuildによる自動デプロイ

このプロジェクトは、CodeBuildによるCI/CDパイプラインに対応しています。

### buildspec.ymlの動作

CodeBuild実行時、`buildspec.yml`が以下の処理を自動実行します：

1. **config.jsonの自動生成**
   - `config_sample.json`を`config.json`にコピー
   - Parameter Storeから必要な値を取得：
     - `/ACM/arn` → ACM証明書ARN
     - `/S3/contents/bucket_name` → S3バケット名
     - `/CloudFormation/app/stack_name` → アプリケーションスタック名
   - プレースホルダーを実際の値に置き換え
     - `REPLACE_WITH_ACM_CERTIFICATE_ARN` → ACM証明書ARN
     - `REPLACE_WITH_S3_BUCKET_NAME` → S3バケット名
     - `REPLACE_WITH_APP_STACK_NAME` → アプリケーションスタック名

2. **CDKデプロイ**
   - Python仮想環境(.venv)の作成
   - 依存関係のインストール
   - `cdk deploy --all`で全スタックをデプロイ

### 必要な事前設定

CodeBuildで自動デプロイするには、以下の設定が必要です：

1. **Parameter Storeに必要な値を保存**
   ```bash
   # ACM証明書ARN
   AWS_PROFILE=wiki aws ssm put-parameter \
     --name "/ACM/arn" \
     --value "arn:aws:acm:us-east-1:XXXXXXXXXXXX:certificate/XXXXXXXX" \
     --type String \
     --region ap-northeast-1

   # S3バケット名（グローバルに一意である必要があるため、Parameter Storeで管理）
   AWS_PROFILE=wiki aws ssm put-parameter \
     --name "/S3/contents/bucket_name" \
     --value "s3-wiki-contents-XXXXXXXXXXXX" \
     --type String \
     --region ap-northeast-1

   # アプリケーションスタック名
   AWS_PROFILE=wiki aws ssm put-parameter \
     --name "/CloudFormation/app/stack_name" \
     --value "stack-dummy-app" \
     --type String \
     --region ap-northeast-1
   ```

2. **CodeBuildプロジェクトの作成**

   `WikiProject_CICD`リポジトリの`codebuild-infra.yaml`を使用してCodeBuildプロジェクトを作成してください。

3. **GitHubへのPush**

   mainブランチへのPushで自動的にデプロイが実行されます。

### ローカル開発との違い

| 項目 | ローカル開発 | CodeBuild |
|------|-------------|-----------|
| config.json | 手動作成・編集 | buildspec.ymlで自動生成 |
| ACM ARN | config.jsonに直接記述 | Parameter Storeから取得 |
| S3バケット名 | config.jsonに直接記述 | Parameter Storeから取得 |
| アプリスタック名 | config.jsonに直接記述 | Parameter Storeから取得 |
| デプロイ | `cdk deploy`を手動実行 | GitHubへのPushで自動実行 |

## 主な機能

### stack-wiki-infra-cognito
- Cognito User Pool作成
- Cognito User Pool Client作成（シークレット付き）
- SSM Parameter Storeへの認証情報保存
- パスワードポリシー設定（最小8文字、大文字/小文字/数字/記号必須）
- トークン有効期限設定（Access/ID: 30分、Refresh: 5日）

### stack-wiki-infra-dsql
- Aurora DSQL Cluster作成
- クラスタエンドポイントをSSM Parameter Storeに保存
- 削除保護有効化

### stack-wiki-infra-main
- S3バケット作成（フロントエンド静的ファイル用）
- CloudFront Distribution作成
- Origin Access Control (OAC)設定
- カスタムドメイン設定（ACM証明書）
- API Gateway Originの設定（/accounts/*, /api/*）
- SPAルーティング対応（404→200 /index.html）

## 権限管理

CDKでは、**CDK実行者**（開発者/CI/CD）と**CloudFormation Execution Role**の2つのロールが関与します。

### CDK実行者（開発者）に必要な権限

```json
{
  "必要な権限": [
    "cloudformation:* (スタック操作)",
    "s3:* (CDKアセットバケットのみ)",
    "iam:PassRole (CloudFormation Execution Roleのみ)"
  ],
  "不要な権限": [
    "lambda:CreateFunction",
    "s3:CreateBucket (アプリのバケット)",
    "cognito-idp:*"
  ]
}
```

**重要**: CDK実行者には、リソース作成権限は不要です。実際のリソース作成は、`cdk bootstrap`で作成されるCloudFormation Execution Roleが行います。

---

## 注意事項

1. **client_secret**: Cognito Client SecretはCDKで自動的にSSMパラメータに保存されます。

2. **削除保護**: Cognito User PoolはRemovalPolicy.RETAINに設定されているため、`cdk destroy`でも削除されません。手動削除が必要です。

3. **ACM証明書**: 事前にus-east-1リージョンで証明書を作成しておく必要があります。

4. **Route53**: DNSレコード設定は含まれていません。手動で設定してください。

5. **CloudFormation Execution Role**: デフォルトではAdministratorAccess相当の権限が付与されます。本番環境では必ず`--cloudformation-execution-policies`でカスタムポリシー（[init/cfn-execution-policies.yaml](init/cfn-execution-policies.yaml)）を使用してください。

6. **API Gateway URL**: Dashboard MainスタックはSAMスタックからAPI Gateway URLを自動的にインポートします。`config.json`で`sam_stack_name`を指定する必要があります（詳細は「API Gateway URL の設定方法」参照）。

## 有用なコマンド

* `cdk ls`          - スタック一覧表示
* `cdk synth`       - CloudFormationテンプレート生成
* `cdk deploy`      - スタックデプロイ
* `cdk diff`        - デプロイ済みスタックとの差分表示
* `cdk destroy`     - スタック削除
* `cdk docs`        - CDKドキュメントを開く

## API Gateway URL の設定方法

Dashboard MainスタックはCloudFrontのOriginとしてAPI Gatewayを使用します。API Gateway URLは**SAMスタックから自動的にインポート**されます。

`config.json`で`backend_stack_name`を指定してください：

```json
{
  "dashboard": {
    "backend_stack_name": "stack-wiki-dashboard-backend-main",
    ...
  }
}
```

**前提条件**:
- SAMスタック（Backend）が先にデプロイされていること
- SAMテンプレートのOutputにExportが設定されていること（下記参照）

**SAMテンプレート（template.yaml）の設定**:
```yaml
Outputs:
  WikiDashboardApiUrl:
    Description: API Gateway endpoint URL for stage-01 for Wiki Dashboard Backend
    Value: !Sub "https://${MainAPIGateway}.execute-api.${AWS::Region}.amazonaws.com/stage-01/"
    Export:
      Name: !Sub "${AWS::StackName}-ApiUrl"
```

CDKはSAMスタックの`${StackName}-ApiUrl`というExport値を`Fn::ImportValue`で参照し、URLからドメイン名とステージ名を自動的に抽出してCloudFrontのOriginに設定します。

---

## デプロイ順序の推奨

依存関係を考慮した推奨デプロイ順序：

1. **Cognito** → 認証基盤（必須）
2. **DSQL** → データベース
3. **App（SAM）** → API Gateway作成（ダミーアプリまたは実際のアプリ）
4. **Main** → S3 + CloudFront（SAMスタックからAPI Gateway URLを自動取得）

```bash
# 1. Cognito
AWS_PROFILE=wiki cdk deploy stack-wiki-infra-cognito

# 2. DSQL
AWS_PROFILE=wiki cdk deploy stack-wiki-infra-dsql

# 3. App（SAM）をデプロイ
# ダミーアプリの場合：
cd dummy_app && sam build && sam deploy
# または実際のアプリの場合：
cd WikiProject_App && sam build && sam deploy

# 4. Main（SAMスタックからAPI Gateway URLを自動インポート）
AWS_PROFILE=wiki cdk deploy stack-wiki-infra-main
```

