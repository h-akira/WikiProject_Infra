# CDK Bootstrap用の初期設定

このディレクトリには、CDKのCloudFormation実行ロールにカスタム権限を付与するためのCloudFormationテンプレートが含まれています。

## 概要

CDKでは、デプロイ時に**2つの異なるロール**が使用されます:

1. **CDK実行者（開発者/CI-CD）**: CloudFormationスタックの作成・更新操作のみを実行
2. **CloudFormation実行ロール**: 実際のAWSリソース（Cognito、S3、Lambda等）を作成・削除

このテンプレートは、Wiki Projectで実際に必要な**最小限の権限**のみを定義したカスタムポリシーを作成します。

## ポリシー構成

セキュリティと管理性を向上させるため、権限は**4つの独立したポリシー**に分割されています:

### Policy 1: Cognito & DSQL
- Cognito User Pool/Client作成・管理
- Aurora DSQL クラスタ作成・管理

### Policy 2: S3 & CloudFront
- S3バケット作成・管理
- CloudFront Distribution作成・管理

### Policy 3: Config (SSM & ACM)
- SSM Parameter Store作成・管理
- ACM証明書参照（読み取り専用）
- Lambda関数作成・管理
- CloudWatch Logs作成・管理

### Policy 4: IAM
- IAMロール・ポリシー作成・管理
- PassRole権限（制限付き）

## 付与される権限

このポリシーセットが許可するAWSサービス:

| サービス | 用途 | ポリシー | スコープ |
|---------|------|---------|---------|
| **Cognito** | User Pool/Client作成 | Policy 1 | User Poolのみ |
| **Aurora DSQL** | データベースクラスタ作成 | Policy 1 | DSQLクラスタのみ |
| **S3** | バケット作成・管理 | Policy 2 | 全バケット（CDKが管理） |
| **CloudFront** | Distribution作成・管理 | Policy 2 | 全リソース（必須） |
| **SSM Parameter Store** | パラメータ作成・管理 | Policy 3 | 全パラメータ |
| **ACM** | 証明書参照（読み取り専用） | Policy 3 | 全リソース（読み取りのみ） |
| **Lambda** | 関数作成・管理 | Policy 3 | 全関数 |
| **CloudWatch Logs** | ロググループ作成・管理 | Policy 3 | Lambda用ロググループ |
| **IAM** | ロール・ポリシー作成 | Policy 4 | 全ロール（PassRoleは制限付き） |

## デプロイ手順

### 1. カスタムポリシーをデプロイ

```bash
cd /Users/hakira/Programs/WikiProject/WikiProject_Infra/init

aws cloudformation deploy \
  --template-file cfn-execution-policies.yaml \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

**CAPABILITY_NAMED_IAM**: IAM Managed Policyを作成するために必要

### 2. ポリシーARNを確認

```bash
# 全ポリシーARNを取得
aws cloudformation describe-stacks \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`AllPolicyArns`].OutputValue' \
  --output text
```

出力例:
```
arn:aws:iam::XXXXXXXXXXXX:policy/policy-wiki-infra-cfn-exec-cognito-dsql,arn:aws:iam::XXXXXXXXXXXX:policy/policy-wiki-infra-cfn-exec-storage,arn:aws:iam::XXXXXXXXXXXX:policy/policy-wiki-infra-cfn-exec-config,arn:aws:iam::XXXXXXXXXXXX:policy/policy-wiki-infra-cfn-exec-iam
```

### 3. CDK Bootstrapでカスタムポリシーを指定

**新規環境の場合**:
```bash
# 各ポリシーARNを取得
COGNITO_DSQL_ARN=$(aws cloudformation describe-stacks \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoDSQLPolicyArn`].OutputValue' \
  --output text)

STORAGE_ARN=$(aws cloudformation describe-stacks \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`StoragePolicyArn`].OutputValue' \
  --output text)

CONFIG_ARN=$(aws cloudformation describe-stacks \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ConfigPolicyArn`].OutputValue' \
  --output text)

IAM_ARN=$(aws cloudformation describe-stacks \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`IAMPolicyArn`].OutputValue' \
  --output text)

# Bootstrap実行
cdk bootstrap \
  --cloudformation-execution-policies "${COGNITO_DSQL_ARN},${STORAGE_ARN},${CONFIG_ARN},${IAM_ARN}" \
  --region ap-northeast-1
