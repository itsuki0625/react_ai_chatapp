# ビルドステージ
FROM node:18-alpine AS build

# 作業ディレクトリを設定
WORKDIR /app

# `package.json`と`package-lock.json`をコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm install --legacy-peer-deps

# アプリケーションのソースコードをコピー
COPY . .

# アプリケーションをビルド
RUN npm run build

# 本番ステージ
FROM nginx:alpine

# Nginxの設定ファイルを削除
RUN rm -rf /usr/share/nginx/html/*

# ビルドしたファイルをNginxの公開ディレクトリにコピー
COPY --from=build /app/build /usr/share/nginx/html

# ポート3000を開放
EXPOSE 80

# Nginxをフォアグラウンドで実行
CMD ["nginx", "-g", "daemon off;"]
