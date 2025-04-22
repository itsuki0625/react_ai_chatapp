# SmartAO API エンドポイント一覧

Base URL: `/api/v1`

## 認証系 API
**ベースパス**: `/auth`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST    | `/auth/login` | OAuth2互換のログイン処理。アクセストークンを取得 |
| POST    | `/auth/logout` | ログアウト処理 |
| GET     | `/auth/me` | 現在のユーザー情報を取得 |
| GET     | `/auth/test-auth` | 認証テスト用エンドポイント |
| POST    | `/auth/signup` | 新規ユーザー登録 |
| GET     | `/auth/user-settings` | ユーザー設定の取得 |
| PUT     | `/auth/user-settings` | ユーザー設定の更新 |
| DELETE  | `/auth/delete-account` | アカウントの削除 |
| POST    | `/auth/change-password` | パスワード変更 |
| POST    | `/auth/verify-email` | メールアドレス検証 |
| POST    | `/auth/resend-verification` | 検証メールの再送信 |
| POST    | `/auth/refresh-token` | リフレッシュトークンによるアクセストークンの更新 |
| POST    | `/auth/forgot-password` | パスワードリセット要求 |
| POST    | `/auth/reset-password` | パスワードリセット実行 |
| POST    | `/auth/setup-2fa` | 二要素認証のセットアップ |
| POST    | `/auth/verify-2fa` | 二要素認証の検証 |
| DELETE  | `/auth/disable-2fa` | 二要素認証の無効化 |

## ユーザーロール管理 API
**ベースパス**: `/roles`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/roles` | 利用可能なロール一覧を取得 |
| GET     | `/roles/{role_id}` | 特定のロールの詳細と権限を取得 |
| POST    | `/roles` | 新しいロールを作成（管理者のみ） |
| PUT     | `/roles/{role_id}` | ロール情報を更新（管理者のみ） |
| DELETE  | `/roles/{role_id}` | ロールを削除（管理者のみ） |
| POST    | `/roles/assign` | ユーザーにロールを割り当て（管理者のみ） |

## チャット系 API
**ベースパス**: `/chat`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| OPTIONS | `/chat/stream` | ストリームエンドポイントのOPTIONSリクエスト |
| POST    | `/chat/stream` | ストリーミング形式でAIとチャット |
| DELETE  | `/chat/sessions` | チャットセッションの終了 |
| POST    | `/chat` | AIとのチャット（標準形式） |
| GET     | `/chat/sessions/archived` | アーカイブされたチャットセッションの取得 |
| GET     | `/chat/sessions/{session_id}/messages` | 特定のセッションのメッセージ履歴を取得 |
| PATCH   | `/chat/sessions/{session_id}/archive` | チャットセッションをアーカイブ |
| GET     | `/chat/sessions` | ユーザーのチャットセッション一覧を取得 |
| GET     | `/chat/{chat_id}/checklist` | 特定のチャットのチェックリスト評価を取得 |
| POST    | `/chat/self-analysis` | 自己分析AIとのチャットを開始 |
| GET     | `/chat/self-analysis/report` | 自己分析レポートを取得 |
| POST    | `/chat/admission` | 総合型選抜AIとのチャットを開始 |
| POST    | `/chat/study-support` | 汎用学習支援AIとのチャットを開始 |
| GET     | `/chat/analysis` | AIチャット対話の分析結果を取得 |

## 志望校管理 API
**ベースパス**: `/applications`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST    | `/applications` | 新しい志望校を登録 |
| GET     | `/applications` | ユーザーの志望校一覧を取得 |
| GET     | `/applications/{application_id}` | 特定の志望校情報を取得 |
| PUT     | `/applications/{application_id}` | 志望校情報を更新 |
| DELETE  | `/applications/{application_id}` | 志望校を削除 |
| POST    | `/applications/{application_id}/documents` | 書類を追加 |
| POST    | `/applications/{application_id}/schedules` | 日程を追加 |
| PUT     | `/applications/{application_id}/documents/{document_id}` | 書類情報を更新 |
| PUT     | `/applications/{application_id}/schedules/{schedule_id}` | 日程情報を更新 |
| DELETE  | `/applications/{application_id}/documents/{document_id}` | 書類を削除 |
| DELETE  | `/applications/{application_id}/schedules/{schedule_id}` | 日程を削除 |
| PUT     | `/applications/reorder` | 志望校の優先順位を更新 |
| GET     | `/applications/statistics` | 志望校関連の統計情報を取得 |
| GET     | `/applications/deadlines` | 近づく提出期限の一覧を取得 |

## 大学情報 API
**ベースパス**: `/universities`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/universities` | 大学一覧を取得 |
| GET     | `/universities/{university_id}` | 特定の大学の詳細情報を取得 |
| GET     | `/universities/{university_id}/departments` | 特定の大学の学部・学科一覧を取得 |
| GET     | `/universities/{university_id}/admission-methods` | 特定の大学の入試方式一覧を取得 |
| GET     | `/universities/search` | 大学を検索 |
| GET     | `/universities/recommended` | ユーザーの自己分析に基づいた推奨大学一覧を取得 |

