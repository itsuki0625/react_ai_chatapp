# Terraform outputs for STG environment

output "stg_subnets" {
  description = "STG ECS タスク用 Public Subnets"
  value       = module.vpc.public_subnets
}

output "stg_security_groups" {
  description = "STG ECS タスク用セキュリティグループ (App SG)"
  value       = [aws_security_group.app.id]
} 