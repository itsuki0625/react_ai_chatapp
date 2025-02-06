# ベースイメージとして公式のPythonイメージを使用
FROM python:3.11-slim

WORKDIR /app

# システムの依存関係をインストール（修正）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# `requirements.txt`をコピーして依存関係をインストール
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

ENV PYTHONPATH=/app


# ポート5050を開放
EXPOSE 5050

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5050", "--reload"]