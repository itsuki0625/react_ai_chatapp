#!/usr/bin/env bash
set -euxo pipefail

# =================================================
# AWS Free Tier 向けインフラ構築スクリプト
# 実行前に AWS CLI が設定済みであることを確認してください。
# =================================================

# 環境変数
AWS_REGION=ap-northeast-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
VPC_CIDR=10.0.0.0/16

# サブネットCIDR
PUB_SUBNET1=10.0.1.0/24
PUB_SUBNET2=10.0.2.0/24
PRI_SUBNET1=10.0.101.0/24
PRI_SUBNET2=10.0.102.0/24

# RDS パラメータ
DB_IDENTIFIER=smartao-stg-db
DB_USER=user
DB_PASS=password
DB_NAME=demo
DB_CLASS=db.t3.micro
DB_STORAGE=20

# SES ドメイン (検証に使う)
SES_DOMAIN=example.com

# =================================================
# 1. VPC 作成
# =================================================
VPC_ID=$(aws ec2 create-vpc --cidr-block $VPC_CIDR --region $AWS_REGION \
  --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $AWS_REGION
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=smartao-stg-vpc --region $AWS_REGION

echo "VPC_ID=${VPC_ID}"

# =================================================
# 2. Internet Gateway とルートテーブル
# =================================================
IGW_ID=$(aws ec2 create-internet-gateway --region $AWS_REGION --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID --region $AWS_REGION
RTB_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --region $AWS_REGION --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $RTB_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $AWS_REGION

echo "IGW_ID=${IGW_ID}, RTB_ID=${RTB_ID}"

# =================================================
# 3. サブネット作成
# =================================================
SUBNET_PUB1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block $PUB_SUBNET1 \
  --availability-zone ${AWS_REGION}a --region $AWS_REGION \
  --query 'Subnet.SubnetId' --output text)
SUBNET_PUB2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block $PUB_SUBNET2 \
  --availability-zone ${AWS_REGION}c --region $AWS_REGION \
  --query 'Subnet.SubnetId' --output text)

# ルートテーブル関連付け (Public)
aws ec2 associate-route-table --subnet-id $SUBNET_PUB1 --route-table-id $RTB_ID --region $AWS_REGION
aws ec2 associate-route-table --subnet-id $SUBNET_PUB2 --route-table-id $RTB_ID --region $AWS_REGION

echo "Public Subnets: $SUBNET_PUB1, $SUBNET_PUB2"

# Private Subnet
SUBNET_PRI1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block $PRI_SUBNET1 \
  --availability-zone ${AWS_REGION}a --region $AWS_REGION \
  --query 'Subnet.SubnetId' --output text)
SUBNET_PRI2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block $PRI_SUBNET2 \
  --availability-zone ${AWS_REGION}c --region $AWS_REGION \
  --query 'Subnet.SubnetId' --output text)

echo "Private Subnets: $SUBNET_PRI1, $SUBNET_PRI2"

