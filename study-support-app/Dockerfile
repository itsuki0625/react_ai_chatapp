FROM node:20-alpine

# 作業ディレクトリを設定
WORKDIR /app

# パッケージファイルをコピー
COPY package*.json ./

# npmのキャッシュをクリアしてからインストールを実行
RUN npm cache clean --force && \
    npm install --legacy-peer-deps && \
    npm install -g next

# 公開環境変数を直接指定
ENV NEXT_PUBLIC_API_BASE_URL=http://localhost:5050
ENV NEXT_PUBLIC_BROWSER_API_URL=http://localhost:5050
ENV INTERNAL_API_BASE_URL=http://localhost:5050
ENV NEXT_PUBLIC_ASSET_BASE_URL=http://localhost:5050
# NextAuth環境変数を追加（Build-time）
ENV NEXTAUTH_URL=http://localhost:3000
ENV NEXTAUTH_COOKIE_DOMAIN=localhost:3000
ENV NEXTAUTH_SECRET=gLl9JJlJN95emviDnWGSUZlm9u7He2n+C7YLxveaVoc=

# NextAuth用の環境変数を追加（Runtime）
ENV NEXTAUTH_URL=http://localhost:3000
ENV NEXTAUTH_COOKIE_DOMAIN=localhost:3000
ENV NEXTAUTH_SECRET=gLl9JJlJN95emviDnWGSUZlm9u7He2n+C7YLxveaVoc=


# アプリケーションのソースコードをコピー
COPY . .

# 開発用ポートを開放
EXPOSE 3000

# 開発モードで起動
CMD ["npm", "run", "dev", "--", "-p", "3000"]

