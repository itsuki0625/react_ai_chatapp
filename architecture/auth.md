# 認証システム概要

このドキュメントでは、Next.js（フロントエンド）と FastAPI（バックエンド）を使用するアプリケーションの認証システムの概要を説明します。

## 1. 基本方針

-   **認証方式**: 完全なステートレス JWT (JSON Web Token) 認証を採用します。
-   **トークン**:
    -   **Access Token**: 短命（例: 15 分）で、API リクエスト時の認証に使用されます。
    -   **Refresh Token**: 長命（例: 30 日）で、Access Token の再発行に使用されます。
-   **状態管理**: バックエンド (FastAPI) はユーザセッション状態を持たず、各リクエストで JWT の署名を検証します。
-   **トークン失効**: ログアウトやパスワード変更時には、Refresh Token を無効化リスト（ブラックリスト）に登録して失効させます。

## 2. 認証フロー

### 2.1 サインアップ

1.  ユーザーがフロントエンドでメールアドレス、パスワードなどを入力します。
2.  フロントエンドはバックエンドの `/api/v1/auth/signup` エンドポイントに POST リクエストを送信します。
3.  バックエンドは入力値を検証し、メールアドレスの重複を確認します。
4.  パスワードをハッシュ化（例: bcrypt）してデータベースに保存します。
5.  （オプション）メール認証用のトークンを含むリンクをユーザーのメールアドレスに送信します。
6.  認証が完了すると、バックエンドは Access Token と Refresh Token を生成してレスポンスとして返します。
7.  フロントエンド (NextAuth.js) は受け取ったトークンを安全に保存します。
    -   Access Token: メモリ内、または `HttpOnly` Cookie（`SameSite=Lax` または `Strict`）。Authorization ヘッダーでの送信も考慮。
    -   Refresh Token: `HttpOnly`, `Secure`, `SameSite=Strict` (または `Lax`) 属性付きの Cookie に保存します。

### 2.2 ログイン

1.  ユーザーがフロントエンドでメールアドレスとパスワードを入力します。
2.  フロントエンドは NextAuth.js の Credentials Provider を使用し、バックエンドの `/api/v1/auth/login` エンドポイントに POST リクエストを送信します。
3.  バックエンドは認証情報を検証し、成功した場合、新しい Access Token と Refresh Token を生成して返します。
4.  フロントエンドはサインアップ時と同様にトークンを保存します。

### 2.3 トークンリフレッシュ

1.  Access Token の有効期限が切れた場合、フロントエンド (NextAuth.js のコールバックやミドルウェア) は自動的に Refresh Token を使用してバックエンドの `/api/v1/auth/refresh` エンドポイントに POST リクエストを送信します。
2.  バックエンドは受け取った Refresh Token を検証します（有効期限、失効リストの確認）。
3.  検証が成功した場合、新しい Access Token（およびオプションで新しい Refresh Token）を生成して返します。古い Refresh Token は失効リストに追加される場合があります。
4.  フロントエンドは新しいトークンで既存のトークンを更新します。

### 2.4 ログアウト

1.  ユーザーがフロントエンドでログアウト操作を行います。
2.  フロントエンドはバックエンドの `/api/v1/auth/logout` エンドポイントに POST リクエストを送信します（通常、Refresh Token をリクエストボディや Cookie 経由で渡します）。
3.  バックエンドは受け取った Refresh Token を失効リストに登録します。
4.  フロントエンドは保存している Access Token と Refresh Token (Cookie など) を削除します。

## 3. 技術スタック

| コンポーネント        | 技術                                                 | 役割                                      |
| --------------------- | ---------------------------------------------------- | ----------------------------------------- |
| **フロントエンド**    | Next.js, NextAuth.js (v5 or later)                   | UI、認証状態管理、トークン保存、API コール    |
| **バックエンド**      | FastAPI, Python                                      | API 提供、JWT 生成/検証、ビジネスロジック |
| **JWT ライブラリ**    | `python-jose` または `pyjwt` (`[crypto]` オプション付) | JWT のエンコード/デコード、署名/検証        |
| **パスワードハッシュ**| `passlib` (`bcrypt`)                                 | パスワードの安全なハッシュ化              |
| **データベース**      | PostgreSQL                                           | ユーザー情報、ロール、権限などの永続化    |
| **失効リスト**        | Redis または PostgreSQL                              | Refresh Token のブラックリスト管理        |
| **コンテナ化**        | Docker, Docker Compose                               | 開発・本番環境の構築、実行                |

*   **環境変数 (.env)**: `DATABASE_URL`, `SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `NEXTAUTH_URL`, `AUTH_SECRET` などが設定されます。
*   **docker-compose.yml**: `frontend`, `backend`, `db` サービスを定義し、ネットワーク連携や環境変数の設定を行います。

## 4. API エンドポイント (例)

| Method | Path                           | 説明                     |
| ------ | ------------------------------ | ------------------------ |
| `POST` | `/api/v1/auth/signup`          | 新規ユーザー登録         |
| `POST` | `/api/v1/auth/login`           | ログイン                 |
| `POST` | `/api/v1/auth/refresh`         | Access Token の再発行    |
| `POST` | `/api/v1/auth/logout`          | ログアウト (Refresh Token失効) |
| `GET`  | `/api/v1/users/me`             | 認証済みユーザー情報取得 |
| `POST` | `/api/v1/auth/change-password` | パスワード変更           |
| `DELETE`| `/api/v1/auth/delete-account` | アカウント削除           |

## 5. トークン管理

| 種類          | 保管場所 (フロントエンド)                                       | 期限 (例) | 特徴                                                                 |
| ------------- | ------------------------------------------------------------- | -------- | -------------------------------------------------------------------- |
| **Access Token** | メモリ内、または `HttpOnly` Cookie (`SameSite=Lax`/`Strict`) | 15 分    | API リクエスト時に `Authorization: Bearer <token>` ヘッダーで送信される |
| **Refresh Token**| `HttpOnly`, `Secure`, `SameSite=Strict` Cookie              | 30 日    | Access Token 再発行専用。バックエンドで失効リスト管理 (`jti` クレーム使用) |

## 6. セキュリティ考慮事項

-   **HTTPS**: 通信は常に HTTPS で暗号化します。
-   **JWT 署名アルゴリズム**: `RS256` (公開鍵/秘密鍵) または `HS256` (共通鍵) を使用します。`RS256` の方がより安全性が高いとされます。秘密鍵はバックエンドのみが保持します。
-   **Cookie 属性**: `HttpOnly`, `Secure`, `SameSite` 属性を適切に設定し、XSS や CSRF 攻撃のリスクを軽減します。
-   **CSRF 対策**: Access Token を Cookie で管理する場合、Double Submit Cookie や SameSite 属性の利用を検討します。
-   **レート制限**: ログイン、サインアップ、トークンリフレッシュのエンドポイントにはレート制限を適用し、ブルートフォース攻撃を防ぎます。
-   **パスワードポリシー**: 強力なパスワードポリシーを強制します。
-   **メール認証**: サインアップ時にメールアドレスの所有確認を行います。
-   **依存関係の脆弱性**: 使用するライブラリの脆弱性を定期的にチェックし、更新します。
