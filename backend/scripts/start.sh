#!/bin/bash

# マイグレーションの自動実行を削除し、アプリケーションの起動のみを行う
uvicorn app.main:app --host 0.0.0.0 --port 5050 --reload 