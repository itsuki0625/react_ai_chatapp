# バックエンドサービス

## 概要
学習支援アプリケーションのバックエンドサービスです。主な機能：
- ユーザー認証
- チャット機能（OpenAI API連携）
- 大学情報管理
- 志望校管理
- サブスクリプション決済（Stripe連携）

## データモデル

アプリケーションは以下の主要なデータモデルで構成されています：

### ユーザー管理
- **User**: ユーザー情報（学生、教師など）
  - 基本属性: メールアドレス、ハッシュ化されたパスワード、氏名、プロフィール画像
  - 学校情報: 学校ID、学年、クラス、学籍番号
  - 関連: ロール、チャットセッション、志望校情報、サブスクリプション
- **Role**: ユーザーロール（管理者、学生、教師など）
  - 権限管理に使用

### チャット機能
- **ChatSession**: チャットのセッション情報
  - セッションタイプ、ステータス、メタデータ
  - ユーザーとの関連付け
- **ChatMessage**: チャット内の個別メッセージ
  - 送信者情報、内容、メッセージタイプ
  - 既読状態の管理
- **ChatAttachment**: チャットに添付されたファイル
  - ファイルURL、タイプ、サイズ

### 大学・学校情報
- **University**: 大学情報
  - 基本情報: 名称、コード、住所、連絡先
  - 関連: 学部情報
- **Department**: 大学の学部情報
  - 学部名、コード、説明
- **School**: 高校などの学校情報
  - 基本情報と関連ユーザー

### 志望校管理
- **DesiredSchool**: ユーザーの志望校情報
  - 志望する大学、志望順位
  - 受験方式、受験日程
- **DesiredDepartment**: 志望学部情報
  - 志望学部と関連情報

### サブスクリプション決済
- **Subscription**: ユーザーのサブスクリプション情報
  - Stripe情報: 顧客ID、サブスクリプションID
  - ステータス、プラン名、価格ID
  - 期間情報、キャンセル情報
- **PaymentHistory**: 支払い履歴
  - 支払い情報: 金額、通貨、ステータス
  - Stripe関連ID (決済ID、請求書ID)
- **CampaignCode**: キャンペーンコード情報
  - コード、割引タイプ、割引額/率
  - 有効期限、最大使用回数

### その他
- **ChecklistEvaluation**: チェックリスト評価
- **Content**: 教材コンテンツ
- **Schedule**: スケジュール情報
- **Document**: 文書管理
- **PersonalStatement**: 志望理由書

## 技術スタック
- **FastAPI**: Webフレームワーク
- **PostgreSQL**: データベース
- **SQLAlchemy**: ORMツール
- **Alembic**: マイグレーションツール
- **Stripe**: 決済処理
- **OpenAI API**: チャット機能

## システム構成
- **バックエンド**: FastAPI (ポート: 5050)
- **フロントエンド**: Next.js (ポート: 3000)
- **データベース**: PostgreSQL (ポート: 5020)

## セットアップ方法

### 1. 環境変数の設定
`.env.example`ファイルをコピーして`.env`ファイルを作成します：
```bash
cp .env.example .env
```

**必須環境変数**：
```
# データベース設定
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=demo
DATABASE_URL=postgresql://user:password@db:5432/demo

# 認証・暗号化
SECRET_KEY=あなたの秘密鍵

# OpenAI API
OPENAI_API_KEY=あなたのOpenAI APIキー

# サーバー設定
PORT=5050

# フロントエンド設定
NEXT_PUBLIC_BACKEND_URL=http://localhost:5050
NEXT_PUBLIC_API_BASE_URL=http://localhost:5050

# Stripe決済設定
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxx
STRIPE_PRICE_ID=price_xxxxxxxxxxxxxxxx

# NextAuth.js設定（フロントエンド用）
NEXTAUTH_URL=http://localhost:3030
NEXTAUTH_SECRET=あなたのNextAuth秘密鍵
```

