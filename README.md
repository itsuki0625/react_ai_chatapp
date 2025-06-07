# データベースの設定とマイグレーション

## 初期セットアップ
1. Dockerコンテナを起動する
   ```
   docker-compose up -d
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

## ECS でのデモデータ挿入

Docker 上ではなく、ECS Fargate 上のコンテナで一度だけデモデータを挿入するには、ECS Exec 機能を使います。以下の手順を README に追記します。

1. **Execute Command の有効化**
   ```bash
   aws ecs update-service \
     --cluster smartao-api-stg \
     --service smartao-api-stg-service \
     --enable-execute-command \
     --region <your-region>
   ```
   - `smartao-api-stg` はバックエンドのクラスター名、`smartao-api-stg-service` はサービス名です。

2. **IAM 権限の確認**
   - タスク実行ロール (`ecsTaskExecutionRole`) に以下のポリシーをアタッチ:
     - `AmazonECSTaskExecutionRolePolicy`
     - `AmazonSSMManagedInstanceCore`
   - 操作ユーザーの IAM (CLI 実行者) に:
     - `ecs:ExecuteCommand`
     - SSM Session Manager 関連ポリシー (`ssm:StartSession`, `ssm:SendCommand` など)
     - CloudWatch Logs 書き込み権限

3. **タスク ARN を取得（タスクが稼働中であること）**
   ```bash
   aws ecs list-tasks \
     --cluster smartao-api-stg \
     --service-name smartao-api-stg-service \
     --region <your-region> \
     --query 'taskArns[0]' --output text
   ```

4. **Execute Command でシードスクリプトを実行**
   ```bash
   aws ecs execute-command \
     --cluster smartao-api-stg \
     --task <TASK_ARN> \
     --container backend \
     --interactive \
     --command "python scripts/seed_demo_data.py" \
     --region <your-region>
   ```
   - `scripts/seed_demo_data.py` は `backend/scripts/` に作成した初回デモデータ挿入スクリプトです。  
   - 実行後、デモデータが挿入され、CloudWatch Logs にも出力されます。

以上の手順で、ECS Fargate 上のコンテナに手を触れずに一時的にデータ挿入が可能です。


docker-compose exec backend pytest /app/services/agents/monono_agent/tests/llm_adapters

