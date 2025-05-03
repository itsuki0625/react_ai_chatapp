terraform {
  backend "s3" {
    bucket         = "smartao-stg-terraform-state"    # 事前に作成したS3バケット名に置き換えてください
    key            = "stg/terraform.tfstate"      # ステージング環境用のstateファイルキー
    region         = "ap-northeast-1"            # AWSリージョンを指定
    encrypt        = true                         # サーバーサイド暗号化を有効化
    dynamodb_table = "smartao-stg-terraform-lock"     # 事前に作成したDynamoDBテーブル名に置き換えてください
  }
} 