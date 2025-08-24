# 権限マイグレーション専用のECS Task定義
# このモジュールはSTG/Prod両環境で使用可能

variable "environment" {
  description = "Environment name (stg or prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS Region"
  type        = string
}

variable "cluster_id" {
  description = "ECS Cluster ID"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnets" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Application security group ID"
  type        = string
}

variable "ecr_repository_url" {
  description = "Backend ECR repository URL"
  type        = string
}

variable "secrets_manager_arn" {
  description = "Secrets Manager ARN for backend env"
  type        = string
}

variable "execution_role_arn" {
  description = "ECS Task execution role ARN"
  type        = string
}

variable "task_role_arn" {
  description = "ECS Task role ARN"
  type        = string
}

# 権限マイグレーション専用のECS Task定義
resource "aws_ecs_task_definition" "migration_task" {
  family                   = "${var.environment}-migration-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"   # マイグレーション処理のため少し多め
  memory                   = "1024"  # マイグレーション処理のため少し多め
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn
  
  container_definitions = jsonencode([
    {
      name      = "migration"
      image     = "${var.ecr_repository_url}:${var.environment}"
      essential = true
      
      # マイグレーション用のコマンド上書き
      entryPoint = ["/bin/sh"]
      command = ["-c", "echo 'Migration task ready. Use AWS CLI to execute specific migration commands.'"]
      
      # 環境変数はSecrets Managerから取得
      secrets = [
        {
          name      = "BACKEND_ENV_SECRETS"
          valueFrom = var.secrets_manager_arn
        }
      ]
      
      # 追加の環境変数
      environment = [
        {
          name  = "MIGRATION_MODE"
          value = "true"
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
      
      # ログ設定
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.environment}-migration"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "migration"
          awslogs-create-group  = "true"
        }
      }
      
      # リソース制限
      memoryReservation = 512
      
      # ヘルスチェックを無効化（一時実行タスクのため）
      healthCheck = {
        command     = ["CMD-SHELL", "exit 0"]
        interval    = 30
        timeout     = 5
        retries     = 1
        startPeriod = 10
      }
    }
  ])

  tags = {
    Environment = var.environment
    Purpose     = "Migration"
  }
}

# CloudWatch Logs Group
resource "aws_cloudwatch_log_group" "migration_logs" {
  name              = "/ecs/${var.environment}-migration"
  retention_in_days = 30
  
  tags = {
    Environment = var.environment
    Purpose     = "Migration"
  }
}

# 出力
output "migration_task_definition_arn" {
  description = "ARN of the migration task definition"
  value       = aws_ecs_task_definition.migration_task.arn
}

output "migration_task_family" {
  description = "Family name of the migration task definition"
  value       = aws_ecs_task_definition.migration_task.family
}

output "migration_log_group" {
  description = "CloudWatch log group for migration tasks"
  value       = aws_cloudwatch_log_group.migration_logs.name
}
