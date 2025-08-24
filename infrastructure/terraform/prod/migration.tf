# 権限マイグレーション機能をProd環境に追加

module "migration_task" {
  source = "../modules/migration-task"
  
  environment             = var.environment
  aws_region             = var.aws_region
  cluster_id             = aws_ecs_cluster.backend.id
  vpc_id                 = module.vpc.vpc_id
  private_subnets        = module.vpc.private_subnets
  app_security_group_id  = aws_security_group.app.id
  ecr_repository_url     = aws_ecr_repository.backend.repository_url
  secrets_manager_arn    = aws_secretsmanager_secret.backend_env.arn
  execution_role_arn     = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn          = aws_iam_role.ecs_task_role.arn
}

# マイグレーション実行用のIAMポリシーを追加
resource "aws_iam_policy" "migration_policy" {
  name        = "${var.environment}-migration-policy"
  description = "Additional permissions for migration tasks"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup"
        ]
        Resource = "${module.migration_task.migration_log_group}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.backend_env.arn
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      }
    ]
  })
}

# 既存のタスクロールにマイグレーションポリシーを追加
resource "aws_iam_role_policy_attachment" "migration_policy_attachment" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.migration_policy.arn
}

# 出力
output "migration_task_arn" {
  description = "ARN of migration task definition"
  value       = module.migration_task.migration_task_definition_arn
}

output "migration_log_group" {
  description = "CloudWatch log group for migration"
  value       = module.migration_task.migration_log_group
}
