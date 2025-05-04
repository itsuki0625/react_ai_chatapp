variable "aws_region" {
  type    = string
  default = "ap-northeast-1"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "azs" {
  type    = list(string)
  default = ["ap-northeast-1a", "ap-northeast-1c"]
}

variable "public_subnets" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  type    = list(string)
  default = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "The allocated storage in gibibytes for the database instance"
  type        = number
  default     = 20
}

variable "db_username" {
  type    = string
  default = "monono"
}

variable "db_password" {
  type = string
  description = "password"
}

variable "db_name" {
  type    = string
  default = "demo"
}

variable "api_base_url" {
  type        = string
  description = "http://stg-api.smartao.jp"
}

# ★ アイコン用S3バケット名
variable "icon_images_bucket_name" {
  description = "The name of the S3 bucket for user icons"
  type        = string
  default     = "prod-icon-images" # ★ デフォルト値を環境に合わせて設定 (例: prod-icon-images)
} 