## 入試情報 API
**ベースパス**: `/admission`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/admission/methods` | 入試方式一覧を取得 |
| GET     | `/admission/methods/{method_id}` | 特定の入試方式の詳細情報を取得 |
| GET     | `/admission/departments` | 学部・学科一覧を取得 |
| GET     | `/admission/departments/{department_id}` | 特定の学部・学科の詳細情報を取得 |
| GET     | `/admission/statistics` | 入試統計情報を取得 |
| GET     | `/admission/examples` | 過去の合格事例を取得 |

## 志望理由書 API
**ベースパス**: `/statements`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST    | `/statements` | 新しい志望理由書を作成 |
| GET     | `/statements` | ユーザーの志望理由書一覧を取得 |
| GET     | `/statements/{statement_id}` | 特定の志望理由書の詳細を取得 |
| PUT     | `/statements/{statement_id}` | 志望理由書を更新 |
| DELETE  | `/statements/{statement_id}` | 志望理由書を削除 |
| POST    | `/statements/{statement_id}/feedback/request` | 教師にフィードバックを依頼 |
| GET     | `/statements/{statement_id}/feedback` | フィードバック一覧を取得 |
| POST    | `/statements/{statement_id}/feedback` | フィードバックを提供（教師のみ） |
| POST    | `/statements/{statement_id}/ai-improve` | AIによる文章改善を実行 |
| GET     | `/statements/templates` | 志望理由書のテンプレート一覧を取得 |
| GET     | `/statements/examples` | 志望理由書の例文一覧を取得 |

## 学習コンテンツ API
**ベースパス**: `/contents`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/contents/faqs` | FAQ一覧を取得 |
| GET     | `/contents/faqs/{faq_id}` | 特定のFAQの詳細を取得 |
| GET     | `/contents` | コンテンツ一覧を取得 |
| GET     | `/contents/{content_id}` | 特定のコンテンツの詳細を取得 |
| GET     | `/contents/categories` | コンテンツカテゴリ一覧を取得 |
| GET     | `/contents/categories/{category_id}` | 特定のカテゴリのコンテンツ一覧を取得 |
| POST    | `/contents/{content_id}/view` | コンテンツの視聴記録を作成 |
| GET     | `/contents/{content_id}/reviews` | コンテンツのレビュー一覧を取得 |
| POST    | `/contents/{content_id}/reviews` | コンテンツのレビューを投稿 |
| GET     | `/contents/recommended` | ユーザーへのおすすめコンテンツを取得 |
| GET     | `/contents/history` | ユーザーのコンテンツ視聴履歴を取得 |

