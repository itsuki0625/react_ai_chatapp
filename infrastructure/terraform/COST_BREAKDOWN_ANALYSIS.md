# 💰 インフラコスト詳細分析
## 本番環境 vs STG環境

### 📊 現在の全体コスト構造
**総額: $497/月** (本番 + STG + 税込み)

---

## 🏭 **本番環境の予測コスト**

### 基本リソース
| リソース | 仕様 | 月額コスト |
|---------|------|----------|
| **VPC Endpoints** | Interface Endpoints × 4 | **$90.00** |
| **NAT Gateway** | 1個 (ap-northeast-1a) | **$22.50** |
| **ALB** | Application Load Balancer × 2 | **$27.00** |
| **ECS Fargate** | 256 CPU + 512MB Memory × 2サービス | **$35.00** |
| **RDS PostgreSQL** | db.t3.micro (20GB) | **$15.00** |
| **ECR** | イメージストレージ | **$2.00** |
| **CloudWatch Logs** | ECS + ALB ログ | **$5.00** |
| **S3** | アイコン画像等 | **$3.00** |
| **Route53** | DNS管理 | **$1.00** |
| **その他** | IAM, Secrets Manager等 | **$4.50** |

### **本番環境小計: $205/月**

---

## 🧪 **STG環境の現在コスト**

### 基本リソース
| リソース | 仕様 | 月額コスト |
|---------|------|----------|
| **VPC Endpoints** | Interface Endpoints × 4 | **$90.00** |
| **NAT Gateway** | 1個 (ap-northeast-1a) | **$22.50** |
| **ALB** | Application Load Balancer × 2 | **$27.00** |
| **ECS Fargate** | 256 CPU + 512MB Memory × 2サービス | **$35.00** |
| **RDS PostgreSQL** | db.t3.micro (20GB) | **$15.00** |
| **ECR** | イメージストレージ | **$2.00** |
| **CloudWatch Logs** | ECS + ALB ログ | **$5.00** |
| **S3** | アイコン画像等 | **$3.00** |
| **その他** | IAM, Secrets Manager等 | **$4.50** |

### **STG環境小計: $204/月**

---

## 🔍 **コスト配分詳細**

### 現在の料金配分
```
総コスト: $497/月
├── 本番環境: $205/月 (41%)
├── STG環境: $204/月 (41%) 
├── 消費税: $45/月 (9%)
├── その他/変動費: $43/月 (9%)
    └── データ転送料、追加ストレージ等
```

### 最大のコスト要因 (両環境共通)
1. **VPC Endpoints: $180/月** (36%)
2. **NAT Gateway: $45/月** (9%)
3. **ALB: $54/月** (11%)
4. **ECS Fargate: $70/月** (14%)

---

## 🎯 **本番環境の削減ポテンシャル**

### 🔒 **保守的削減案** (推奨)
| 項目 | 削減額/月 | リスク |
|------|----------|-------|
| CloudWatch Logs Endpoint削除 | **-$22.5** | 低 |
| ECR DKR Endpoint削除 | **-$22.5** | 中 |
| **保守的削減合計** | **-$45/月** | **安全** |

### ⚡ **積極的削減案** (要検討)
| 項目 | 削減額/月 | リスク |
|------|----------|-------|
| 上記 + ALB統合 | **-$27** | 中 |
| 上記 + Secrets Manager Endpoint削除 | **-$22.5** | 高 |
| **積極的削減合計** | **-$94.5/月** | **要注意** |

---

## 💡 **推奨削減戦略**

### Phase 1: STG環境完全最適化 ✅
- **削減額**: $126/月
- **リスク**: 極低
- **実行**: 即座に可能

### Phase 2: 本番環境保守的最適化
- **削減額**: $45/月  
- **リスク**: 低
- **実行**: STG削減後1-2週間

### Phase 3: 本番環境積極的最適化
- **削減額**: $94.5/月
- **リスク**: 中-高
- **実行**: 慎重に検討

---

## 🎯 **最終削減目標**

| シナリオ | 現在 | 削減後 | 削減額 | 削減率 |
|---------|------|--------|-------|--------|
| **保守的** | $497 | $326 | **$171** | **34%** |
| **積極的** | $497 | $276 | **$221** | **44%** |
| **最大** | $497 | $203 | **$294** | **59%** |

---

## 📈 **月別削減スケジュール**

### 今月: STG環境最適化
- 削減額: **$126/月**
- 新月額: **$371**

### 来月: 本番環境保守的最適化  
- 追加削減: **$45/月**
- 新月額: **$326**

### 3ヶ月後: 本番環境積極的最適化
- 追加削減: **$49.5/月**
- 新月額: **$276**

---

## ⚠️ **リスク分析**

### 本番環境変更時の注意点
1. **ダウンタイム**: ALB統合時に数分の停止
2. **パフォーマンス**: VPC Endpoint削除でレイテンシ微増
3. **セキュリティ**: インターネット経由通信の増加
4. **可用性**: 単一ALBによる単一障害点

### 推奨対策
- Blue-Green デプロイメント導入
- 詳細監視体制の構築
- 段階的実行による影響範囲限定 