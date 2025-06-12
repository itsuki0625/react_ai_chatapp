# Stripe Webhook 設定手順

## 必要なWebhookイベント

サブスクリプション機能を正常に動作させるため、Stripeダッシュボードで以下のWebhookイベントを設定してください。

### 設定場所
1. Stripeダッシュボード → Developers → Webhooks
2. 既存のWebhookエンドポイントを編集、または新規作成

### エンドポイントURL
```
https://your-domain.com/api/v1/subscriptions/webhook
```

### 必要なイベントタイプ

#### ✅ 必須イベント
- `checkout.session.completed` - チェックアウト完了
- `customer.subscription.created` - サブスクリプション作成
- `customer.subscription.updated` - サブスクリプション更新
- `customer.subscription.deleted` - サブスクリプション削除
- `invoice.payment_succeeded` - 支払い成功
- `invoice.payment_failed` - 支払い失敗
- `customer.created` - 顧客作成
- `customer.updated` - 顧客更新

#### 🔍 現在受信されているイベント
- `customer.*` (顧客関連)
- `checkout.session.*` (チェックアウト関連)

#### ❌ 不足しているイベント
- `customer.subscription.*` (サブスクリプション関連)
- `invoice.*` (請求・支払い関連)

## 設定手順

1. **Stripeダッシュボードにログイン**
2. **Developers → Webhooks**に移動
3. **既存のエンドポイントを編集**または**新規作成**
4. **Listen to** セクションで **"Select events"** をクリック
5. 以下のイベントを追加:
   ```
   checkout.session.completed
   customer.subscription.created
   customer.subscription.updated
   customer.subscription.deleted
   invoice.payment_succeeded
   invoice.payment_failed
   customer.created
   customer.updated
   ```
6. **Save changes**をクリック

## トラブルシューティング

### 支払いが反映されない場合
1. Webhookイベントが正しく設定されているか確認
2. バックエンドログで受信イベントを確認:
   ```bash
   docker-compose logs backend | Select-String "Webhook"
   ```
3. Stripeダッシュボードで**Webhook delivery attempts**を確認

### よくある問題
- **`customer.subscription.*` イベントが設定されていない**
  → サブスクリプション作成/更新が処理されない
- **`invoice.payment_succeeded` イベントが設定されていない**
  → 支払い完了が処理されない
- **エンドポイントURLが間違っている**
  → Webhookが届かない

## 設定確認
設定後、テスト支払いを行い、以下のログが出力されることを確認してください:

```
INFO [app.api.v1.endpoints.subscription] Webhook受信: Type=customer.subscription.created
INFO [app.api.v1.endpoints.subscription] Webhook受信: Type=invoice.payment_succeeded
INFO [app.api.v1.endpoints.subscription] Webhook受信: Type=checkout.session.completed
``` 