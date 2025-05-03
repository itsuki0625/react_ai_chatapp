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

# Secrets Manager と S3 CA Cert へのアクセス権限を定義
data "aws_iam_policy_document" "ecs_task_secrets_access" {
  statement {
    sid    = "SecretsManagerAccess"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/api/env-*" # パターンを修正
      # frontend用のシークレットも必要であれば追加
      # "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.environment}/frontend/env-*" 
    ]
  }

  # ★ 追加: S3のCA証明書への読み取りアクセス権限
  statement {
    sid    = "S3CACertAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject"
    ]
    resources = [
      "arn:aws:s3:::${var.environment}-rds-ca-certs-${data.aws_caller_identity.current.account_id}/certs/rds-ca-${var.environment}-bundle.pem"
    ]
  }

  # ★ 追加: アイコン用 S3 バケットへのアクセス権限
  statement {
    sid    = "IconBucketAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
      # 必要に応じて ListBucket も追加
      # "s3:ListBucket"
    ]
    resources = [
      # S3 バケットの ARN を参照するように修正 (main.tfで定義したリソース名に合わせる)
      aws_s3_bucket.icon_images.arn,
      "${aws_s3_bucket.icon_images.arn}/*" # バケット内のオブジェクト ARN
    ]
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

# === Add Task Role for Application ===
resource "aws_iam_role" "ecs_task_role" {
  name               = "${var.environment}-ecs-task-role" # New role for the application itself
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json # Assumed by ecs-tasks
  tags = { Environment = var.environment }
}

# Attach the existing custom policy (Secrets Manager & S3 access) to the new Task Role
resource "aws_iam_role_policy_attachment" "ecs_task_role_secrets_attachment" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.ecs_task_secrets_policy.arn # Reuse the policy with S3/SecretsManager permissions
}
# === End Task Role for Application === 