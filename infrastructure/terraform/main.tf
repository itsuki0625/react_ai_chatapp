terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws      = { source = "hashicorp/aws",      version = "~> 5.0" }
    external = { source = "hashicorp/external", version = "~> 2.1" }
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
}
resource "aws_ecr_repository" "frontend" {
  name = "${var.environment}-frontend"
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
resource "aws_secretsmanager_secret" "backend_env" {
  name = "${var.environment}/api/env"
}
resource "aws_secretsmanager_secret_version" "backend_env_version" {
  secret_id     = aws_secretsmanager_secret.backend_env.id
  secret_string = join("\n", [
    for key, value in local.backend_env : "${key}=${value}"
  ])
} 