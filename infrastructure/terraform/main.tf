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
  enable_nat_gateway   = false
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

# Application Load Balancer (Frontend)
resource "aws_lb" "frontend" {
  name               = "${var.environment}-front-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = module.vpc.public_subnets
  security_groups    = [aws_security_group.app.id]

  tags = { Environment = var.environment }
}

resource "aws_lb_target_group" "frontend" {
  name        = "${var.environment}-front-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
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
  subnets            = module.vpc.public_subnets
  security_groups    = [aws_security_group.app.id]

  tags = { Environment = var.environment }
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.environment}-api-tg"
  port        = 5050
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
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
  db_name                 = var.db_name
  db_subnet_group_name    = aws_db_subnet_group.rds.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  skip_final_snapshot     = true
  publicly_accessible     = false
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

# RDS CA 証明書バンドルのダウンロード URL を取得
data "http" "rds_ca_bundle" {
  url = "https://truststore.pki.rds.amazonaws.com/rds-combined-ca-bundle.pem" # 公式の最新結合バンドルURL
}

# ★ 追加: CA証明書保存用のS3バケット
# (既存バケットを使う場合は、このリソースは不要で、下の aws_s3_object の bucket を既存バケット名にする)
resource "aws_s3_bucket" "ca_certs" {
  bucket = "${var.environment}-rds-ca-certs-${data.aws_caller_identity.current.account_id}" # グローバルに一意な名前
  # 必要に応じてバージョニングや暗号化などを設定
  tags = {
    Environment = var.environment
    Name        = "${var.environment}-rds-ca-certs"
  }
}

# ★ 変更: ダウンロードした証明書バンドルをS3オブジェクトとして保存
resource "aws_s3_object" "rds_ca_bundle_pem" {
  bucket  = aws_s3_bucket.ca_certs.id # ★ 作成したバケットID (または既存バケット名)
  key     = "certs/rds-ca-${var.environment}-bundle.pem" # S3内のオブジェクトキー
  content = data.http.rds_ca_bundle.response_body
  # content_type は text/plain が適切か？ pemファイルなのでそれでも良いか。
  content_type = "application/x-pem-file" # または text/plain

  # RDSインスタンスの作成後に実行されるようにする
  depends_on = [aws_db_instance.rds, aws_s3_bucket.ca_certs]
} 