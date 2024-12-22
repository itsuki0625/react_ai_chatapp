FROM node:20-alpine

# 作業ディレクトリを設定
WORKDIR /app

# パッケージファイルをコピー
COPY package*.json ./

# 依存関係をインストール（開発用も含めて全て）
RUN npm install --legacy-peer-deps

# アプリケーションのソースコードをコピー
COPY . .

# 開発用ポートを開放
EXPOSE 3000

# 開発モードで起動
CMD ["npm", "run", "dev"]

