# Terraform outputs for PROD environment (using STG VPC)

# Note: These outputs might reflect STG resources if not overridden in PROD

output "stg_vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "stg_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "backend_security_group_id" {
  description = "The ID of the backend security group"
  value       = aws_security_group.app.id
}

output "vpc_module_private_route_table_ids" {
  description = "The ID of the private route tables"
  value       = module.vpc.private_route_table_ids
}

output "vpc_module_private_subnets" {
  description = "The ID of the private subnets"
  value       = module.vpc.private_subnets
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "The ID of the public subnets"
  value       = module.vpc.public_subnets
}

output "backend_cluster_name" {
  description = "The name of the backend ECS cluster"
  value       = aws_ecs_cluster.backend.name
} 