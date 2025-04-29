# STG 環境 インフラセットアップ手順

このドキュメントでは、ステージング（STG）環境のインフラをゼロから構築する手順をまとめています。

---

## 前提条件
1. AWS CLI v2 がインストールされ、`aws configure` で認証情報が設定済み
2. Terraform 1.5.0 以上がインストール済み
3. GitHub リポジトリに以下のシークレットが登録済み
   - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION` (例: `ap-northeast-1`)
   - `AWS_ECR_REGISTRY` (例: `123456789012.dkr.ecr.ap-northeast-1.amazonaws.com`)
   - `DB_PASSWORD` （RDS マスターDBのパスワード）
   - `API_BASE_URL` （例: `https://stg-api.smartao.jp`）
   - `STG_SUBNETS`（サブネットIDカンマ区切り）
   - `STG_SECURITY_GROUPS`（セキュリティグループIDカンマ区切り）

---

## 0. 環境変数の設定
本手順で利用する環境変数・シークレットと管理方法は以下のとおりです。

### GitHub シークレット
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY  : AWS認証情報
- AWS_REGION                           : AWSリージョン (例: ap-northeast-1)
- AWS_ECR_REGISTRY                     : ECRレジストリURI
- DB_PASSWORD                          : RDS マスターDBのパスワード
- API_BASE_URL                         : フロントエンドが利用するAPIのベースURL (例: https://stg-api.smartao.jp)
- STG_SUBNETS                          : Terraform で作成するサブネットIDをカンマ区切りで指定
- STG_SECURITY_GROUPS                  : Terraform で作成するセキュリティグループIDをカンマ区切りで指定

### Terraform 変数（TF_VAR）
- TF_VAR_db_password   = DB_PASSWORD と同じ値を参照
- TF_VAR_api_base_url  = API_BASE_URL と同じ値を参照

### コンテナ環境変数注入
- **バックエンド（ECS Task）**: Secrets Manager に登録した `backend/env` シークレットを `aws_ecs_task_definition` の `secrets` で注入
- **フロントエンド（ECS Task）**: SSM Parameter Store の `/stg/api-base-url` を `environment` で注入
- Docker Compose ローカル開発用には `backend/.env.stg` および `study-support-app/.env.stg` を参照

---

## 1. リポジトリのクローン
```bash
git clone <repository-url>
cd react_ai_chatapp
```

---

## 2. Terraform 変数の設定
1. `infrastructure/terraform`ディレクトリへ移動
   ```bash
   cd infrastructure/terraform
   ```
2. 変数ファイルの準備
   - `terraform.tfvars` を作成し、以下を記載
     ```hcl
     db_password    = "<RDS マスターDB パスワード>"
     api_base_url   = "https://stg-api.smartao.jp"
     ```
   - または、環境変数としてエクスポート
     ```bash
     export TF_VAR_db_password="<RDS パスワード>"
     export TF_VAR_api_base_url="https://stg-api.smartao.jp"
     ```

---

## 3. STG インフラ構築 (Terraform)
### GitHub Actions から実行
1. GitHub 上の **Actions** タブ → **STG Terraform Infra Setup** ワークフローを選択
2. 「Run workflow」を押し、必要に応じて入力フォームからブランチやシークレットを確認
3. 実行後、以下のリソースが無料枠中心で作成されます:
   - VPC / Public・Private サブネット
   - セキュリティグループ (アプリ用 / RDS用)
   - ALB (フロント / バックエンド) とターゲットグループ・HTTPリスナー
   - ECR リポジトリ (backend, frontend)
   - ECS クラスター
   - RDS for PostgreSQL (db.t3.micro / 20GB)
   - SSM Parameter Store, Secrets Manager

### CLI から実行
```bash
cd infrastructure/terraform
terraform init -input=false
terraform plan -input=false -out=tfplan
terraform apply -input=false -auto-approve tfplan
```

---

## 4. DNS（Cloudflare）設定
1. Cloudflare ダッシュボード → 対象ドメインの **DNS** ページを開く
2. **CNAME レコード** を追加
   - フロントエンド  
     - **Name**: `stg`（`stg.smartao.jp`）  
     - **Target**: フロント ALB の DNS 名  
   - バックエンド  
     - **Name**: `stg-api`（`stg-api.smartao.jp`）  
     - **Target**: バックエンド ALB の DNS 名  
3. TTL: Auto, Proxy status: お好みで (DNS only / Proxied)

---

## 5. アプリケーションデプロイ (STG)
1. `stg` ブランチへコードをプッシュ
2. GitHub Actions の `Build & Push STG Docker Images to ECR` が自動実行
   - Docker イメージのビルド & ECR プッシュ
   - ECS タスク定義更新 & サービスデプロイ
   - DB マイグレーション (Fargate run-task により実行)

---

## 6. 確認方法
- CloudWatch Logs で各サービスのログを確認
- ALB のターゲットグループでヘルスチェックステータスを確認
- ブラウザで `https://stg.smartao.jp` や `https://stg-api.smartao.jp` にアクセス

以上でステージング環境のインフラ構築からアプリデプロイまでが完了します。