# =================================================
# 4. セキュリティグループ作成
# =================================================
# アプリ用 SG
SG_APP=$(aws ec2 create-security-group --group-name smartao-stg-app-sg \
  --description "App SG" --vpc-id $VPC_ID --region $AWS_REGION \
  --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_APP \
  --protocol tcp --port 3000 --cidr 0.0.0.0/0 --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $SG_APP \
  --protocol tcp --port 5050 --cidr 0.0.0.0/0 --region $AWS_REGION

echo "SG_APP=${SG_APP}"

# RDS 用 SG
SG_RDS=$(aws ec2 create-security-group --group-name smartao-stg-rds-sg \
  --description "RDS SG" --vpc-id $VPC_ID --region $AWS_REGION \
  --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_RDS \
  --protocol tcp --port 5432 --source-group $SG_APP --region $AWS_REGION

echo "SG_RDS=${SG_RDS}"

# =================================================
# Application Load Balancer の作成 (フロントエンド)
# =================================================
ALB_FRONT_ARN=$(aws elbv2 create-load-balancer \
  --name smartao-front-stg-alb \
  --subnets $SUBNET_PUB1 $SUBNET_PUB2 \
  --security-groups $SG_APP \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --region $AWS_REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)
echo "Front ALB ARN=${ALB_FRONT_ARN}"

# フロントエンド用ターゲットグループ作成
TG_FRONT_ARN=$(aws elbv2 create-target-group \
  --name smartao-front-stg-tg \
  --protocol HTTP \
  --port 3000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --region $AWS_REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)
echo "Front TG ARN=${TG_FRONT_ARN}"

# フロントエンド用リスナー作成 (ポート80)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_FRONT_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_FRONT_ARN \
  --region $AWS_REGION

# =================================================
# Application Load Balancer の作成 (バックエンド)
# =================================================
ALB_BACK_ARN=$(aws elbv2 create-load-balancer \
  --name smartao-api-stg-alb \
  --subnets $SUBNET_PUB1 $SUBNET_PUB2 \
  --security-groups $SG_APP \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --region $AWS_REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)
echo "Back ALB ARN=${ALB_BACK_ARN}"

# バックエンド用ターゲットグループ作成
TG_BACK_ARN=$(aws elbv2 create-target-group \
  --name smartao-api-stg-tg \
  --protocol HTTP \
  --port 5050 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --region $AWS_REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)
echo "Back TG ARN=${TG_BACK_ARN}"

# バックエンド用リスナー作成 (ポート80)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_BACK_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_BACK_ARN \
  --region $AWS_REGION

echo "ALBs and target groups created"

# =================================================
# 5. ECR リポジトリ作成
# =================================================
aws ecr create-repository --repository-name backend --region $AWS_REGION
aws ecr create-repository --repository-name frontend --region $AWS_REGION

echo "ECR repositories created"

# =================================================
# 6. ECS クラスター作成
# =================================================
aws ecs create-cluster --cluster-name smartao-api-stg --region $AWS_REGION
aws ecs create-cluster --cluster-name smartao-front-stg --region $AWS_REGION

echo "ECS clusters created"

# =================================================
# 7. RDS インスタンス作成
# =================================================
aws rds create-db-subnet-group \
  --db-subnet-group-name smartao-stg-db-subnet-group \
  --db-subnet-group-description "Subnet group for STG" \
  --subnet-ids $SUBNET_PRI1 $SUBNET_PRI2 --region $AWS_REGION

aws rds create-db-instance \
  --db-instance-identifier $DB_IDENTIFIER \
  --db-instance-class $DB_CLASS \
  --engine postgres \
  --allocated-storage $DB_STORAGE \
  --master-username $DB_USER \
  --master-user-password $DB_PASS \
  --db-name $DB_NAME \
  --db-subnet-group-name smartao-stg-db-subnet-group \
  --vpc-security-group-ids $SG_RDS \
  --no-publicly-accessible \
  --region $AWS_REGION

echo "RDS instance creation initiated"

# =================================================
# 8. SES ドメイン検証
# =================================================
aws ses verify-domain-identity --domain $SES_DOMAIN --region $AWS_REGION

echo "SES domain verification requested: $SES_DOMAIN"

# =================================================
# 9. Parameter Store (例)
# =================================================
aws ssm put-parameter --name /smartao/stg/api-base-url --value https://stg-api.smartao.jp --type String --overwrite --region $AWS_REGION

echo "Parameter Store entry created"

# =================================================
# 10. Secrets Manager (例)
# =================================================
aws secretsmanager create-secret --name stg/backend/env --secret-string file://backend/.env.stg --region $AWS_REGION

echo "Secrets Manager secret created"

# =================================================
# 11. IAM Role for ECS Task Execution
# =================================================
aws iam create-role --role-name ecsTaskExecutionRole-stg \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' --region $AWS_REGION
aws iam attach-role-policy --role-name ecsTaskExecutionRole-stg --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy --region $AWS_REGION
aws iam attach-role-policy --role-name ecsTaskExecutionRole-stg --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerRegistryPowerUser --region $AWS_REGION

echo "IAM role ecsTaskExecutionRole-stg created"

# =================================================
# End of script
# ================================================= 