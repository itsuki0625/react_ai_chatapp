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

  # VPC Flow Logs (オプション)
  # enable_flow_log                      = true
  # create_flow_log_cloudwatch_log_group = true
  # create_flow_log_cloudwatch_iam_role  = true

  # --- VPC Endpoints ---
  # Gateway Endpoints
  create_gateway_endpoints = true
  gateway_endpoints = {
    s3 = {
      tags = { Name = "${var.environment}-s3-gateway-vpce" }
    }
  }

  # Interface Endpoints
  create_interface_endpoints = true
  interface_endpoints = {
    secretsmanager = {
      tags = { Name = "${var.environment}-secretsmanager-vpce" }
    },
    ecs = {
      tags = { Name = "${var.environment}-ecs-vpce" }
    },
    "ecr.api" = { # Need quotes for keys with dots
      tags = { Name = "${var.environment}-ecr-api-vpce" }
    },
    "ecr.dkr" = {
      tags = { Name = "${var.environment}-ecr-dkr-vpce" }
    },
    logs = {
      tags = { Name = "${var.environment}-logs-vpce" }
    }
  }

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
  parameter_group_name = aws_db_parameter_group.custom_rds_pg.name
  tags = { Environment = var.environment }
}

# SSM Parameter Store
resource "aws_ssm_parameter" "api_base_url" {
  name  = "/${var.environment}/api-base-url"
  type  = "String"
  value = var.api_base_url
}

# Secrets Manager (backend.env)
resource "random_id" "secret_suffix" {
  byte_length = 4
}
resource "aws_secretsmanager_secret" "backend_env" {
  name                         = "${var.environment}/api/env-${random_id.secret_suffix.hex}"
  recovery_window_in_days      = 0
}

# --- VPC エンドポイント定義 (VPCモジュール内で作成されるため、個別の定義は削除) ---
# # Secrets Manager VPC Endpoint
# resource "aws_vpc_endpoint" "secretsmanager" { ... }

# # VPCエンドポイント用のセキュリティグループ
# # VPCモジュールがエンドポイント用のSGを作成するため、個別定義は不要になる場合が多い
# # 必要であれば、module.vpc.default_security_group_idなどを参照するか、
# # module.vpc.endpoint_security_group_ids を利用する
# resource "aws_security_group" "vpc_endpoint" { ... }

# # ECR API Endpoint
# resource "aws_vpc_endpoint" "ecr_api" { ... }

# # ECR DKR Endpoint
# resource "aws_vpc_endpoint" "ecr_dkr" { ... }

# # CloudWatch Logs Endpoint
# resource "aws_vpc_endpoint" "logs" { ... }

# # S3 Gateway Endpoint
# resource "aws_vpc_endpoint" "s3_gateway" { ... }

# --- VPC エンドポイント定義 ここまで --- 