# インフラ構成 (AWS Free Tier 中心)

以下は可能な限り無料利用枠のみで構成した例です。

---

## 1. リージョン
- ap-northeast-1 (東京)

## 2. VPC / ネットワーク
- **VPC**: 1つの専用VPC
- **サブネット**
  - Public Subnet ×2 (Fargate タスクに直接割り当て、NAT Gateway不要)
  - Private Subnet ×2 (RDS 配置用)
- **セキュリティグループ**
  - ALB / Fargate (HTTP/HTTPS)
  - ECSタスク → RDS (PostgreSQL: 5432)

## 2-1. Cloudflare での DNS 設定（手動）
- Cloudflare ダッシュボードにログイン
- 対象ドメイン（例: `smartao.com`）の **DNS** ページを開く
- **CNAME レコードを追加 (frontend)**
  - **Type**: CNAME
  - **Name**: `stg`  （`stg.smartao.com`）
  - **Target / Content**: フロントエンド ALB の DNS 名 (例: `smartao-front-stg-xxxxxx.elb.amazonaws.com`)
  - **TTL**: Auto
  - **Proxy status**: DNS only（オレンジ雲オフ） or Proxied（オレンジ雲オン）
- **CNAME レコードを追加 (backend)**
  - **Type**: CNAME
  - **Name**: `stg-api`  （`stg-api.smartao.com`）
  - **Target / Content**: バックエンド ALB の DNS 名 (例: `smartao-api-stg-yyyyyy.elb.amazonaws.com`)
  - **TTL**: Auto
  - **Proxy status**: DNS only（オレンジ雲オフ） or Proxied（オレンジ雲オン）
- 保存後、数秒～数分で両サブドメインが ALB を経由して ECS Fargate に向くようになります。

## 3. コンテナオーケストレーション (ECS Fargate)
- **ECR**
  - リポジトリ: `backend`, `frontend`
  - 月500MBまで無料
- **ECS クラスター**
  - バックエンド: `smartao-api-stg`
  - フロントエンド: `smartao-front-stg`
- **サービス**
  - `smartao-api-stg-service`, `smartao-front-stg-service`
- **タスク定義**
  - cpu: 256 / memory: 512
  - networkMode: `awsvpc` / assignPublicIp: ENABLED
- **ログ**
  - CloudWatch Logs へ出力 (5GB/月まで無料)

## 4. データベース (RDS for PostgreSQL)
- インスタンスタイプ: db.t3.micro (無料枠)
- ストレージ: 20GB General Purpose (gp2)
- Multi-AZ: 無効 (コスト削減)
- パラメータグループ: デフォルト
- 接続: ECSタスクのセキュリティグループ経由

## 5. メール送信 (SES)
- **無料枠**: 月62,000通まで
- ドメイン/メールアドレス検証済み
- バウンス・苦情通知は SNS へ連携可能
- アプリケーションから AWS SDK(v3) 経由で送信

## 6. 設定管理 / シークレット管理
- AWS Systems Manager Parameter Store (無料枠)
  - 非機密環境変数の管理
- AWS Secrets Manager
  - DB接続情報やAPIキーなど機密情報を安全に注入

## 7. SSL/TLS
- AWS Certificate Manager で無料証明書発行
- ALB または CloudFront へアタッチ

## 8. CI/CD
- GitHub Actions (無料枠)
  - イメージビルド & ECR プッシュ
  - ECS タスク定義更新 & サービスデプロイ
  - DBマイグレーション & シードデータ導入

## 9. 監視・アラート
- CloudWatch Metrics (10メトリクスまで無料)
- CloudWatch Logs Insights
- 必要に応じて CloudWatch Alarm で通知

## 10. コスト最適化
- NAT Gateway は使用せず、パブリックIP直接割当
- マルチAZ無効化
- ストレージ & ログ量は無料枠内に収める

---

※ 本構成は小規模開発 / ステージング用途を想定し、AWS無料利用枠を最大限活用しています。
