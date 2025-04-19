# バックエンドサービス

## 概要
学習支援アプリケーションのバックエンドサービスです。ユーザー認証、チャット機能、大学情報管理、志望校管理、サブスクリプション決済などの機能を提供します。

## 技術スタック
- FastAPI: Webフレームワーク
- PostgreSQL: データベース
- SQLAlchemy: ORMツール
- Alembic: マイグレーションツール
- Stripe: 決済処理

## セットアップ方法

### 環境変数の設定
`.env.example`ファイルをコピーして`.env`ファイルを作成し、必要な環境変数を設定します。

```bash
cp .env.example .env
```

編集が必要な主な環境変数:
- `DATABASE_URL`: PostgreSQLデータベースの接続URL
- `SECRET_KEY`: セッションの暗号化に使用される秘密鍵
- `OPENAI_API_KEY`: OpenAI APIのアクセスキー
- `STRIPE_API_KEY`: Stripe APIのシークレットキー
- `STRIPE_WEBHOOK_SECRET`: Stripeウェブフックの検証シークレット
- `STRIPE_PRICE_ID`: デフォルトの価格ID（オプション）

### Dockerを使用した起動

```bash
docker-compose up -d
```

### マイグレーションの実行

```bash
docker-compose exec backend alembic upgrade head
```

## Stripe決済機能

### 利用準備
1. [Stripeダッシュボード](https://dashboard.stripe.com/)でアカウントを作成
2. APIキーを取得し、`.env`ファイルに設定
3. 商品とプランを作成し、価格IDを取得
4. ウェブフックエンドポイントを設定し、シークレットを取得

### サブスクリプションプランの設定
データベースにサブスクリプションプランを追加します。

```python
# 例: スクリプトまたは管理者APIを使用
from app.schemas.subscription import SubscriptionPlanCreate
from app.crud.subscription import create_subscription_plan
from sqlalchemy.orm import Session

def create_plans(db: Session):
    basic_plan = SubscriptionPlanCreate(
        name="ベーシックプラン",
        description="基本機能が利用可能なプラン",
        price_id="price_xxxxxxxxxxxxx",  # Stripeダッシュボードから取得した価格ID
        amount=980,
        currency="jpy",
        interval="month",
        is_active=True
    )
    create_subscription_plan(db, basic_plan)
    
    premium_plan = SubscriptionPlanCreate(
        name="プレミアムプラン",
        description="全機能が利用可能なプラン",
        price_id="price_yyyyyyyyyyyyy",  # Stripeダッシュボードから取得した価格ID
        amount=1980,
        currency="jpy",
        interval="month",
        is_active=True
    )
    create_subscription_plan(db, premium_plan)
```

### キャンペーンコードの設定
割引キャンペーンコードを作成します。キャンペーンコードには所有者（アフィリエイトパートナーなど）を設定することもできます。

```python
# 例: キャンペーンコードの作成
from app.schemas.subscription import CampaignCodeCreate
from app.crud.subscription import create_campaign_code
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def create_campaign_codes(db: Session):
    # パーセント割引のキャンペーンコード
    percent_code = CampaignCodeCreate(
        code="WELCOME20",
        description="新規登録20%割引キャンペーン",
        discount_type="percentage",
        discount_value=20.0,  # 20%割引
        max_uses=100,  # 最大100回まで使用可能
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=30),  # 30日間有効
        is_active=True
    )
    create_campaign_code(db, percent_code)
    
    # 固定額割引のキャンペーンコード（アフィリエイト用）
    fixed_code = CampaignCodeCreate(
        code="AFFILIATE500",
        description="アフィリエイト紹介キャンペーン",
        owner_id="af12e3c4-5678-9abc-def0-123456789abc",  # アフィリエイトパートナーのID
        discount_type="fixed",
        discount_value=500.0,  # 500円割引
        is_active=True
    )
    create_campaign_code(db, fixed_code)
```

### ウェブフックの設定
1. Stripeダッシュボードでウェブフックエンドポイントを登録: `https://あなたのドメイン/api/v1/subscriptions/webhook`
2. 以下のイベントを監視するよう設定:
   - `checkout.session.completed`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

### API機能一覧
- `GET /api/v1/subscriptions/plans`: 利用可能なサブスクリプションプラン一覧の取得
- `GET /api/v1/subscriptions/user-subscription`: ユーザーのアクティブなサブスクリプション情報の取得
- `GET /api/v1/subscriptions/payment-history`: 支払い履歴の取得
- `POST /api/v1/subscriptions/create-checkout`: チェックアウトセッションの作成
- `POST /api/v1/subscriptions/create-portal-session`: カスタマーポータルセッションの作成
- `POST /api/v1/subscriptions/manage-subscription`: サブスクリプションの管理（キャンセル、再開、プラン変更）
- `POST /api/v1/subscriptions/webhook`: Stripeからのウェブフックを処理

### キャンペーンコード機能
- `POST /api/v1/subscriptions/verify-campaign-code`: キャンペーンコードの検証
- `GET /api/v1/subscriptions/campaign-codes`: キャンペーンコードの一覧取得
- `POST /api/v1/subscriptions/campaign-codes`: 新しいキャンペーンコードの作成
- `GET /api/v1/subscriptions/campaign-codes/{id}`: 特定のキャンペーンコードの詳細取得
- `PUT /api/v1/subscriptions/campaign-codes/{id}`: キャンペーンコードの更新
- `DELETE /api/v1/subscriptions/campaign-codes/{id}`: キャンペーンコードの削除

キャンペーンコードは以下の特徴を持ちます：
- 割引タイプ: パーセント割引(percentage)または固定金額割引(fixed)
- 所有者: 特定のユーザーに紐付け可能（アフィリエイトトラッキングなど）
- 有効期限: 開始日と終了日を設定可能
- 使用回数制限: 最大使用回数を設定可能
- 有効/無効フラグ: コードを一時的に無効化可能

## 開発ガイドライン
- APIエンドポイントの追加: `app/api/v1/endpoints/`に新しいルーターを作成
- モデルの追加: `app/models/`にSQLAlchemyモデルを定義
- スキーマの追加: `app/schemas/`にPydanticスキーマを定義
- CRUDオペレーションの追加: `app/crud/`にデータベース操作関数を定義
