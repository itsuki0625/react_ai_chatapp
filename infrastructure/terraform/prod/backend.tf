terraform {
  backend "s3" {
    bucket         = "smartao-prod-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "smartao-prod-terraform-lock"
  }
} 