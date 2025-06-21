# STG環境コスト削減 移行ガイド

## 🎯 目標
月額 $389 → $137 の **65%コスト削減** を実現

## 📊 コスト削減内訳
- VPC Endpoints削除: **-$180/月**
- NAT Gateway削除: **-$45/月**  
- ALB統合 (2台→1台): **-$27/月**
- **合計削減額: $252/月**

## 🚀 実装手順

### Phase 1: バックアップ作成
```bash
# 現在の設定をバックアップ
cp main.tf main.tf.backup
cp services.tf services.tf.backup

# 現在のTerraform stateをバックアップ
terraform state pull > terraform.tfstate.backup
```

### Phase 2: 段階的移行

#### Step 1: VPC Endpointsの削除
```bash
# VPC Endpointsを削除 (約$180/月削減)
terraform destroy -target=aws_vpc_endpoint.secretsmanager
terraform destroy -target=aws_vpc_endpoint.ecr_api  
terraform destroy -target=aws_vpc_endpoint.ecr_dkr
terraform destroy -target=aws_vpc_endpoint.logs
terraform destroy -target=aws_security_group.vpc_endpoint
```

#### Step 2: ALBの統合
```bash
# 新しい統合ALB設定を適用
cp cost-optimized-main.tf main.tf

# バックエンドALBを削除
terraform destroy -target=aws_lb.backend
terraform destroy -target=aws_lb_listener.backend_http

# 新しい統合ALB設定を適用
terraform apply -target=aws_lb.main
terraform apply -target=aws_lb_listener.main_http
terraform apply -target=aws_lb_listener_rule.backend
```

#### Step 3: NAT Gatewayの削除
```bash
# NAT Gatewayを削除し、パブリックサブネット使用に変更
terraform apply -target=module.vpc
```

#### Step 4: ECSサービスの更新
```bash
# ECSサービスを新しいALB設定で更新
terraform apply -target=aws_ecs_service.backend
terraform apply -target=aws_ecs_service.frontend
```

### Phase 3: 設定確認
```bash
# 全体の設定を確認・適用
terraform plan
terraform apply

# アプリケーションの動作確認
curl http://<ALB-DNS-NAME>        # Frontend確認
curl http://<ALB-DNS-NAME>/api/   # Backend確認
```

## 🔧 設定変更のポイント

### 1. ALB統合設定
- Frontend: デフォルトルーティング (port 80)
- Backend: パスベースルーティング (`/api/*`)

### 2. VPC設定変更
```hcl
# 変更前
enable_nat_gateway = true
single_nat_gateway = true

# 変更後  
enable_nat_gateway = false
single_nat_gateway = false
```

### 3. セキュリティ考慮事項
- パブリックサブネットでECS実行
- インターネット経由でAWSサービスにアクセス
- セキュリティグループで適切にアクセス制御

## ⚠️ 注意事項

### データベース接続
- RDS接続文字列の確認が必要
- パブリックサブネット配置に伴う設定変更

### アプリケーション設定
- Backend APIのベースURL確認
- フロントエンドのAPI呼び出しパス確認 (`/api/*`)

### ダウンタイム
- ALB切り替え時に数分のダウンタイムが発生する可能性
- 事前にメンテナンス時間を通知推奨

## 🎉 追加の極限コスト削減案

さらにコストを下げたい場合は `ultra-minimal-config.tf` を参照:
- **月額 $6-8** まで削減可能
- EC2 t3.nano + SQLite構成
- 機能制限あり (開発・テスト用途限定)

## 🔍 モニタリング

移行後は以下を監視:
1. **AWS Cost Explorer** でコスト削減効果を確認
2. **CloudWatch** でアプリケーション性能を監視  
3. **ALB アクセスログ** でルーティングを確認

## 🆘 ロールバック手順

問題が発生した場合:
```bash
# バックアップから復元
cp main.tf.backup main.tf
cp services.tf.backup services.tf

# Terraform stateを復元
terraform state push terraform.tfstate.backup

# 元の構成を再適用
terraform apply
```

## 📞 サポート

移行中に問題が発生した場合は、バックアップファイルを使用してすぐにロールバックできます。 