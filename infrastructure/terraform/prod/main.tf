terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws      = { source = "hashicorp/aws",      version = "~> 5.0" }
    external = { source = "hashicorp/external", version = "~> 2.1" }
    random   = { source = "hashicorp/random",   version = "~> 3.5" }
  }
}

provider "aws" {
  region = var.aws_region
}

# === 新しい VPC モジュール定義 ===
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0" # 必要に応じてバージョンを指定

  name = "${var.environment}-vpc"
  cidr = "10.1.0.0/16" # 本番環境用のCIDRブロック (stgと重複しないように)

  azs             = ["${var.aws_region}a", "${var.aws_region}c"] # 必要に応じてAZを変更
  private_subnets = ["10.1.1.0/24", "10.1.2.0/24"]
  public_subnets  = ["10.1.101.0/24", "10.1.102.0/24"]

  enable_nat_gateway = true # Privateサブネットからのアウトバウンド通信用
  single_nat_gateway = true # コスト削減のため (必要なら false に変更)

  # Disable default ACL and route table creation to satisfy module requirements
  manage_default_network_acl = false
  manage_default_route_table = false

  # VPC Flow Logs (オプション)
  # enable_flow_log                      = true
  # create_flow_log_cloudwatch_log_group = true
  # create_flow_log_cloudwatch_iam_role  = true

  # --- VPC Endpoints ---
  # Gateway Endpoints
  # create_gateway_endpoints = true # Removed
  # gateway_endpoints = { ... } # Removed

  # Interface Endpoints
  # create_interface_endpoints = true # Removed
  # interface_endpoints = { ... } # Removed

  tags = {
    Terraform   = "true"
    Environment = var.environment
  }
}
# === VPC モジュール定義ここまで ===

# セキュリティグループ: アプリケーション
resource "aws_security_group" "app" {
  name        = "${var.environment}-app-sg"
  description = "Allow HTTP/3000/5050"
  vpc_id      = module.vpc.vpc_id # <- 参照変更

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 5050
    to_port     = 5050
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Environment = var.environment }
}

# セキュリティグループ: RDS
resource "aws_security_group" "rds" {
  name        = "${var.environment}-rds-sg"
  description = "Allow PostgreSQL"
  vpc_id      = module.vpc.vpc_id # <- 参照変更

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Environment = var.environment }
}

# Application Load Balancer (Frontend)
resource "aws_lb" "frontend" {
  name               = "${var.environment}-front-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = module.vpc.public_subnets # <- 参照変更
  security_groups    = [aws_security_group.app.id]

  tags = { Environment = var.environment }
}

resource "aws_lb_target_group" "frontend" {
  name        = "${var.environment}-front-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id # <- 参照変更
  target_type = "ip"
}

resource "aws_lb_listener" "frontend_http" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Application Load Balancer (Backend)
resource "aws_lb" "backend" {
  name               = "${var.environment}-api-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = module.vpc.public_subnets # <- 参照変更
  security_groups    = [aws_security_group.app.id]

  tags = { Environment = var.environment }
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.environment}-api-tg"
  port        = 5050
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id # <- 参照変更
  target_type = "ip"
}

resource "aws_lb_listener" "backend_http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# ECR リポジトリ
resource "aws_ecr_repository" "backend" {
  name = "${var.environment}-backend"
  force_delete = true
}
resource "aws_ecr_repository" "frontend" {
  name = "${var.environment}-frontend"
  force_delete = true
}

# ECS クラスター
resource "aws_ecs_cluster" "backend" {
  name = "${var.environment}-api"
}
resource "aws_ecs_cluster" "frontend" {
  name = "${var.environment}-front"
}

# カスタムDBパラメータグループ
resource "aws_db_parameter_group" "custom_rds_pg" {
  name   = "${var.environment}-custom-rds-pg"
  family = "postgres17" # 必要に応じてバージョン確認・修正

  parameter {
    name         = "rds.force_ssl"
    value        = "0"
    apply_method = "immediate"
  }

  tags = { Environment = var.environment }
}

# RDS (PostgreSQL)
resource "aws_db_subnet_group" "rds" {
  name       = "${var.environment}-rds-subnet-group"
  subnet_ids = module.vpc.private_subnets # <- 参照変更
  tags = { Environment = var.environment }
}
resource "aws_db_instance" "rds" {
  identifier              = "${var.environment}-db"
  engine                  = "postgres"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.rds.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  skip_final_snapshot     = true
  publicly_accessible     = false
  parameter_group_name    = aws_db_parameter_group.custom_rds_pg.name
  multi_az                = false  # Multi-AZ無効化 (コスト削減 -$15/月)
  backup_retention_period = 7      # バックアップは7日間保持
  backup_window          = "03:00-04:00"  # JST 12:00-13:00
  maintenance_window     = "sun:04:00-sun:05:00"  # JST日曜13:00-14:00
  tags = { Environment = var.environment }
}

