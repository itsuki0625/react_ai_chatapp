# 学校テナント機能 - セットアップガイド

## 🎯 概要

学校テナント機能が完全に実装されました。このガイドでは、機能の有効化と設定方法について説明します。

---

## 🚀 機能概要

### **実装済み機能**

#### **🏫 学校管理者機能**
- 学校ダッシュボード（統計情報、活動履歴）
- 学校内ユーザー管理（先生・生徒の管理）
- 先生・生徒の担当関係管理
- 学校設定管理
- 分析・レポート機能

#### **👨‍🏫 先生機能**
- 担当生徒一覧
- 生徒の学習進捗確認
- チャット履歴閲覧
- 志望理由書閲覧
- 志望校情報確認

#### **🔐 セキュリティ機能**
- ロールベースアクセス制御
- テナント境界の強制
- 権限チェック機能

---

## ⚙️ 環境設定

### **環境変数**

`.env.local` ファイルに以下の設定を追加：

```bash
# API設定
NEXT_PUBLIC_API_BASE_URL=http://localhost:5050/api/v1

# 学校テナント機能設定
NEXT_PUBLIC_USE_MOCK_DATA=true
NEXT_PUBLIC_ENABLE_SCHOOL_ADMIN=true
NEXT_PUBLIC_ENABLE_TEACHER_FEATURES=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true

# デバッグ設定（開発環境のみ）
NEXT_PUBLIC_DEBUG=true
```

### **本番環境設定**

```bash
# 本番環境用
NEXT_PUBLIC_API_BASE_URL=https://api.smartao.jp/api/v1
NEXT_PUBLIC_USE_MOCK_DATA=false
NEXT_PUBLIC_DEBUG=false
```

---

## 🔧 開発環境での使用

### **1. Mock データモード**

開発環境では、実APIの代わりにMockデータを使用できます：

```typescript
// 自動的にMockデータを使用（開発環境）
NEXT_PUBLIC_USE_MOCK_DATA=true
```

### **2. デバッグパネル**

開発環境では、右下にデバッグパネルが表示されます：
- APIモードの切り替え（Mock ⇔ 実API）
- 現在のユーザー情報表示
- 接続状態の確認
- 機能フラグの確認

### **3. 実APIとの切り替え**

デバッグパネルのスイッチで簡単に切り替え可能：
- **Mock モード**: テスト用の固定データ
- **実API モード**: バックエンドとの実際の通信

---

## 📋 使用方法

### **学校管理者として使用**

1. **ログイン**: 学校管理者ロールでログイン
2. **アクセス**: `/school-admin/dashboard` にアクセス
3. **機能利用**: 
   - ダッシュボードで学校の状況を確認
   - ユーザー管理で先生・生徒を管理
   - 担当関係の設定・変更
   - 学校設定の調整

### **先生として使用**

1. **ログイン**: 教員ロールでログイン
2. **アクセス**: `/teacher/students` にアクセス
3. **機能利用**:
   - 担当生徒の一覧表示
   - 生徒の学習進捗確認
   - チャット内容の確認
   - 志望理由書の確認

---

## 🗂️ ファイル構成

### **フロントエンド**

```
study-support-app/src/
├── contexts/
│   └── TenantContext.tsx          # メインコンテキスト
├── lib/
│   ├── api/tenant-client.ts       # 実API クライアント
│   ├── mock/tenant-api.ts         # Mock API
│   └── config/tenant.ts           # 設定管理
├── hooks/
│   └── useTenantApi.ts            # カスタムフック
├── components/
│   ├── shared/TenantGuard.tsx     # 権限ガード
│   ├── dev/TenantDebugPanel.tsx   # デバッグパネル
│   └── feature/
│       ├── school-admin/          # 学校管理者用
│       └── teacher/               # 先生用
└── types/
    └── tenant.ts                  # 型定義
```

### **バックエンド**

```
backend/app/
├── api/v1/endpoints/
│   ├── school_admin.py           # 学校管理者API
│   └── teacher.py                # 先生用API
├── models/
│   └── teacher_student.py        # テナント用モデル
├── schemas/
│   └── school_tenant.py          # スキーマ定義
├── crud/
│   └── school_tenant.py          # CRUD操作
└── core/
    └── permissions.py            # 権限管理
```

---

## 🧪 テスト

### **Mock データでのテスト**

```bash
# 開発サーバー起動
npm run dev

# Mock モードで機能確認
1. デバッグパネルでMockモードを確認
2. 学校管理者でログイン
3. /school-admin/dashboard にアクセス
4. 各機能の動作確認
```

### **実APIでのテスト**

```bash
# バックエンド起動
docker-compose up -d

# 権限マイグレーション実行
./backend/scripts/migrate_permissions_docker.sh migrate --environment dev

# フロントエンドで実APIモードに切り替え
1. デバッグパネルでAPIモードをONに
2. 機能の動作確認
```

---

## 🚨 トラブルシューティング

### **よくある問題**

#### **1. 権限エラー**
```
Error: この機能を利用する権限がありません
```
**解決方法**: 
- ユーザーに適切なロールが割り当てられているか確認
- 権限マイグレーションが実行されているか確認

#### **2. API接続エラー**
```
API接続エラー (Mock データを使用中)
```
**解決方法**:
- バックエンドが起動しているか確認
- API URLが正しく設定されているか確認
- デバッグパネルでMockモードに切り替え

#### **3. データが表示されない**
**解決方法**:
- デバッグパネルでデータを再取得
- ブラウザのキャッシュをクリア
- ログアウト→ログインでセッションリフレッシュ

### **ログ確認**

```bash
# フロントエンド
ブラウザの開発者ツール Console タブ

# バックエンド  
docker-compose logs backend
```

---

## 📈 本番環境デプロイ

### **1. 環境変数設定**

```bash
# 本番用環境変数
NEXT_PUBLIC_USE_MOCK_DATA=false
NEXT_PUBLIC_API_BASE_URL=https://api.smartao.jp/api/v1
```

### **2. 権限マイグレーション**

```bash
# STG環境
./backend/scripts/migrate_permissions_ecs.sh migrate --environment stg

# 本番環境
./backend/scripts/migrate_permissions_ecs.sh migrate --environment prod
```

### **3. 動作確認**

1. 学校管理者アカウントでログイン
2. 各機能の動作確認
3. 先生アカウントでの動作確認
4. セキュリティテスト

---

## 💡 今後の拡張

### **計画中の機能**
- 生徒の保護者機能
- 詳細分析レポート
- 通知機能の拡張
- 一括操作機能の追加

### **カスタマイズ**
- 学校別のブランディング
- カスタム権限の追加
- レポート形式のカスタマイズ

---

## 📞 サポート

質問や問題がある場合：
1. このドキュメントのトラブルシューティングを確認
2. デバッグパネルで状態を確認
3. 開発チームに連絡

**Happy Coding! 🎉**
