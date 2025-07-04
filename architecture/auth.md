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

### 2.2 ログイン (Credentials Provider)

1.  ユーザーがフロントエンドでメールアドレスとパスワードを入力します。
2.  フロントエンドは NextAuth.js の `CredentialsProvider` を使用します。このプロバイダー内の `authorize` 関数が実行されます。
3.  `authorize` 関数は、入力された認証情報（メール、パスワード）を `application/x-www-form-urlencoded` 形式にエンコードします。
4.  バックエンドの `/api/v1/auth/login` エンドポイントに `POST` リクエストを送信します。`Content-Type` ヘッダーは `application/x-www-form-urlencoded` に設定されます。
5.  バックエンドは認証情報を検証（ユーザー存在確認、パスワード照合）し、成功した場合、新しい Access Token と Refresh Token を含むユーザー情報を JSON レスポンスとして返します。
6.  `authorize` 関数はバックエンドからのレスポンスを受け取り、NextAuth.js が `jwt` コールバックで利用できる形式の `User` オブジェクト（アクセストークン、リフレッシュトークン、有効期限を含む）を返却します。
7.  ログインに失敗した場合（例: 認証情報不一致、バックエンドエラー）、`authorize` 関数は `null` を返し、NextAuth.js はエラー（`CredentialsSignin`）をスローしてログイン失敗として処理します。

### 2.3 トークンリフレッシュ (`jwt` コールバック)

NextAuth.js の `jwt` コールバックは、セッションが読み込まれる度（例: `getSession()`, `useSession()` 呼び出し時）や、特定のイベント（サインイン、サインアップ、`update()` 呼び出し）で実行され、JWT トークン (`token` オブジェクト) を管理します。

1.  **初回ログイン/サインアップ時 (`trigger === 'signIn' || trigger === 'signUp'`)**: `authorize` 関数から渡された `user` オブジェクトの情報（ユーザーID、名前、ロール、トークン、有効期限など）を使って、NextAuth.js の `token` オブジェクトを初期化します。
2.  **セッション更新時 (`trigger === 'update'`)**: `useSession().update()` などで渡された `session` データを使って、`token` オブジェクト内の情報（名前、学年、都道府県など）を更新します。
3.  **通常セッション読み込み時 (上記トリガー以外)**:
    a.  **有効期限チェック**: `token` オブジェクト内の `accessTokenExpires` (秒単位のタイムスタンプ) を確認します。
    b.  **リフレッシュ不要**: 現在時刻が有効期限の 60 秒前より手前であれば、トークンはまだ有効とみなし、現在の `token` オブジェクトをそのまま返します。
    c.  **リフレッシュ実行**: 現在時刻が有効期限の 60 秒前以降の場合、トークンリフレッシュが必要と判断します。
        i.  `token` オブジェクト内の `refreshToken` が存在するか確認します。なければ `error: "RefreshAccessTokenError"` を含む `token` を返します。
        ii. バックエンドの `/api/v1/auth/refresh-token` エンドポイントに `POST` リクエストを送信します。リクエストボディには `{ "refresh_token": token.refreshToken }` を JSON 形式で含めます。`credentials: 'include'` オプションにより、関連する Cookie（HttpOnly のリフレッシュトークン Cookie など）も送信されます。
        iii. **リフレッシュ成功**: バックエンドから新しい `access_token` と `expires_in` (および任意で新しい `refresh_token`) を含む JSON レスポンスが返ってきた場合、`token` オブジェクトの `accessToken`, `accessTokenExpires`, `refreshToken` (更新された場合) などを更新し、`error` フィールドをクリアして返します。
        iv. **リフレッシュ失敗**: バックエンドがエラーレスポンス（例: 500エラー、無効なリフレッシュトークン）を返した場合、`token` オブジェクトに `error: "RefreshAccessTokenError"` と、可能であればバックエンドからのエラー詳細 `errorDetail` を設定して返します。
        v.  **通信エラー等**: `fetch` 自体が失敗した場合も、`token` オブジェクトに `error: "RefreshAccessTokenError"` とエラーメッセージ `errorDetail` を設定して返します。

### 2.4 セッション作成 (`session` コールバック)

`jwt` コールバックの後に実行され、フロントエンドで利用可能なセッションオブジェクト (`session`) を作成します。

