# STG環境管理ガイド

## 🎯 概要

STG環境は**オンデマンド起動**でコスト最適化されています。
- **停止時**: 月額$5（RDS、VPC等の基本料金のみ）
- **起動時**: 月額$135（ECS Fargate起動時）
- **想定使用**: 開発・テスト時のみ起動、使用後すぐ停止

## 🚀 STG環境起動方法

### 1. GitHub Actions経由（推奨）

#### メイン起動ワークフロー
- **ワークフロー**: `STG Environment Wake Up`
- **機能**: 
  - 起動時間選択（1-24時間）
  - 使用目的記録
  - パブリックIP自動取得
  - CloudFlare設定ガイド表示

#### 使用手順
1. GitHubリポジトリ → Actions
2. `STG Environment Wake Up` を選択
3. `Run workflow` をクリック
4. 起動時間を選択（デフォルト4時間）
5. 使用目的を入力
6. `Run workflow` で実行

#### 起動完了後
- ワークフローログでパブリックIPを確認
- CloudFlareでstg.smartao.jpのAレコードを新しいIPに更新
- フロントエンド: `http://[IP]:3000`
- バックエンド: `http://[IP]:5050`

### 2. Webhook経由（高速起動）

#### 簡単起動ワークフロー
- **ワークフロー**: `STG Webhook Wake`
- **機能**: 最小限の起動処理のみ
- **用途**: 外部システムからの自動起動

#### Personal Access Token設定
```bash
# GitHubでPersonal Access Tokenを作成
# Scopes: repo, workflow

curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/react_ai_chatapp/dispatches \
  -d '{"event_type":"wake-stg"}'
```

## 🛑 STG環境停止方法

### 1. 手動停止

#### 停止ワークフロー
- **ワークフロー**: `STG Environment Sleep`
- **機能**: 安全確認付き停止

#### 使用手順
1. GitHubリポジトリ → Actions
2. `STG Environment Sleep` を選択
3. `Run workflow` をクリック
4. 停止確認で `true` を選択
5. `Run workflow` で実行

### 2. 自動停止

#### 自動停止ワークフロー
- **ワークフロー**: `STG Auto Sleep`
- **機能**: 指定時間後の自動停止

#### 使用手順
1. STG環境起動後に実行
2. 停止までの時間を選択（1-24時間）
3. GitHub Actionsが指定時間後に自動停止

## 💰 コスト管理

### 月額料金
- **停止時**: $5/月
  - RDS t3.micro: $15/月 → 無料枠適用で$0
  - VPC基本料金: $5/月
- **起動時**: $135/月（フル稼働時）
  - ECS Fargate: $130/月
  - その他: $5/月

### コスト削減のベストプラクティス
1. **使用後は必ず停止**
2. **長時間使用時は自動停止タイマー設定**
3. **不要な起動を避ける**
4. **起動時間を最小限に**

## 🔧 トラブルシューティング

### よくある問題

#### 1. 起動に失敗する
```bash
# 手動確認方法
aws ecs describe-services --cluster stg-front --services stg-front-service
aws ecs describe-services --cluster stg-api --services stg-api-service
```

#### 2. IPアドレスが取得できない
- 起動直後はIP割り当てに時間がかかる場合があります
- 2-3分待ってから再度確認してください

#### 3. CloudFlare設定
- stg.smartao.jpのAレコードを新しいIPに更新
- TTLは300秒（5分）に設定推奨
- プロキシ設定は無効（DNS only）

### 緊急停止
```bash
# AWS CLI経由での緊急停止
aws ecs update-service --cluster stg-front --service stg-front-service --desired-count 0
aws ecs update-service --cluster stg-api --service stg-api-service --desired-count 0
```

## 📊 監視・ログ

### サービス状態確認
```bash
# ECSサービス状態
aws ecs describe-services --cluster stg-front --services stg-front-service
aws ecs describe-services --cluster stg-api --services stg-api-service

# 実行中タスク確認
aws ecs list-tasks --cluster stg-front --service-name stg-front-service
aws ecs list-tasks --cluster stg-api --service-name stg-api-service
```

### ログ確認
- CloudWatch Logs
- グループ: `/ecs/stg-front`, `/ecs/stg-api`

## 🚨 注意事項

1. **STG環境は本番データを含みません**
2. **起動中は課金が発生します**
3. **使用後は必ず停止してください**
4. **パブリックIPは起動のたびに変わります**
5. **CloudFlare設定の更新が必要です**

## 📞 サポート

問題が発生した場合:
1. GitHub Actionsのログを確認
2. AWS CLIでサービス状態を確認
3. 緊急時は手動停止を実行 