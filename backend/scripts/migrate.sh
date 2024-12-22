#!/bin/bash

# マイグレーションを実行
alembic upgrade head

# シードデータを挿入
python app/seeds/run_seeds.py

echo "Migration and seeding completed successfully!" 