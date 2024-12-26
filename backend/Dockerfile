# ベースイメージとして公式のPythonイメージを使用
FROM python:3.11-slim

WORKDIR /app

# システムの依存関係をインストール（必要に応じて）
RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# `requirements.txt`をコピーして依存関係をインストール
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

ENV PYTHONPATH=/app

# スクリプトに実行権限を付与
RUN chmod +x /app/scripts/start.sh

# ポート5000を開放
EXPOSE 5000

# 起動コマンドを変更（start.shスクリプトを使用する場合）
CMD ["/app/scripts/start.sh"]

# または直接uvicornを使用する場合は以下を使用
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]