## 学習計画 API
**ベースパス**: `/study-plans`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST    | `/study-plans` | 新しい学習計画を作成 |
| GET     | `/study-plans` | ユーザーの学習計画一覧を取得 |
| GET     | `/study-plans/{plan_id}` | 特定の学習計画の詳細を取得 |
| PUT     | `/study-plans/{plan_id}` | 学習計画を更新 |
| DELETE  | `/study-plans/{plan_id}` | 学習計画を削除 |
| POST    | `/study-plans/{plan_id}/goals` | 学習目標を追加 |
| PUT     | `/study-plans/{plan_id}/goals/{goal_id}` | 学習目標を更新 |
| DELETE  | `/study-plans/{plan_id}/goals/{goal_id}` | 学習目標を削除 |
| GET     | `/study-plans/{plan_id}/progress` | 学習計画の進捗状況を取得 |
| POST    | `/study-plans/{plan_id}/progress` | 学習進捗を更新 |
| GET     | `/study-plans/templates` | 学習計画テンプレート一覧を取得 |
| POST    | `/study-plans/ai-generate` | AIによる学習計画の自動生成を実行 |

## クイズ・テスト API
**ベースパス**: `/quizzes`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST    | `/quizzes` | 新しいクイズを作成 |
| GET     | `/quizzes` | クイズ一覧を取得 |
| GET     | `/quizzes/{quiz_id}` | 特定のクイズの詳細を取得 |
| PUT     | `/quizzes/{quiz_id}` | クイズを更新 |
| DELETE  | `/quizzes/{quiz_id}` | クイズを削除 |
| POST    | `/quizzes/{quiz_id}/questions` | クイズに問題を追加 |
| PUT     | `/quizzes/{quiz_id}/questions/{question_id}` | クイズの問題を更新 |
| DELETE  | `/quizzes/{quiz_id}/questions/{question_id}` | クイズの問題を削除 |
| POST    | `/quizzes/{quiz_id}/attempt` | クイズを受験開始 |
| POST    | `/quizzes/{quiz_id}/submit` | クイズの回答を提出 |
| GET     | `/quizzes/{quiz_id}/results` | クイズの結果を取得 |
| GET     | `/quizzes/recommended` | 推奨クイズ一覧を取得 |
| GET     | `/quizzes/history` | ユーザーのクイズ受験履歴を取得 |
| GET     | `/quizzes/analysis` | ユーザーのクイズ結果分析を取得 |

## コミュニケーション API
**ベースパス**: `/communication`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/communication/messages` | メッセージ一覧を取得 |
| POST    | `/communication/messages` | 新しいメッセージを送信 |
| GET     | `/communication/messages/{message_id}` | 特定のメッセージの詳細を取得 |
| DELETE  | `/communication/messages/{message_id}` | メッセージを削除 |
| GET     | `/communication/threads` | スレッド一覧を取得 |
| POST    | `/communication/threads` | 新しいスレッドを作成 |
| GET     | `/communication/threads/{thread_id}` | 特定のスレッドの詳細とメッセージを取得 |
| POST    | `/communication/threads/{thread_id}/messages` | スレッドにメッセージを追加 |
| GET     | `/communication/forums` | フォーラム一覧を取得 |
| POST    | `/communication/forums` | 新しいフォーラムを作成 |
| GET     | `/communication/forums/{forum_id}` | 特定のフォーラムの詳細を取得 |
| POST    | `/communication/forums/{forum_id}/topics` | フォーラムにトピックを追加 |
| GET     | `/communication/forums/{forum_id}/topics/{topic_id}` | 特定のトピックとその返信を取得 |
| POST    | `/communication/forums/{forum_id}/topics/{topic_id}/replies` | トピックに返信を追加 |

## サブスクリプション API
**ベースパス**: `/subscriptions`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/subscriptions` | ユーザーのサブスクリプション情報を取得 |
| POST    | `/subscriptions` | 新しいサブスクリプションを開始 |
| GET     | `/subscriptions/plans` | サブスクリプションプラン一覧を取得 |
| DELETE  | `/subscriptions/{subscription_id}` | サブスクリプションをキャンセル |
| GET     | `/subscriptions/payment-history` | 支払い履歴を取得 |
| POST    | `/subscriptions/apply-coupon` | クーポンコードを適用 |
| GET     | `/subscriptions/invoice` | 最新の請求書を取得 |
| PUT     | `/subscriptions/update-payment` | 支払い方法を更新 |