# SSM Parameter Store
resource "aws_ssm_parameter" "api_base_url" {
  name  = "/${var.environment}/api-base-url"
  type  = "String"
  value = var.api_base_url
}

# Secrets Manager (backend.env)
# resource "random_id" "secret_suffix" {
#   byte_length = 4
# }
resource "aws_secretsmanager_secret" "backend_env" {
  name                         = "${var.environment}/api/env"
  recovery_window_in_days      = 7
  description                  = "Environment variables for backend application in ${var.environment}"
  tags = { Environment = var.environment, Application = "backend" }
}

# === VPC エンドポイント定義 (個別リソースとして定義) ===

# VPCエンドポイント用のセキュリティグループ
resource "aws_security_group" "vpc_endpoint" {
  name        = "${var.environment}-vpce-sg"
  description = "Allow HTTPS from App SG for VPC Endpoint"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    # タスクが使用するappセキュリティグループからのアクセスを許可
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Environment = var.environment }
}

# Secrets Manager VPC Endpoint
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type = "Interface"
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [aws_security_group.vpc_endpoint.id]
  private_dns_enabled = true
  tags = {
    Name        = "${var.environment}-secretsmanager-vpce"
    Environment = var.environment
  }
}

# ECR API VPC Endpoint
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type = "Interface"
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [aws_security_group.vpc_endpoint.id]
  private_dns_enabled = true
  tags = {
    Name        = "${var.environment}-ecr-api-vpce"
    Environment = var.environment
  }
}

# ECR DKR VPC Endpoint (削除: コスト削減 -$22.5/月)
# resource "aws_vpc_endpoint" "ecr_dkr" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.ecr.dkr"
#   vpc_endpoint_type = "Interface"
#   subnet_ids         = module.vpc.private_subnets
#   security_group_ids = [aws_security_group.vpc_endpoint.id]
#   private_dns_enabled = true
#   tags = {
#     Name        = "${var.environment}-ecr-dkr-vpce"
#     Environment = var.environment
#   }
# }

# CloudWatch Logs VPC Endpoint (削除: コスト削減 -$22.5/月)
# resource "aws_vpc_endpoint" "logs" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.logs"
#   vpc_endpoint_type = "Interface"
#   subnet_ids         = module.vpc.private_subnets
#   security_group_ids = [aws_security_group.vpc_endpoint.id]
#   private_dns_enabled = true
#   tags = {
#     Name        = "${var.environment}-logs-vpce"
#     Environment = var.environment
#   }
# }

# The following S3 Gateway VPC Endpoint block is removed as it's now managed by the VPC module
# Restore the external definition
# S3 Gateway VPC Endpoint
resource "aws_vpc_endpoint" "s3_gateway" {
  vpc_id       = module.vpc.vpc_id
  service_name = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  # プライベートサブネットのルートテーブルに関連付ける
  # Use the module's output for private route table IDs
  route_table_ids = module.vpc.private_route_table_ids

  tags = {
    Name        = "${var.environment}-s3-gateway-vpce"
    Environment = var.environment
  }
}

# --- VPC エンドポイント定義 ここまで ---

# --- ここから追加 ---
# アイコン用 S3 バケットを追加
resource "aws_s3_bucket" "icon_images" {
  bucket = var.icon_images_bucket_name # ★ 変数を使用
  tags = {
    Name        = "${var.environment}-icon-images"
    Environment = var.environment
  }
}

# ★ S3バケットのパブリックアクセスブロック設定
resource "aws_s3_bucket_public_access_block" "icon_images" {
  bucket = aws_s3_bucket.icon_images.id

  block_public_acls       = true
  block_public_policy     = false # ★ バケットポリシーによるパブリックアクセスを許可
  ignore_public_acls      = true
  restrict_public_buckets = false # ★ パブリックバケットと見なされるのを制限しない
}

# ★ S3バケットポリシーを追加
resource "aws_s3_bucket_policy" "icon_images_public_read" {
  bucket = aws_s3_bucket.icon_images.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadForIconsFolder"
        Effect    = "Allow"
        Principal = "*"
        Action    = [
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.icon_images.arn}/icons/*"
        ]
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.icon_images]
}
# --- ここまで追加 ---

# --- Outputs --- 