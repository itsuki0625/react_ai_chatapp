terraform {
  backend "s3" {
    bucket         = "YOUR-PROD-TERRAFORM-STATE-BUCKET"
    key            = "prod/terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "YOUR-PROD-TERRAFORM-LOCK-TABLE"
  }
} 