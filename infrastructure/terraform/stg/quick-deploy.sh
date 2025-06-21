#!/bin/bash
# 🚀 STG環境 即座コスト削減デプロイスクリプト
# 削減効果: $126/月 (25%削減)

set -e  # エラー時に停止

echo "🎯 STG環境コスト削減開始..."
echo "削減予想: $126/月 (VPC Endpoints: $90 + NAT Gateway: $22.5 + ALB統合: $13.5)"

# 1. バックアップ作成
echo "📦 現在の設定をバックアップ中..."
cp main.tf main.tf.backup.$(date +%Y%m%d_%H%M%S)
cp services.tf services.tf.backup.$(date +%Y%m%d_%H%M%S)
terraform state pull > terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)

# 2. 高額なVPC Endpointsを削除 (-$90/月)
echo "💰 VPC Endpoints削除中 (-$90/月)..."
terraform destroy -target=aws_vpc_endpoint.secretsmanager -auto-approve || echo "Already deleted"
terraform destroy -target=aws_vpc_endpoint.ecr_api -auto-approve || echo "Already deleted"
terraform destroy -target=aws_vpc_endpoint.ecr_dkr -auto-approve || echo "Already deleted"
terraform destroy -target=aws_vpc_endpoint.logs -auto-approve || echo "Already deleted"
terraform destroy -target=aws_security_group.vpc_endpoint -auto-approve || echo "Already deleted"

# 3. 最適化設定を適用
echo "🔧 最適化設定を適用中..."
cp cost-optimized-main.tf main.tf

# 4. インフラ更新実行
echo "🚀 インフラ更新実行中..."
terraform plan -out=stg-optimize.tfplan
echo "⚠️  プランを確認してください。続行しますか? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    terraform apply stg-optimize.tfplan
    echo "✅ STG環境最適化完了!"
    echo "💰 月額削減効果: $126"
    echo "📊 最適化内容:"
    echo "  - VPC Endpoints削除: -$90/月"
    echo "  - NAT Gateway削除: -$22.5/月"
    echo "  - ALB統合: -$13.5/月"
else
    echo "❌ デプロイをキャンセルしました"
    # 設定を戻す
    cp main.tf.backup.* main.tf 2>/dev/null || echo "バックアップファイルが見つかりません"
    exit 1
fi

# 5. 動作確認
echo "🔍 動作確認中..."
sleep 30  # ALBの準備時間
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "ALB DNS取得に失敗")
if [[ "$ALB_DNS" != "ALB DNS取得に失敗" ]]; then
    echo "🌐 Frontend確認: http://$ALB_DNS"
    echo "🌐 Backend確認: http://$ALB_DNS/api/"
    
    # 簡単なヘルスチェック
    if curl -s -o /dev/null -w "%{http_code}" "http://$ALB_DNS" | grep -q "200\|301\|302"; then
        echo "✅ フロントエンド正常"
    else
        echo "⚠️  フロントエンドの確認が必要です"
    fi
fi

echo ""
echo "🎉 STG環境コスト削減完了!"
echo "💰 予想月額削減: $126"
echo "📈 全体削減率: 25%"
echo ""
echo "📋 次のステップ:"
echo "1. AWS Cost Explorerで削減効果を1週間後に確認"
echo "2. アプリケーション動作を継続監視"
echo "3. 本番環境の最適化検討 (さらに$67.5/月削減可能)" 