# Terraform outputs for STG environment

output "stg_subnets" {
  description = "STG ECS タスク用 Public Subnets"
  value       = module.vpc.public_subnets
}

output "stg_security_groups" {
  description = "STG ECS タスク用セキュリティグループ (App SG)"
  value       = [aws_security_group.app.id]
}

output "vpc_module_private_route_table_ids" {
  description = "List of IDs of private route tables created by the VPC module."
  value       = module.vpc.private_route_table_ids
}

output "vpc_module_private_subnets" {
  description = "List of IDs of private subnets created by the VPC module."
  value       = module.vpc.private_subnets
} 