## 通知 API
**ベースパス**: `/notifications`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/notifications` | ユーザーの通知一覧を取得 |
| PUT     | `/notifications/{notification_id}/read` | 通知を既読にマーク |
| PUT     | `/notifications/read-all` | すべての通知を既読にマーク |
| DELETE  | `/notifications/{notification_id}` | 通知を削除 |
| GET     | `/notifications/settings` | 通知設定を取得 |
| PUT     | `/notifications/settings` | 通知設定を更新 |
| POST    | `/notifications/test` | テスト通知を送信 |

## ダッシュボード API
**ベースパス**: `/dashboard`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/dashboard/student` | 学生向けダッシュボード情報を取得 |
| GET     | `/dashboard/teacher` | 教師向けダッシュボード情報を取得 |
| GET     | `/dashboard/admin` | 管理者向けダッシュボード情報を取得 |
| GET     | `/dashboard/progress` | 学習進捗情報を取得 |
| GET     | `/dashboard/events` | 予定イベント情報を取得 |
| GET     | `/dashboard/applications` | 志望校状況の概要を取得 |
| GET     | `/dashboard/recommendations` | 推奨コンテンツとアクションの概要を取得 |
| GET     | `/dashboard/ai-analysis` | AIチャット分析の概要を取得 |
| GET     | `/dashboard/statistics` | システム利用統計を取得（管理者のみ） |

## データ分析・レポート API
**ベースパス**: `/analytics`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/analytics/study-time` | 学習時間分析を取得 |
| GET     | `/analytics/content-usage` | コンテンツ利用傾向を取得 |
| GET     | `/analytics/strengths-weaknesses` | 強み・弱み分析を取得 |
| GET     | `/analytics/recommended-paths` | 推奨学習パスを取得 |
| GET     | `/analytics/self-analysis` | 自己分析レポートを取得 |
| GET     | `/analytics/user-engagement` | ユーザーエンゲージメント分析を取得（管理者のみ） |
| GET     | `/analytics/content-popularity` | コンテンツ人気度分析を取得（管理者のみ） |
| GET     | `/analytics/ai-chat-trends` | AIチャット利用傾向分析を取得（管理者のみ） |
| GET     | `/analytics/custom-report` | カスタムレポートを生成（管理者のみ） |
| GET     | `/analytics/export` | 分析データをエクスポート |

## 管理者向け API
**ベースパス**: `/admin`

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET     | `/admin/users` | ユーザー一覧を取得（管理者のみ） |
| GET     | `/admin/users/{user_id}` | 特定ユーザーの詳細情報を取得（管理者のみ） |
| PUT     | `/admin/users/{user_id}` | ユーザー情報を更新（管理者のみ） |
| DELETE  | `/admin/users/{user_id}` | ユーザーを削除（管理者のみ） |
| GET     | `/admin/audit-logs` | 監査ログを取得（管理者のみ） |
| GET     | `/admin/system-status` | システムステータスを取得（管理者のみ） |
| POST    | `/admin/announcements` | システムアナウンスを作成（管理者のみ） |
| GET     | `/admin/backup` | データバックアップを実行（管理者のみ） |
| POST    | `/admin/coupons` | キャンペーンコードを作成（管理者のみ） |
| GET     | `/admin/coupons` | キャンペーンコード一覧を取得（管理者のみ） |
| PUT     | `/admin/content-visibility` | コンテンツの公開状態を設定（管理者のみ） |
| GET     | `/admin/system-logs` | システムログを取得（管理者のみ） |
