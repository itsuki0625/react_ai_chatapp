import secrets

# 安全な乱数を使用して鍵を生成
secret_key = secrets.token_urlsafe(32)
print(secret_key)  