1.  `jwt` コールバックから渡された `token` オブジェクトを受け取ります。
2.  **エラーチェック**: `token` オブジェクトに `error` フィールドが存在する場合、そのエラー情報 (`error` および `errorDetail`) を `session` オブジェクトにコピーして返します。これにより、フロントエンドはトークンリフレッシュのエラーを検知できます。
3.  **セッション構築**: エラーがない場合、`token` オブジェクトの情報（`id`, `name`, `email`, `role`, `status`, `permissions`, `accessToken`, `accessTokenExpires` など）を `session.user` および `session.accessToken`, `session.expires` にマッピングして返します。この際、ロールの正規化などの処理も行われます。

### 2.5 ログアウト

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

| Method | Path                           | 説明                                          |
| ------ | ------------------------------ | --------------------------------------------- |
| `POST` | `/api/v1/auth/signup`          | 新規ユーザー登録                              |
| `POST` | `/api/v1/auth/login`           | ログイン (Form Data: `username`, `password`)    |
| `POST` | `/api/v1/auth/refresh-token`   | Access Token の再発行 (JSON: `refresh_token`) |
| `POST` | `/api/v1/auth/logout`          | ログアウト (Refresh Token失効)                  |
| `GET`  | `/api/v1/users/me`             | 認証済みユーザー情報取得                      |
| `POST` | `/api/v1/auth/change-password` | パスワード変更                                |
| `DELETE`| `/api/v1/auth/delete-account` | アカウント削除                                |

## 5. トークン管理

NextAuth.js では、`jwt` コールバックで管理される `token` オブジェクトが認証状態の中心となります。この `token` オブジェクトには以下の情報が含まれます。

*   **`accessToken`**: バックエンド API へのアクセスに使用される短命トークン。
*   **`refreshToken`**: アクセストークンのリフレッシュに使用される長命トークン。
*   **`accessTokenExpires`**: アクセストークンの有効期限 (秒単位のUNIXタイムスタンプ)。
*   **ユーザー情報**: ID, 名前, メール, ロール, ステータス, 権限など。
*   **エラー情報**: `error` (`RefreshAccessTokenError`), `errorDetail` (エラー詳細メッセージ)。

| 種類          | 保管場所                                                    | 期限 (例) | 特徴                                                                                                |
| ------------- | ----------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| **JWT Token (`token` オブジェクト)** | NextAuth.js によって Cookie に暗号化されて保存される        | セッション設定 (`maxAge`) | 内部的に Access/Refresh Token やユーザー情報を含む。`jwt` コールバックで更新・リフレッシュされる。         |
| **Access Token** | JWT Token (`token` オブジェクト) 内に保持                  | 15 分    | `session` コールバック経由で `session.accessToken` としてフロントエンドに公開され、API リクエストに使用される。 |
| **Refresh Token**| JWT Token (`token` オブジェクト) 内に保持。バックエンドも別途 Cookie (`HttpOnly` など) で管理する場合がある。 | 30 日    | `jwt` コールバック内で Access Token 再発行に使用される。                                               |

**フロントエンドでの利用 (`session` オブジェクト):**

`useSession()` や `getSession()` で取得できる `session` オブジェクトは、`session` コールバックによって `token` オブジェクトから生成されます。フロントエンドアプリケーションは、この `session` オブジェクトを通じて以下の情報を利用します。

*   `session.user`: ユーザー情報 (ID, 名前, ロール, 権限など)
*   `session.accessToken`: 現在有効なアクセストークン
*   `session.expires`: セッションの有効期限 (ISO 8601 形式)
*   `session.error`, `session.errorDetail`: トークンリフレッシュエラーが発生した場合の情報

## 6. セキュリティ考慮事項

-   **HTTPS**: 通信は常に HTTPS で暗号化します。
-   **JWT 署名アルゴリズム**: `RS256` (公開鍵/秘密鍵) または `HS256` (共通鍵) を使用します。`RS256` の方がより安全性が高いとされます。秘密鍵はバックエンドのみが保持します。
-   **Cookie 属性**: Refresh Token を保存する Cookie には `HttpOnly`, `Secure`, `SameSite=Strict` 属性を必ず設定し、XSS や CSRF 攻撃のリスクを軽減します。
-   **CSRF 対策**: NextAuth.js はデフォルトで CSRF 保護を提供しています（例: Double Submit Cookie パターン）。特にフォーム送信を伴う認証アクション (ログイン、サインアップ) では、NextAuth.js が生成する CSRF トークンが利用されます。Access Token を Cookie で管理する場合は、この保護が特に重要になります。
-   **レート制限**: ログイン、サインアップ、トークンリフレッシュのエンドポイントにはバックエンド (FastAPI) 側でレート制限を適用し、ブルートフォース攻撃を防ぎます。
-   **パスワードポリシー**: 強力なパスワードポリシー（長さ、文字種など）を強制します。
-   **メール認証**: サインアップ時にメールアドレスの所有確認を行うことを強く推奨します。
-   **依存関係の脆弱性**: `npm audit` や `pip check` などを定期的に実行し、使用するライブラリの脆弱性をチェックし、更新します。

