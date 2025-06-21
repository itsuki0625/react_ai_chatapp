# ECS Task Definitions and Services for frontend & backend

# Backend task definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "backend-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "256"  # 512MB → 256MB (コスト削減)
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  container_definitions    = jsonencode([
    {
      name      = "backend",
      image     = "${aws_ecr_repository.backend.repository_url}:latest",
      essential = true,
      portMappings = [
        { containerPort = 5050, protocol = "tcp" }
      ],
      # 環境変数は Secrets Manager から取得 (ECSが自動展開)
      secrets = [
        {
          name      = "BACKEND_ENV_SECRETS" # Temporary name
          valueFrom = aws_secretsmanager_secret.backend_env.arn # Reference the Secret ARN
        }
      ],
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.environment}-api"
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
  platform_version = "1.4.0"
  network_configuration {
    security_groups = [aws_security_group.app.id]
    subnets         = module.vpc.public_subnets
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
  memory                   = "256"  # 512MB → 256MB (コスト削減)
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  container_definitions    = jsonencode([
    {
      name      = "frontend",
      image     = "${aws_ecr_repository.frontend.repository_url}:latest",
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
  platform_version = "1.4.0"
  network_configuration {
    security_groups = [aws_security_group.app.id]
    subnets         = module.vpc.public_subnets
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }
  depends_on = [ aws_lb_listener.frontend_http ]
} 