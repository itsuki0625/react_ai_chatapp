# ECS Task Definitions and Services for frontend & backend

# Backend task definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.environment}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  container_definitions    = jsonencode([
    {
      name      = "backend",
      image     = "${aws_ecr_repository.backend.repository_url}:${var.environment}",
      essential = true,
      portMappings = [
        { containerPort = 5050, protocol = "tcp" }
      ],
      # 環境変数は全て SSM パラメータから取得
      secrets = [for param in aws_ssm_parameter.backend_env : {
        name      = split("/", param.name)[3] # 各キー名を抽出
        valueFrom = param.arn
      }],
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/backend-stg"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

# Backend service
resource "aws_ecs_service" "backend" {
  name            = "${var.environment}-api-service"
  cluster         = aws_ecs_cluster.backend.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  platform_version = "LATEST"
  network_configuration {
    subnets         = module.vpc.public_subnets
    security_groups = [aws_security_group.app.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 5050
  }
  depends_on = [ aws_lb_listener.backend_http ]
}

# Frontend task definition
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.environment}-front"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  container_definitions    = jsonencode([
    {
      name      = "frontend",
      image     = "${aws_ecr_repository.frontend.repository_url}:${var.environment}",
      essential = true,
      portMappings = [
        { containerPort = 3000, protocol = "tcp" }
      ],
      secrets = [
        {
          name      = "NEXT_PUBLIC_API_BASE_URL"
          valueFrom = aws_ssm_parameter.api_base_url.arn
        },
        {
          name      = "NEXT_PUBLIC_BROWSER_API_URL"
          valueFrom = aws_ssm_parameter.api_base_url.arn
        }
      ],
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.environment}-front"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

# Frontend service
resource "aws_ecs_service" "frontend" {
  name            = "${var.environment}-front-service"
  cluster         = aws_ecs_cluster.frontend.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  platform_version = "LATEST"
  network_configuration {
    subnets         = module.vpc.public_subnets
    security_groups = [aws_security_group.app.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }
  depends_on = [ aws_lb_listener.frontend_http ]
}

# Variable for secrets used by backend
variable "backend_secret_names" {
  type    = list(string)
  default = [
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "SECRET_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "NEXTAUTH_URL",
    "AUTH_SECRET"
  ]
}

# .env.stgをパースしてキー・値のマップを取得
data "external" "dotenv" {
  program = ["bash", "-c", <<-EOF
    echo -n '{'
    awk -F= '/^[A-Za-z0-9_]+=/{gsub(/"/,"\\\"",$2); printf "\"%s\":\"%s\",", $1, $2}' ../../backend/.env.stg | sed 's/,$//'
    echo '}'
EOF
  ]
}
locals {
  backend_env = data.external.dotenv.result
}

# SSMパラメータを for_each で自動作成
resource "aws_ssm_parameter" "backend_env" {
  for_each = local.backend_env
  name     = "/${var.environment}/backend/${each.key}"
  type     = "SecureString"
  value    = each.value
} 