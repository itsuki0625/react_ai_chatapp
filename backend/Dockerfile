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

# ポート5000を開放
EXPOSE 5000

# サーバーの起動コマンド
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000","--reload"]