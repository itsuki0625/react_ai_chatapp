# Terraform outputs for STG environment

output "stg_subnets" {
  description = "STG ECS タスク用 Private Subnets"
  value       = module.vpc.private_subnets
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

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
} 