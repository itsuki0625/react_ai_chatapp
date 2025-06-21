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

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name                 = "${var.environment}-vpc"
  cidr                 = var.vpc_cidr
  azs                  = var.azs
  public_subnets       = var.public_subnets
  private_subnets      = var.private_subnets
  enable_nat_gateway   = false  # STG環境ではコスト削減のため無効
  single_nat_gateway   = false  # NAT Gateway無効のため無効
  enable_dns_hostnames = true
  manage_default_network_acl = false

  tags = { Environment = var.environment }
}

# セキュリティグループ: アプリケーション
resource "aws_security_group" "app" {
  name        = "${var.environment}-app-sg"
  description = "Allow HTTP/3000/5050"
  vpc_id      = module.vpc.vpc_id

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
  vpc_id      = module.vpc.vpc_id

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

# Application Load Balancer削除 (STG環境はALBなしでコスト削減)
# resource "aws_lb" "main" {
#   name               = "${var.environment}-main-alb"
#   internal           = false
#   load_balancer_type = "application"
#   subnets            = module.vpc.public_subnets
#   security_groups    = [aws_security_group.app.id]
#   tags = { Environment = var.environment }
# }

# resource "aws_lb_target_group" "frontend" {
#   name        = "${var.environment}-front-tg"
#   port        = 3000
#   protocol    = "HTTP"
#   vpc_id      = module.vpc.vpc_id
#   target_type = "ip"
# }

# resource "aws_lb_target_group" "backend" {
#   name        = "${var.environment}-api-tg"
#   port        = 5050
#   protocol    = "HTTP"
#   vpc_id      = module.vpc.vpc_id
#   target_type = "ip"
# }

# resource "aws_lb_listener" "main_http" {
#   load_balancer_arn = aws_lb.main.arn
#   port              = 80
#   protocol          = "HTTP"
#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.frontend.arn
#   }
# }

# resource "aws_lb_listener_rule" "backend" {
#   listener_arn = aws_lb_listener.main_http.arn
#   priority     = 100
#   action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.backend.arn
#   }
#   condition {
#     path_pattern {
#       values = ["/api/*"]
#     }
#   }
# }

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

# ★ 追加: カスタムDBパラメータグループ
resource "aws_db_parameter_group" "custom_rds_pg" {
  name   = "${var.environment}-custom-rds-pg"
  # ★ 注意: RDSのPostgreSQLバージョンに合わせてfamilyを修正してください (例: postgres14, postgres15)
  family = "postgres17"

  parameter {
    name         = "rds.force_ssl"
    value        = "0"         # SSL強制を無効化
    apply_method = "immediate" # 即時適用 (再起動が必要な場合あり)
  }

  tags = { Environment = var.environment }
}

# RDS (PostgreSQL)
resource "aws_db_subnet_group" "rds" {
  name       = "${var.environment}-rds-subnet-group"
  subnet_ids = module.vpc.private_subnets
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
  parameter_group_name = aws_db_parameter_group.custom_rds_pg.name # ★ 作成したパラメータグループを指定
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
  recovery_window_in_days      = 0
  description                  = "Environment variables for backend application in ${var.environment}"
  tags = { Environment = var.environment, Application = "backend" }
}

# Secrets Manager VPC Endpoint - STG環境ではコスト削減のため削除
# resource "aws_vpc_endpoint" "secretsmanager" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.secretsmanager" # リージョンを適切に指定
#   vpc_endpoint_type = "Interface"

#   # タスクが実行されるプライベートサブネットを指定
#   subnet_ids = module.vpc.private_subnets

#   # VPCエンドポイント用のセキュリティグループ (インバウンドHTTPSを許可)
#   security_group_ids = [aws_security_group.vpc_endpoint.id] # 新しく作成するSGを指定

#   private_dns_enabled = true # これにより、タスクは通常のエンドポイント名でアクセス可能

#   tags = {
#     Name        = "${var.environment}-secretsmanager-vpce"
#     Environment = var.environment
#   }
# }

# VPCエンドポイント用のセキュリティグループ - 使用しないためコメントアウト
# resource "aws_security_group" "vpc_endpoint" {
#   name        = "${var.environment}-vpce-sg"
#   description = "Allow HTTPS from App SG for VPC Endpoint"
#   vpc_id      = module.vpc.vpc_id

#   ingress {
#     from_port       = 443
#     to_port         = 443
#     protocol        = "tcp"
#     # タスクが使用するappセキュリティグループからのアクセスを許可
#     security_groups = [aws_security_group.app.id]
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   tags = { Environment = var.environment }
# }

# ECR API VPC Endpoint - STG環境ではコスト削減のため削除
# resource "aws_vpc_endpoint" "ecr_api" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.ecr.api"
#   vpc_endpoint_type = "Interface"

#   subnet_ids         = module.vpc.private_subnets # プライベートサブネットを指定
#   security_group_ids = [aws_security_group.vpc_endpoint.id] # Secrets Managerと同じSGを再利用可能
#   private_dns_enabled = true

#   tags = {
#     Name        = "${var.environment}-ecr-api-vpce"
#     Environment = var.environment
#   }
# }

# ECR DKR VPC Endpoint - STG環境ではコスト削減のため削除
# resource "aws_vpc_endpoint" "ecr_dkr" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.ecr.dkr"
#   vpc_endpoint_type = "Interface"

#   subnet_ids         = module.vpc.private_subnets # プライベートサブネットを指定
#   security_group_ids = [aws_security_group.vpc_endpoint.id] # Secrets Managerと同じSGを再利用可能
#   private_dns_enabled = true

#   tags = {
#     Name        = "${var.environment}-ecr-dkr-vpce"
#     Environment = var.environment
#   }
# }

# CloudWatch Logs VPC Endpoint - STG環境ではコスト削減のため削除
# resource "aws_vpc_endpoint" "logs" {
#   vpc_id            = module.vpc.vpc_id
#   service_name      = "com.amazonaws.${var.aws_region}.logs"
#   vpc_endpoint_type = "Interface"

#   subnet_ids         = module.vpc.private_subnets # プライベートサブネットを指定
#   security_group_ids = [aws_security_group.vpc_endpoint.id] # 既存のSGを再利用
#   private_dns_enabled = true

#   tags = {
#     Name        = "${var.environment}-logs-vpce"
#     Environment = var.environment
#   }
# }

# The following S3 Gateway VPC Endpoint block is removed as it's now managed by the VPC module
# Restore the external definition
# S3 Gateway VPC Endpoint - 無料なので残す
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

# アイコン用 S3 バケットを追加
resource "aws_s3_bucket" "icon_images" {
  bucket = "${var.environment}-icon-images"

  tags = {
    Name        = "${var.environment}-icon-images"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_public_access_block" "icon_images" {
  bucket = aws_s3_bucket.icon_images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# アイコン用バケット名を出力
output "icon_images_bucket_name" {
  description = "S3 bucket name for icon images"
  value       = aws_s3_bucket.icon_images.bucket
} 