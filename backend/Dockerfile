# ベースイメージとして公式のPythonイメージを使用
FROM python:3.11-slim

WORKDIR /app

# システムの依存関係をインストール（必要に応じて）
RUN apt-get update && apt-get install -y build-essential

# `requirements.txt`をコピーして依存関係をインストール
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

ENV PYTHONPATH=/app

# ポート5000を開放
EXPOSE 5000

# マイグレーション用のスクリプトを追加
COPY ./scripts/start.sh /start.sh
COPY ./scripts/migrate.sh /migrate.sh
COPY ./scripts/seed.sh /seed.sh
RUN chmod +x /start.sh /migrate.sh /seed.sh

# 起動コマンドを変更
CMD ["/start.sh"]