### 2. Docker起動
Docker Composeを使用してサービスを起動します：
```bash
docker-compose up -d
```

サービス構成：
- `backend`: FastAPIアプリケーション（ポート5050）
- `frontend`: Next.jsアプリケーション（ポート3000）
- `db`: PostgreSQLデータベース（内部ポート5432、外部ポート5020）

### 3. マイグレーション実行
データベーススキーマを初期化します：
```bash
docker-compose exec backend alembic upgrade head
```

### 4. アクセス方法
- バックエンドAPI: http://localhost:5050
- API ドキュメント: http://localhost:5050/docs
- フロントエンド: http://localhost:3000

## 決済機能（Stripe）

### セットアップ手順
1. [Stripeダッシュボード](https://dashboard.stripe.com/)でアカウント作成
2. APIキー（シークレットキーと公開キー）を取得し`.env`に設定
3. 商品・プラン作成と価格ID取得（STRIPE_PRICE_ID）
4. ウェブフックシークレットを取得し設定（STRIPE_WEBHOOK_SECRET）

### サブスクリプション管理
データベースにプランを追加するサンプルコード:

```python
# サブスクリプションプラン作成例
from app.schemas.subscription import SubscriptionPlanCreate
from app.crud.subscription import create_subscription_plan
from sqlalchemy.orm import Session

def create_plans(db: Session):
    basic_plan = SubscriptionPlanCreate(
        name="ベーシックプラン",
        description="基本機能が利用可能なプラン",
        price_id="price_xxxxxxxxxxxxx",  # Stripeの価格ID
        amount=980,
        currency="jpy",
        interval="month",
        is_active=True
    )
    create_subscription_plan(db, basic_plan)
```

### キャンペーンコード機能
キャンペーンコードの特徴:
- 割引タイプ: パーセント割引/固定金額割引
- 所有者設定: アフィリエイトトラッキング対応
- 有効期限・使用回数制限設定可能
- 有効/無効切替機能

### Stripeウェブフック設定
エンドポイント: `/api/v1/subscriptions/webhook`

監視イベント:
- `checkout.session.completed`
- `invoice.paid`/`invoice.payment_failed`
- `customer.subscription.*` (created/updated/deleted)

## API一覧

### サブスクリプション関連
- `GET /api/v1/subscriptions/plans`: プラン一覧取得
- `GET /api/v1/subscriptions/user-subscription`: ユーザーサブスクリプション情報
- `GET /api/v1/subscriptions/payment-history`: 支払履歴
- `POST /api/v1/subscriptions/create-checkout`: チェックアウト作成
- `POST /api/v1/subscriptions/create-portal-session`: 管理ポータル作成
- `POST /api/v1/subscriptions/manage-subscription`: サブスクリプション操作

### キャンペーンコード関連
- `POST /api/v1/subscriptions/verify-campaign-code`: コード検証
- `GET/POST /api/v1/subscriptions/campaign-codes`: 一覧取得/作成
- `GET/PUT/DELETE /api/v1/subscriptions/campaign-codes/{id}`: 詳細/更新/削除

## トラブルシューティング

### よくある問題
1. **データベース接続エラー**：Docker起動後すぐにバックエンドが接続できない場合は、少し待ってからリトライしてください
2. **Stripeウェブフックテスト**：ローカル開発環境でStripeウェブフックをテストするには [Stripe CLI](https://stripe.com/docs/stripe-cli) を使用してください
3. **ポートの競合**：ポート5050や3000が既に使用されている場合は、docker-compose.ymlで別のポートに変更してください

## 開発ガイドライン
- **APIエンドポイント**: `app/api/v1/endpoints/`にルーター作成
- **モデル**: `app/models/`にSQLAlchemyモデル定義
- **スキーマ**: `app/schemas/`にPydanticスキーマ定義
- **CRUD操作**: `app/crud/`にデータベース操作関数定義
- **設定変更**: 環境変数を変更した場合は、Dockerコンテナを再起動してください
