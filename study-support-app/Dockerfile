FROM node:20-alpine

# 作業ディレクトリを設定
WORKDIR /app

# パッケージファイルをコピー
COPY package*.json ./

# npmのキャッシュをクリアしてからインストールを実行
RUN npm cache clean --force && \
    npm install --legacy-peer-deps && \
    npm install -g next

# アプリケーションのソースコードをコピー
COPY . .

# 開発用ポートを開放
EXPOSE 3000

# 開発モードで起動
CMD ["npm", "run", "dev", "--", "-p", "3000"]

