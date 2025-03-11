# データベースの初期設定

1. データベースの設定を行う
    - docker-compose up -d
2. 初回のマイグレーションを行う
    - docker-compose run --rm backend alembic revision --autogenerate -m "Initial migration"    
3. マイグレーションを行う
    - docker-compose exec backend alembic upgrade head
4. デモデータを挿入する
    - docker-compose exec backend python -m app.database.init_db


# データベース設定

1. データベースの設定を行う
    - docker-compose up -d
2. 初回のマイグレーションを行う
    - docker-compose exec backend bash
2. マイグレーションを行う
    - alembic revision --autogenerate -m "WWW"
3. マイグレーションを行う
    - alembic upgrade head
4. アプリケーションを起動する
    - docker-compose down
    - docker-compose up -d


AWS_ACCESS_KEY_ID: AWSのアクセスキーID
AWS_SECRET_ACCESS_KEY: AWSのシークレットアクセスキー
EC2_HOST: EC2インスタンスのパブリックIP or DNS
EC2_USERNAME: EC2のSSHユーザー名（通常は'ec2-user'）
EC2_SSH_KEY: EC2インスタンスへのSSH秘密鍵
DB_HOST: RDSのエンドポイント
DB_PORT: RDSのポート（通常は5432）
DB_NAME: データベース名
DB_USER: データベースユーザー
DB_PASSWORD: データベースパスワード
OPENAI_API_KEY: OpenAIのAPIキー
SECRET_KEY: バックエンドのシークレットキー
