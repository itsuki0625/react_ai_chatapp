# データベースの設定とマイグレーション

## 初期セットアップ
1. Dockerコンテナを起動する
   ```
   docker-compose up -d
   ```

2. マイグレーションファイルを作成する
   ```
   docker-compose exec backend alembic revision --autogenerate -m "説明を入力"
   ```

3. マイグレーションを適用する
   ```
   docker-compose exec backend alembic upgrade head
   ```

4. （必要に応じて）デモデータを挿入する
   ```
   docker-compose exec backend python -m app.database.init_db
   ```

## 既存のデータベースに変更を加える場合
1. Dockerコンテナが起動していることを確認
   ```
   docker-compose ps
   ```

2. 新しいマイグレーションファイルを作成
   ```
   docker-compose exec backend alembic revision --autogenerate -m "変更内容の説明"
   ```

3. マイグレーションを適用
   ```
   docker-compose exec backend alembic upgrade head
   ```

4. アプリケーションを再起動（必要な場合）
   ```
   docker-compose down
   docker-compose up -d
   ```

