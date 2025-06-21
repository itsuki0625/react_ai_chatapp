# 🚀 全体インフラコスト削減計画
## 本番環境 + STG環境 統合最適化

### 📊 現在のコスト構造 (合計 $497/月)
| 項目 | 月額 | 内訳 |
|------|------|------|
| **VPC** | **$214.97** | VPC Endpoints (PROD:$90 + STG:$90) + その他 |
| **EC2-Other** | **$87.85** | NAT Gateway (PROD:$45 + STG:$45) |
| **ECS** | **$67.76** | Fargate (PROD:$35 + STG:$35) |
| **ALB** | **$54.05** | ALB x4台 (PROD:2台 + STG:2台) |
| **Others** | **$27.34** | RDS、S3、その他 |
| **Tax** | **$45.20** | 消費税 |

---

## 🎯 段階的コスト削減戦略

### 【Phase 1】STG環境の最適化 (即座に実行可能)
**削減目標: -$126/月 (25%削減)**

#### 1.1 STG VPC Endpointsの削除 (-$90/月)
```bash
cd infrastructure/terraform/stg
terraform destroy -target=aws_vpc_endpoint.secretsmanager
terraform destroy -target=aws_vpc_endpoint.ecr_api
terraform destroy -target=aws_vpc_endpoint.ecr_dkr
terraform destroy -target=aws_vpc_endpoint.logs
```

#### 1.2 STG NAT Gatewayの削除 (-$22.5/月)
```bash
# パブリックサブネットでECS実行に変更
terraform apply -target=module.vpc
```

#### 1.3 STG ALB統合 (-$13.5/月)
```bash
# 2台のALBを1台に統合
terraform apply -target=aws_lb.main
```

**Phase 1合計削減: $126/月**

---

### 【Phase 2】本番環境の選択的最適化 (慎重に実行)
**削減目標: -$67.5/月 (13%削減)**

#### 2.1 本番ALB統合の検討 (-$27/月)
- **リスク**: 障害時の影響範囲拡大
- **対策**: Blue-Green デプロイメント導入
- **推奨**: Route53 ヘルスチェック追加

#### 2.2 本番VPC Endpointsの部分削減 (-$40.5/月)
削除対象の優先順位:
1. **CloudWatch Logs Endpoint** (-$22.5/月) ← 低リスク
2. **ECR DKR Endpoint** (-$22.5/月) ← 中リスク
3. **Secrets Manager** (保持) ← 高リスク
4. **ECR API** (保持) ← 高リスク

**Phase 2合計削減: $67.5/月**

---

### 【Phase 3】長期的な構造最適化 (3-6ヶ月計画)
**削減目標: -$100/月 (20%削減)**

#### 3.1 ECS to EKS on Fargate Spot
- Fargate Spot利用で最大70%削減
- 予想削減: $45/月

#### 3.2 Multi-AZ NAT Gateway最適化
- 単一NAT Gateway + VPC Endpoint組み合わせ
- 予想削減: $22.5/月

#### 3.3 RDS Aurora Serverless v2検討
- 使用量ベース課金
- 予想削減: $15-30/月

---

## 🎯 **推奨実装順序**

### 💡 **即座に実行 (今週)** 
**STG環境の完全最適化**
```bash
# 1. STG環境のコスト最適化適用
cd infrastructure/terraform/stg
cp cost-optimized-main.tf main.tf
terraform plan
terraform apply
```
**予想削減: $126/月**

### 🔄 **段階的実行 (来月)**
**本番環境の慎重な最適化**
```bash
# 1. 本番CloudWatch Logs Endpointの削除
cd infrastructure/terraform/prod
terraform destroy -target=aws_vpc_endpoint.logs

# 2. 本番ALB統合の準備
# - 監視体制強化
# - ロールバック手順確認
# - Blue-Green デプロイメント導入
```
**予想削減: $40-67/月**

---

## 💰 **コスト削減効果まとめ**

| Phase | 削減額/月 | 累積削減額 | 削減率 |
|-------|----------|-----------|--------|
| **Phase 1 (STG)** | $126 | $126 | 25% |
| **Phase 2 (PROD)** | $67.5 | $193.5 | 39% |
| **Phase 3 (長期)** | $100 | $293.5 | 59% |

### 🎯 **最終目標**
- **現在**: $497/月
- **最適化後**: $203/月
- **削減額**: **$294/月 (59%削減)**

---

## ⚠️ **リスク管理**

### 高リスク変更 (慎重に実行)
- ✅ 本番VPC Endpoints削除
- ✅ 本番ALB統合
- ✅ ECS→EKS移行

### 低リスク変更 (積極的に実行)
- ✅ STG環境全体最適化
- ✅ CloudWatch Logs Endpoint削除
- ✅ NAT Gateway最適化

---

## 🔍 **モニタリング指標**

### コスト監視
- AWS Cost Explorer での日次確認
- 予算アラート設定: $400/月
- 異常検知: 前月比+20%で通知

### 性能監視
- ALB Response Time < 200ms
- ECS Task CPU < 70%
- RDS Connection < 80%

---

## 🆘 **緊急時対応**

### 即座にロールバック可能な設定
```bash
# 全設定をバックアップから復元
terraform state push terraform.tfstate.backup
terraform apply
```

### 段階的復旧手順
1. ALB設定復元 (1-2分)
2. NAT Gateway復元 (3-5分)
3. VPC Endpoints復元 (5-10分) 