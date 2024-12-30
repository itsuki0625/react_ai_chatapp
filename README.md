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
    - docker-compose run --rm backend alembic revision --autogenerate -m "Initial migration"   
2. マイグレーションを行う
    - docker-compose exec backend alembic upgrade head
4. アプリケーションを起動する
    - docker-compose down
    - docker-compose up -d

