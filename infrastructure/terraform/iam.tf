data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name               = "${var.environment}-ecs-task-exec-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
  tags = { Environment = var.environment }
}

resource "aws_iam_role_policy_attachment" "ecs_task_exec_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecs_ecr_pull_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# --- Add Secrets Manager Access Policy ---

# 現在のリージョンとアカウントIDを取得
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Secrets Manager から特定のシークレットを読み取る権限を定義
data "aws_iam_policy_document" "ecs_task_secrets_access" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    # 一時的に全てのシークレットへのアクセスを許可（デバッグ目的）
    resources = ["*"] 
    # resources = [
    #   "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:stg/backend/env-*",
    #   "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:stg/api/env-*" 
    # ] # 元の指定をコメントアウト
  }
}

# 上記ドキュメントから IAM ポリシーを作成
resource "aws_iam_policy" "ecs_task_secrets_policy" {
  name        = "${var.environment}-ecs-task-secrets-policy"
  description = "Allow ECS tasks to access specific secrets"
  policy      = data.aws_iam_policy_document.ecs_task_secrets_access.json
}

# 作成したポリシーを ECS タスク実行ロールにアタッチ
resource "aws_iam_role_policy_attachment" "ecs_task_secrets_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.ecs_task_secrets_policy.arn
}
# --- End Secrets Manager Access Policy --- 