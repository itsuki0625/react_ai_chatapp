# CloudWatch Log Groups for ECS Tasks

# Backend 用の CloudWatch Log Group を作成
resource "aws_cloudwatch_log_group" "backend_log_group" {
  # タスク定義で指定されているロググループ名
  name              = "/ecs/backend-stg" 
  # ログの保持期間 (例: 14日)
  retention_in_days = 14 
  tags = {
    Environment = var.environment
    Application = "backend"
  }
}

# Frontend 用の CloudWatch Log Group を作成
resource "aws_cloudwatch_log_group" "frontend_log_group" {
  # タスク定義で指定されているロググループ名
  name              = "/ecs/frontend-stg" 
  # ログの保持期間 (例: 14日)
  retention_in_days = 14
  tags = {
    Environment = var.environment
    Application = "frontend"
  }
} 