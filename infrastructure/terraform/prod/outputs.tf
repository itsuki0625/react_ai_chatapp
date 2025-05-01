# Terraform outputs for PROD environment (using STG VPC)

# Note: These outputs might reflect STG resources if not overridden in PROD

output "stg_subnets" {
  description = "STG ECS タスク用 Private Subnets (Referenced by PROD)"
  value       = data.terraform_remote_state.stg.outputs.private_subnets
}

output "stg_security_groups" {
  description = "PROD ECS タスク用セキュリティグループ (App SG)"
  value       = [aws_security_group.app.id]
}

output "vpc_module_private_route_table_ids" {
  description = "List of IDs of private route tables created by the STG VPC module."
  value       = data.terraform_remote_state.stg.outputs.private_route_table_ids
}

output "vpc_module_private_subnets" {
  description = "List of IDs of private subnets created by the STG VPC module."
  value       = data.terraform_remote_state.stg.outputs.private_subnets
}

output "vpc_id" {
  description = "The ID of the VPC (from STG)"
  value       = data.terraform_remote_state.stg.outputs.vpc_id
}

output "public_subnets" {
  description = "List of IDs of public subnets (from STG)"
  value       = data.terraform_remote_state.stg.outputs.public_subnets
} 