# Stripe 3Dセキュア対応 セットアップガイド

## 環境変数設定

`.env.local` ファイルを作成して以下を設定してください：

```bash
# Stripe Configuration (必須)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here

# API Configuration  
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here-change-this-in-production
```

## Stripeテストキー取得方法

1. [Stripe Dashboard](https://dashboard.stripe.com/) にログイン
2. 左サイドバーの「Developers」→「API keys」をクリック
3. 「Publishable key」をコピーして `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` に設定

## 3Dセキュアテスト用カード番号

```
4000 0025 0000 3155  # 3Dセキュア認証が必要
4000 0000 0000 9995  # 常に失敗するカード  
4242 4242 4242 4242  # 正常処理用カード
4000 0000 0000 0002  # カード拒否テスト
```

## 機能テスト手順

1. **プラン選択画面**でプランを選択
2. **「カード決済 (推奨)」**タブを選択
3. テストカード情報を入力
4. 3Dセキュア認証画面が表示されることを確認
5. 認証完了後の決済成功を確認

## トラブルシューティング

### エラー: "Stripe is not loaded"
- ネットワーク接続を確認
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` が正しく設定されているか確認

### 3Dセキュア認証が動作しない
- テスト用カード番号 `4000 0025 0000 3155` を使用
- ブラウザの開発者ツールでエラーログを確認

## 📧 メール通知機能のセットアップ

### **バックエンド環境変数の設定**

`backend/.env`ファイルに以下のメール設定を追加してください：

```bash
# SMTP設定（Gmail使用の場合）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@your-domain.com
ADMIN_EMAIL=admin@your-domain.com
```

### **Gmailアプリパスワード設定手順**

1. Googleアカウントで2段階認証を有効にする
2. [Googleアカウント管理画面](https://myaccount.google.com/) → セキュリティ
3. 「アプリパスワード」を生成
4. 生成されたパスワードを`SMTP_PASSWORD`に設定

### **メール通知の種類**

- ✅ **決済成功通知** - PaymentIntent succeeded時に自動送信
- ⚠️ **決済失敗通知** - PaymentIntent failed時に自動送信  
- 🔐 **3Dセキュア認証リマインダー** - PaymentIntent requires_action時に自動送信
- 🚨 **管理者向けアラート** - 高失敗率検知時に自動送信

### **新機能: Phase 3 追加項目**

- 📊 **決済履歴ページ** - `/subscription/history` でアクセス
  - フィルタリング・検索機能
  - CSVエクスポート機能
  - ステータス別表示

- 📈 **管理者決済監視** - `/admin/payments` でアクセス  
  - リアルタイム決済統計
  - 3Dセキュア失敗監視
  - アラート機能 