## 7. 認可 (Authorization)

認証（Authentication）が「誰であるか」を確認するプロセスであるのに対し、認可（Authorization）は「何ができるか」を制御するプロセスです。

-   **基本方針**: ロールベースアクセス制御 (RBAC) を採用します。
    -   ユーザーには一つ以上の「ロール」（例: 管理者, 教員, 生徒）が割り当てられます。
    -   各ロールには特定の「権限」（例: ユーザー情報の編集, コンテンツの閲覧）が付与されます。
    -   ユーザーは、割り当てられたロールを通じて得られる権限の範囲内で操作を実行できます。
-   **実装**:
    -   **モデル**: `User`, `Role`, `Permission`, `RolePermission` (中間テーブル) モデルをデータベースで定義します。
    -   **バックエンド (FastAPI)**:
        -   API エンドポイントごとに必要な権限を定義します。
        -   FastAPI の `Depends` システムを利用して、リクエストごとにユーザーのロールと権限を検証する依存関係を作成します。
        -   例えば、`get_current_superuser` のような依存関係関数は、リクエスト元のユーザーが管理者ロール（および特定の管理者権限）を持っているかを確認します。
        -   より細かな制御が必要な場合は、特定の権限（例: `content_write`）を持つかを確認する依存関係を作成します。
    -   **フロントエンド (Next.js)**:
        -   ユーザーのロールに基づいて UI 要素（メニュー項目、ボタンなど）の表示/非表示を制御します。
        -   ただし、フロントエンドでの制御は補助的なものであり、**最終的なアクセス制御は必ずバックエンドで行う必要があります**。
-   **定義済み権限の例**:
    システムには以下のような権限が定義されています（必要に応じて追加・変更されます）。

    ```
    # 基本
    user_read: ユーザー情報の閲覧権限
    user_write: ユーザー情報の編集権限
    content_read: コンテンツの閲覧権限
    content_write: コンテンツの編集権限
    admin_access: 管理者画面へのアクセス権限

    # コミュニティ関連
    community_read: コミュニティ投稿を閲覧する
    community_post_create: コミュニティ投稿を作成する
    community_post_delete_own: 自分のコミュニティ投稿を削除する
    community_post_delete_any: （管理者向け）任意のコミュニティ投稿を削除する
    community_category_manage: （管理者向け）コミュニティカテゴリを管理する

    # チャット関連
    chat_session_read: チャットセッションを閲覧する
    chat_message_send: チャットメッセージを送信する

    # 志望校管理関連
    desired_school_manage_own: 自分の志望校リストを管理する
    desired_school_view_all: （管理者向け）全ユーザーの志望校リストを閲覧する

    # 志望理由書関連
    statement_manage_own: 自分の志望理由書を管理する
    statement_review_request: 志望理由書のレビューを依頼する
    statement_review_respond: （教員/管理者向け）志望理由書のレビューを行う
    statement_view_all: （管理者向け）全ユーザーの志望理由書を閲覧する
    ```
-   **権限の割り当て**:
    -   初期データ投入時 (`demo_data.py`) や管理者用 API を通じて、各ロールに必要な権限が割り当てられます。
    -   例えば、「生徒」ロールには `content_read`, `community_post_create` などが付与され、「管理者」ロールにはほぼ全ての権限が付与されます。

## 8. 現状分析まとめ

- フロントエンドは NextAuth.js の `CredentialsProvider` を利用し、メール/パスワードを FormData (`application/x-www-form-urlencoded`) で送信してログインを実装
- `jwt` コールバックでは初回トークン初期化、有効期限の 60 秒前で自動リフレッシュ、リフレッシュ失敗時に `error`/`errorDetail` を保持
- `session` コールバックが `token` 情報とエラー情報を含む `session` オブジェクトを生成し、フロントエンドで利用可能
- `fetchWithAuth.ts` では 401 エラー検知時に `refreshToken()` → リトライするキュー機構を導入し、複数同時リクエストを安定処理
- バックエンド (FastAPI) は `/api/v1/auth/` 系エンドポイントで JWT 発行・検証・リフレッシュ・失効リスト管理を実装
- 現状、DB の `users.grade` カラム未存在によりトークンリフレッシュ処理で 500 エラー発生中 → Alembic マイグレーションでカラム追加が必要
- 今後はログ出力と型定義のさらなる整備、フロント/バックエンド間のエラー検知・回復策を強化する