```

**既存のbootstrap環境を更新する場合**:
```bash
# 既存のbootstrapスタックを削除（注意: CDKで管理されているリソースがある場合は削除しないこと）
aws cloudformation delete-stack \
  --stack-name CDKToolkit \
  --region ap-northeast-1

# スタック削除完了を待つ
aws cloudformation wait stack-delete-complete \
  --stack-name CDKToolkit \
  --region ap-northeast-1

# 新しいポリシーでbootstrap（上記コマンドを実行）
```

### 4. 確認

```bash
# CloudFormation実行ロールを確認
aws iam get-role \
  --role-name cdk-hnb659fds-cfn-exec-role-XXXXXXXXXXXX-ap-northeast-1

# アタッチされているポリシーを確認
aws iam list-attached-role-policies \
  --role-name cdk-hnb659fds-cfn-exec-role-XXXXXXXXXXXX-ap-northeast-1
```

出力に以下の4つのポリシーが含まれていればOK:
- `policy-wiki-infra-cfn-exec-cognito-dsql`
- `policy-wiki-infra-cfn-exec-storage`
- `policy-wiki-infra-cfn-exec-config`
- `policy-wiki-infra-cfn-exec-iam`

## ポリシーの更新

新しいAWSサービスを使用する場合、ポリシーを更新する必要があります。

### 1. cfn-execution-policies.yamlを編集

必要な権限を適切なポリシーセクションに追加します。

### 2. スタックを更新

```bash
cd /Users/hakira/Programs/WikiProject/WikiProject_Infra/init

aws cloudformation deploy \
  --template-file cfn-execution-policies.yaml \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

**重要**: ポリシーは自動的に既存のCloudFormation実行ロールに反映されます（Managed Policyのため）。Bootstrap再実行は不要です。

### 3. 変更内容を確認

```bash
# 例: Cognito & DSQLポリシーの確認
POLICY_ARN=$(aws cloudformation describe-stacks \
  --stack-name stack-wiki-infra-cfn-execution-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CognitoDSQLPolicyArn`].OutputValue' \
  --output text)

aws iam get-policy-version \
  --policy-arn ${POLICY_ARN} \
  --version-id v2  # バージョンは増加します
```

## CI/CD統合

buildspec.ymlでは、自動的にポリシーARNを取得してCDK bootstrapを実行します:

```yaml
env:
  variables:
    CDK_EXECUTION_POLICIES_STACK_NAME: "stack-wiki-infra-cfn-execution-policies"

pre_build:
  commands:
    # 各ポリシーARNを動的に取得
    - COGNITO_DSQL_ARN=$(aws cloudformation describe-stacks ...)
    - STORAGE_ARN=$(aws cloudformation describe-stacks ...)
    - CONFIG_ARN=$(aws cloudformation describe-stacks ...)
    - IAM_ARN=$(aws cloudformation describe-stacks ...)

    # Bootstrap実行
    - cdk bootstrap --cloudformation-execution-policies "${COGNITO_DSQL_ARN},${STORAGE_ARN},${CONFIG_ARN},${IAM_ARN}" ...
```

## トラブルシューティング

### デプロイ時に権限エラーが発生する

**エラー例**:
```
User: arn:aws:sts::XXXXXXXXXXXX:assumed-role/cdk-hnb659fds-cfn-exec-role-XXXXXXXXXXXX-ap-northeast-1/AWSCloudFormation is not authorized to perform: xxx:CreateXXX
```

**原因**: CloudFormation実行ロールに必要な権限が不足

**対処法**:
1. エラーメッセージから不足している権限を特定（例: `dsql:CreateCluster`）
2. `cfn-execution-policies.yaml`の適切なポリシーセクションに権限を追加
3. スタックを更新（上記「ポリシーの更新」参照）
4. CDKデプロイを再実行

## ベストプラクティス

1. **定期的な監査**: 不要な権限が含まれていないか定期的にレビュー
2. **バージョン管理**: cfn-execution-policies.yamlは必ずGit管理する
3. **変更記録**: ポリシー変更時は理由をコミットメッセージに記載
4. **ポリシー分離**: 新しいサービスを追加する場合、適切なポリシーセクションに追加する

## 参考資料

- [AWS CDK Bootstrap](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)
- [CloudFormation Execution Policies](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html#bootstrapping-customizing)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Aurora DSQL Documentation](https://docs.aws.amazon.com/aurora-dsql/)
