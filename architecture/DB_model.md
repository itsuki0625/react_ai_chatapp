# バックエンドシステムのデータベースモデル（第3正規形）

このドキュメントでは、第3正規形に従ってリファクタリングしたバックエンドシステムのデータベースモデルの詳細を説明します。システムはSQLAlchemyを使用してORMマッピングを行い、PostgreSQLデータベースに接続しています。

## 第3正規形について

第3正規形の条件は以下の通りです：

1. 第2正規形のすべての条件を満たしている
2. すべての非キー属性が、非キー属性に対して推移的関数従属性を持たない
3. つまり、非キー属性が他の非キー属性を経由して間接的に主キーに依存することがないようにする

推移的関数従属性がある場合は、新しいテーブルに分割して除去します。

## 基本構造

すべてのモデルは共通の`Base`クラスを継承しており、多くのモデルは`TimestampMixin`も継承して作成日時と更新日時を自動的に記録しています。

```python
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

ほとんどのテーブルは、主キーとしてUUIDを使用しています。

## ユーザー関連テーブル

### Role（ロール）
- `id`: UUID、主キー
- `name`: 名称（必須）
- `description`: 説明
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### Permission（権限）
- `id`: UUID、主キー
- `name`: 権限名（必須、一意）
- `description`: 説明
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### RolePermission（ロール権限）
- `id`: UUID、主キー
- `role_id`: ロールID（外部キー、必須）
- `permission_id`: 権限ID（外部キー、必須）
- `is_granted`: 付与状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### User（ユーザー）
- `id`: UUID、主キー
- `email`: メールアドレス（必須、一意）
- `hashed_password`: ハッシュ化されたパスワード（必須）
- `full_name`: 氏名（必須）
- `school_id`: 所属学校ID（外部キー）
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserProfile（ユーザープロフィール）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須、一意）
- `grade`: 学年
- `class_number`: クラス
- `student_number`: 出席番号
- `profile_image_url`: プロフィール画像URL
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserLoginInfo（ユーザーログイン情報）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須、一意）
- `last_login_at`: 最終ログイン日時
- `failed_login_attempts`: ログイン失敗回数（整数、デフォルト: 0）
- `last_failed_login_at`: 最終ログイン失敗日時
- `locked_until`: アカウントロック解除日時
- `account_lock_reason`: アカウントロック理由（enum: AccountLockReason）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserEmailVerification（ユーザーメール検証）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須、一意）
- `email_verified`: メール検証済みフラグ（ブール値、デフォルト: false）
- `email_verification_token`: メール検証用トークン
- `email_verification_sent_at`: メール検証送信日時
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserTwoFactorAuth（ユーザー2要素認証）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須、一意）
- `enabled`: 有効フラグ（ブール値、デフォルト: false）
- `secret`: 2要素認証シークレット
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserRole（ユーザーロール）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `role_id`: ロールID（外部キー、必須）
- `is_primary`: 主要ロールかどうか（ブール値、デフォルト: false）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserRoleAssignment（ユーザーロール割り当て）
- `id`: UUID、主キー
- `user_role_id`: ユーザーロールID（外部キー、必須、一意）
- `assigned_at`: 割り当て日時（デフォルト: 現在日時）
- `assigned_by`: 割り当てたユーザーID（外部キー）
- `created_at`: 作成日時（デフォルト: 現在日時）

### UserRoleMetaData（ユーザーロールメタデータ）
- `id`: UUID、主キー
- `user_role_id`: ユーザーロールID（外部キー、必須）
- `key`: メタデータキー（必須）
- `value`: メタデータ値（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

### TokenBlacklist（トークンブラックリスト）
- `id`: UUID、主キー
- `token_jti`: トークンJTI（JWT ID、必須、一意）
- `user_id`: ユーザーID（外部キー、必須）
- `expires_at`: 有効期限（必須）
- `reason`: 失効理由（enum: TokenBlacklistReason、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

### UserContactInfo（ユーザー連絡先情報）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `contact_type`: 連絡先タイプ（'phone', 'email', 'address'等）
- `contact_value`: 連絡先値
- `is_primary`: 主要連絡先フラグ（ブール値、デフォルト: false）
- `verified`: 検証済みフラグ（ブール値、デフォルト: false）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## 学校・大学関連テーブル

### School（高校）
- `id`: UUID、主キー
- `name`: 学校名（必須）
- `school_code`: 学校コード（必須、一意）
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### SchoolDetails（高校詳細情報）
- `id`: UUID、主キー
- `school_id`: 学校ID（外部キー、必須、一意）
- `address`: 住所
- `prefecture`: 都道府県
- `city`: 市区町村
- `zip_code`: 郵便番号
- `principal_name`: 校長名
- `website_url`: ウェブサイトURL
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### SchoolContact（学校連絡先）
- `id`: UUID、主キー
- `school_id`: 学校ID（外部キー、必須）
- `contact_type`: 連絡先タイプ（'phone', 'email', 'fax'等）
- `contact_value`: 連絡先値
- `is_primary`: 主要連絡先フラグ（ブール値、デフォルト: false）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### University（大学）
- `id`: UUID、主キー
- `name`: 大学名（必須）
- `university_code`: 大学コード（必須、一意）
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UniversityDetails（大学詳細情報）
- `id`: UUID、主キー
- `university_id`: 大学ID（外部キー、必須、一意）
- `address`: 住所
- `prefecture`: 都道府県
- `city`: 市区町村
- `zip_code`: 郵便番号
- `president_name`: 学長名
- `website_url`: ウェブサイトURL
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UniversityContact（大学連絡先）
- `id`: UUID、主キー
- `university_id`: 大学ID（外部キー、必須）
- `contact_type`: 連絡先タイプ（'phone', 'email', 'fax'等）
- `contact_value`: 連絡先値
- `is_primary`: 主要連絡先フラグ（ブール値、デフォルト: false）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### Department（学部・学科）
- `id`: UUID、主キー
- `university_id`: 大学ID（外部キー、必須）
- `name`: 学部・学科名（必須）
- `department_code`: 学部・学科コード（必須、一意）
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### DepartmentDetails（学部・学科詳細情報）
- `id`: UUID、主キー
- `department_id`: 学部・学科ID（外部キー、必須、一意）
- `description`: 説明
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### AdmissionMethod（入試方式）
- `id`: UUID、主キー
- `name`: 入試方式名（必須）
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### AdmissionMethodDetails（入試方式詳細情報）
- `id`: UUID、主キー
- `admission_method_id`: 入試方式ID（外部キー、必須、一意）
- `description`: 説明
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## 志望校関連テーブル

### DesiredSchool（志望校）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `university_id`: 大学ID（外部キー、必須）
- `preference_order`: 志望順位（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### DesiredDepartment（志望学部・学科）
- `id`: UUID、主キー
- `desired_school_id`: 志望校ID（外部キー、必須）
- `department_id`: 学部・学科ID（外部キー、必須）
- `admission_method_id`: 入試方式ID（外部キー、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### Document（提出書類）
- `id`: UUID、主キー
- `desired_department_id`: 志望学部・学科ID（外部キー、必須）
- `name`: 書類名（必須）
- `status`: ステータス（enum: DocumentStatus、必須）
- `deadline`: 提出期限
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### DocumentSubmission（書類提出）
- `id`: UUID、主キー
- `document_id`: 書類ID（外部キー、必須、一意）
- `submitted_at`: 提出日時
- `submitted_by`: 提出者ID（外部キー、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ScheduleEvent（スケジュールイベント）
- `id`: UUID、主キー
- `desired_department_id`: 志望学部・学科ID（外部キー、必須）
- `event_name`: イベント名（必須）
- `event_date`: 日付（必須）
- `event_type`: タイプ（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### EventCompletion（イベント完了）
- `id`: UUID、主キー
- `event_id`: イベントID（外部キー、必須、一意）
- `completed`: 完了状態（ブール値、デフォルト: false）
- `completed_at`: 完了日時
- `completed_by`: 完了者ID（外部キー）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### PersonalStatement（志望理由書）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `desired_department_id`: 志望学部・学科ID（外部キー、必須）
- `content`: 内容（必須）
- `status`: ステータス（enum: PersonalStatementStatus、必須）
- `submission_deadline`: 提出期限
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### PersonalStatementSubmission（志望理由書提出）
- `id`: UUID、主キー
- `personal_statement_id`: 志望理由書ID（外部キー、必須、一意）
- `submitted_at`: 提出日時
- `submitted_by`: 提出者ID（外部キー、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### Feedback（フィードバック）
- `id`: UUID、主キー
- `personal_statement_id`: 志望理由書ID（外部キー、必須）
- `feedback_user_id`: フィードバック提供ユーザーID（外部キー、必須）
- `content`: フィードバック内容（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## チャット関連テーブル

### ChatSession（チャットセッション）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `title`: タイトル（必須）
- `session_type`: セッションタイプ（enum: SessionType、必須）
- `status`: ステータス（enum: SessionStatus、必須）
- `last_message_at`: 最終メッセージ日時
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ChatSessionMetaData（チャットセッションメタデータ）
- `id`: UUID、主キー
- `session_id`: セッションID（外部キー、必須）
- `key`: メタデータキー（必須）
- `value`: メタデータ値（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ChatMessage（チャットメッセージ）
- `id`: UUID、主キー
- `session_id`: セッションID（外部キー、必須）
- `sender_id`: 送信者ID（外部キー、必須）
- `sender_type`: 送信者タイプ（enum: SenderType、必須）
- `content`: 内容（必須）
- `message_type`: メッセージタイプ（enum: MessageType、必須）
- `is_read`: 既読状態（ブール値、デフォルト: false）
- `read_at`: 既読日時
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ChatMessageMetaData（チャットメッセージメタデータ）
- `id`: UUID、主キー
- `message_id`: メッセージID（外部キー、必須）
- `key`: メタデータキー（必須）
- `value`: メタデータ値（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ChatAttachment（添付ファイル）
- `id`: UUID、主キー
- `message_id`: メッセージID（外部キー、必須）
- `file_url`: ファイルURL（必須）
- `file_type`: ファイルタイプ（必須）
- `file_size`: ファイルサイズ（バイト単位、必須）
- `file_name`: ファイル名（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ChecklistEvaluation（チェックリスト評価）
- `id`: UUID、主キー
- `session_id`: セッションID（外部キー、必須）
- `checklist_item`: チェック項目（必須）
- `is_completed`: 完了フラグ（ブール値、デフォルト: false）
- `score`: 評価スコア
- `evaluator_id`: 評価者ID（外部キー）
- `evaluated_at`: 評価日時
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## サブスクリプション関連テーブル

### Subscription（サブスクリプション）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `stripe_customer_id`: Stripe顧客ID
- `stripe_subscription_id`: Stripeサブスクリプション
- `status`: ステータス（'active', 'past_due', 'canceled', 'unpaid', 'trialing'、必須）
- `plan_id`: プランID（外部キー、必須）
- `current_period_start`: 現在の期間開始日
- `current_period_end`: 現在の期間終了日
- `cancel_at`: キャンセル予定日
- `canceled_at`: キャンセル日
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `campaign_code_id`: キャンペーンコードID（外部キー）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### SubscriptionPlan（サブスクリプションプラン）
- `id`: UUID、主キー
- `name`: プラン名（必須、一意）
- `description`: プラン説明
- `price_id`: Stripe価格ID（必須）
- `amount`: 金額（必須）
- `currency`: 通貨（デフォルト: 'jpy'、必須）
- `interval`: 請求間隔（'month', 'year'、必須）
- `interval_count`: 間隔数（必須、デフォルト: 1）
- `trial_days`: 無料トライアル日数
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `features`: 機能説明（JSONBフィールド）
- `metadata`: メタデータ（JSONBフィールド）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### PaymentHistory（支払い履歴）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `subscription_id`: サブスクリプションID（外部キー）
- `stripe_payment_intent_id`: Stripe支払いインテントID
- `stripe_invoice_id`: Stripe請求書ID
- `amount`: 金額（必須）
- `currency`: 通貨（デフォルト: 'jpy'、必須）
- `status`: ステータス（'succeeded', 'pending', 'failed'、必須）
- `payment_method_id`: 支払い方法ID（外部キー）
- `payment_date`: 支払い日（デフォルト: 現在日時）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### PaymentMethod（支払い方法）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `stripe_payment_method_id`: Stripe支払い方法ID（必須）
- `method_type`: 支払い方法タイプ（'card', 'bank_transfer', 'convenience_store'等、必須）
- `is_default`: デフォルト支払い方法かどうか（ブール値、デフォルト: false）
- `last_four`: カード下4桁または識別子
- `expiry_month`: 有効期限月
- `expiry_year`: 有効期限年
- `brand`: カードブランド
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### CampaignCode（キャンペーンコード）
- `id`: UUID、主キー
- `code`: コード（必須、一意）
- `description`: 説明
- `discount_type_id`: 割引タイプID（外部キー、必須）
- `discount_value`: 割引額または割引率（必須）
- `max_uses`: 最大使用回数
- `used_count`: 使用回数（整数、デフォルト: 0）
- `valid_from`: 有効期間開始
- `valid_until`: 有効期間終了
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_by`: 作成者ID（外部キー）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### DiscountType（割引タイプ）
- `id`: UUID、主キー
- `name`: 割引タイプ名（'percentage', 'fixed'等、必須、一意）
- `description`: 説明
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### CampaignCodeRedemption（キャンペーンコード使用履歴）
- `id`: UUID、主キー
- `campaign_code_id`: キャンペーンコードID（外部キー、必須）
- `user_id`: 使用ユーザーID（外部キー、必須）
- `subscription_id`: 適用サブスクリプションID（外部キー、必須）
- `redeemed_at`: 使用日時（必須、デフォルト: 現在日時）
- `discount_applied`: 適用された割引額（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### Invoice（請求書）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `subscription_id`: サブスクリプションID（外部キー）
- `stripe_invoice_id`: Stripe請求書ID
- `amount`: 金額（必須）
- `currency`: 通貨（デフォルト: 'jpy'、必須）
- `status`: ステータス（'draft', 'open', 'paid', 'uncollectible', 'void'、必須）
- `invoice_date`: 請求日（必須）
- `due_date`: 支払期限日
- `paid_at`: 支払完了日
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### InvoiceItem（請求書項目）
- `id`: UUID、主キー
- `invoice_id`: 請求書ID（外部キー、必須）
- `description`: 項目説明（必須）
- `amount`: 金額（必須）
- `quantity`: 数量（必須、デフォルト: 1）
- `subscription_plan_id`: サブスクリプションプランID（外部キー）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## コンテンツ関連テーブル

### Content（コンテンツ）
- `id`: UUID、主キー
- `title`: タイトル（必須）
- `description`: 説明
- `url`: URL（必須）
- `content_type`: コンテンツタイプ（enum: ContentType、必須）
- `thumbnail_url`: サムネイルURL
- `duration`: 再生時間（秒）
- `is_premium`: プレミアムコンテンツかどうか（ブール値、デフォルト: false）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ContentTag（コンテンツタグ）
- `id`: UUID、主キー
- `content_id`: コンテンツID（外部キー、必須）
- `tag_name`: タグ名（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

### ContentCategory（コンテンツカテゴリ）
- `id`: UUID、主キー
- `name`: カテゴリ名（必須）
- `description`: 説明
- `parent_id`: 親カテゴリID（外部キー、自己参照、オプション）
- `display_order`: 表示順序
- `icon_url`: アイコンURL
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ContentCategoryRelation（コンテンツカテゴリ関連付け）
- `id`: UUID、主キー
- `content_id`: コンテンツID（外部キー、必須）
- `category_id`: カテゴリID（外部キー、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

### ContentViewHistory（コンテンツ視聴履歴）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `content_id`: コンテンツID（外部キー、必須）
- `viewed_at`: 視聴日時（デフォルト: 現在日時）
- `progress`: 視聴進捗（秒数または位置、0～100%）
- `completed`: 視聴完了フラグ（ブール値、デフォルト: false）
- `completed_at`: 完了日時
- `duration`: セッション継続時間（秒）
- `device_type`: 視聴デバイスタイプ（enum: DeviceType）
- `ip_address`: IPアドレス
- `user_agent`: ユーザーエージェント
- `created_at`: 作成日時（デフォルト: 現在日時）

### ContentViewHistoryMetaData（コンテンツ視聴履歴メタデータ）
- `id`: UUID、主キー
- `view_history_id`: 視聴履歴ID（外部キー、必須）
- `key`: メタデータキー（必須）
- `value`: メタデータ値（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

### ContentRating（コンテンツ評価）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `content_id`: コンテンツID（外部キー、必須）
- `rating`: 評価（1～5、必須）
- `comment`: コメント
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## 学習進捗関連テーブル

### StudyPlan（学習計画）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `title`: タイトル（必須）
- `description`: 説明
- `start_date`: 開始日時
- `end_date`: 終了日時
- `goal`: 目標
- `status`: ステータス（enum: StudyPlanStatus、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### StudyPlanItem（学習計画項目）
- `id`: UUID、主キー
- `study_plan_id`: 学習計画ID（外部キー、必須）
- `content_id`: コンテンツID（外部キー、オプション）
- `title`: タイトル（必須）
- `description`: 説明
- `scheduled_date`: 予定日時
- `duration_minutes`: 予定時間（分）
- `completed`: 完了フラグ（ブール値、デフォルト: false）
- `completed_at`: 完了日時
- `display_order`: 表示順序
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### LearningPath（学習パス）
- `id`: UUID、主キー
- `title`: タイトル（必須）
- `description`: 説明
- `difficulty_level`: 難易度（enum: DifficultyLevel、必須）
- `estimated_hours`: 想定学習時間
- `created_by`: 作成者ID（外部キー、必須）
- `is_public`: 公開フラグ（ブール値、デフォルト: true）
- `is_featured`: おすすめフラグ（ブール値、デフォルト: false）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### LearningPathPrerequisite（学習パス前提条件）
- `id`: UUID、主キー
- `learning_path_id`: 学習パスID（外部キー、必須）
- `prerequisite`: 前提条件（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

### LearningPathAudience（学習パス対象者）
- `id`: UUID、主キー
- `learning_path_id`: 学習パスID（外部キー、必須）
- `target_audience`: 対象ユーザー層（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

### LearningPathItem（学習パス項目）
- `id`: UUID、主キー
- `learning_path_id`: 学習パスID（外部キー、必須）
- `content_id`: コンテンツID（外部キー、オプション）
- `quiz_id`: クイズID（外部キー、オプション）
- `title`: タイトル（必須）
- `description`: 説明
- `sequence_number`: 順序番号（必須）
- `is_required`: 必須フラグ（ブール値、デフォルト: true）
- `estimated_minutes`: 想定所要時間（分）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserLearningPath（ユーザー学習パス）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `learning_path_id`: 学習パスID（外部キー、必須）
- `start_date`: 開始日時
- `completed`: 完了フラグ（ブール値、デフォルト: false）
- `completed_at`: 完了日時
- `progress_percentage`: 進捗率（0-100）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserLearningPathItem（ユーザー学習パス項目）
- `id`: UUID、主キー
- `user_learning_path_id`: ユーザー学習パスID（外部キー、必須）
- `learning_path_item_id`: 学習パス項目ID（外部キー、必須）
- `status`: ステータス（enum: LearningItemStatus、必須）
- `started_at`: 開始日時
- `completed_at`: 完了日時
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserLearningPathNote（ユーザー学習パス項目ノート）
- `id`: UUID、主キー
- `user_learning_path_item_id`: ユーザー学習パス項目ID（外部キー、必須）
- `note`: ノート内容（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## クイズ・テスト関連テーブル

### Quiz（クイズ）
- `id`: UUID、主キー
- `title`: タイトル（必須）
- `description`: 説明
- `difficulty_level`: 難易度（enum: DifficultyLevel、必須）
- `time_limit_minutes`: 制限時間（分）
- `passing_percentage`: 合格点（0-100）
- `is_randomized`: ランダム出題フラグ（ブール値、デフォルト: false）
- `max_attempts`: 最大挑戦回数
- `created_by`: 作成者ID（外部キー、必須）
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### QuizQuestion（クイズ問題）
- `id`: UUID、主キー
- `quiz_id`: クイズID（外部キー、必須）
- `question_text`: 問題テキスト（必須）
- `question_type`: 問題タイプ（enum: QuestionType、必須）
- `explanation`: 解説
- `points`: 配点（必須、デフォルト: 1）
- `sequence_number`: 順序番号（必須）
- `media_url`: メディアURL
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### QuizAnswer（クイズ回答選択肢）
- `id`: UUID、主キー
- `question_id`: 問題ID（外部キー、必須）
- `answer_text`: 回答テキスト（必須）
- `is_correct`: 正解フラグ（ブール値、必須）
- `explanation`: 解説
- `sequence_number`: 順序番号（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserQuizAttempt（ユーザークイズ挑戦）
- `id`: UUID、主キー
- `user_id`: ユーザーID（外部キー、必須）
- `quiz_id`: クイズID（外部キー、必須）
- `start_time`: 開始時間（必須）
- `end_time`: 終了時間
- `score`: スコア
- `percentage`: 正答率（0-100）
- `passed`: 合格フラグ（ブール値）
- `attempt_number`: 挑戦回数（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### UserQuizAnswer（ユーザークイズ回答）
- `id`: UUID、主キー
- `attempt_id`: 挑戦ID（外部キー、必須）
- `question_id`: 問題ID（外部キー、必須）
- `answer_id`: 回答ID（外部キー、オプション）
- `user_text_answer`: ユーザーテキスト回答
- `is_correct`: 正解判定（ブール値、必須）
- `points_earned`: 獲得ポイント（必須、デフォルト: 0）
- `time_spent_seconds`: 回答時間（秒）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

## フォーラム関連テーブル

### ForumCategory（フォーラムカテゴリ）
- `id`: UUID、主キー
- `name`: カテゴリ名（必須）
- `description`: カテゴリ説明
- `parent_id`: 親カテゴリID（外部キー、オプション）
- `display_order`: 表示順（整数、デフォルト: 0）
- `icon`: アイコン参照パス
- `is_active`: アクティブ状態（ブール値、デフォルト: true）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ForumTopic（フォーラムトピック）
- `id`: UUID、主キー
- `title`: トピックタイトル（必須）
- `content`: トピック内容（必須）
- `category_id`: カテゴリID（外部キー、必須）
- `user_id`: 作成者ユーザーID（外部キー、必須）
- `is_pinned`: ピン留めフラグ（ブール値、デフォルト: false）
- `is_locked`: ロックフラグ（ブール値、デフォルト: false）
- `view_count`: 閲覧数（整数、デフォルト: 0）
- `last_activity_at`: 最終アクティビティ日時（デフォルト: 現在日時）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ForumPost（フォーラム投稿）
- `id`: UUID、主キー
- `topic_id`: トピックID（外部キー、必須）
- `user_id`: 投稿者ID（外部キー、必須）
- `content`: 投稿内容（必須）
- `is_solution`: 解決策としてマークされているか（ブール値、デフォルト: false）
- `is_edited`: 編集済みか（ブール値、デフォルト: false）
- `edited_at`: 編集日時
- `is_hidden`: 非表示状態（ブール値、デフォルト: false）
- `parent_post_id`: 親投稿ID（外部キー、自己参照、オプション）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ForumPostReaction（フォーラム投稿リアクション）
- `id`: UUID、主キー
- `post_id`: 投稿ID（外部キー、必須）
- `user_id`: ユーザーID（外部キー、必須）
- `reaction_type`: リアクションタイプ（enum: ReactionType、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ForumPostAttachment（フォーラム投稿添付ファイル）
- `id`: UUID、主キー
- `post_id`: 投稿ID（外部キー、必須）
- `file_name`: ファイル名（必須）
- `file_path`: ファイルパス（必須）
- `file_size`: ファイルサイズ（バイト単位）
- `file_type`: ファイルタイプ（MIME）
- `created_at`: 作成日時（デフォルト: 現在日時）

### ForumTopicView（フォーラムトピック閲覧）
- `id`: UUID、主キー
- `topic_id`: トピックID（外部キー、必須）
- `user_id`: ユーザーID（外部キー、必須）
- `viewed_at`: 閲覧日時（デフォルト: 現在日時）
- `ip_address`: IPアドレス
- `user_agent`: ユーザーエージェント

### ForumTopicSubscription（フォーラムトピック購読）
- `id`: UUID、主キー
- `topic_id`: トピックID（外部キー、必須）
- `user_id`: ユーザーID（外部キー、必須）
- `notification_level`: 通知レベル（enum: NotificationLevel、必須）
- `created_at`: 作成日時（デフォルト: 現在日時）
- `updated_at`: 更新日時（デフォルト: 現在日時、更新時自動更新）

### ForumTopicTag（フォーラムトピックタグ）
- `id`: UUID、主キー
- `topic_id`: トピックID（外部キー、必須）
- `tag_name`: タグ名（必須）
- `created_at`: 作成日時（デフォルト: 現在日時）

## リレーションシップ（主要な関連）

以下に主要なテーブル間の関連を示します。すべての関連は外部キー制約によって保証されます。

### ユーザーと認証関連
- User ⟷ Role: UserRoleテーブルを介した多対多関連
- User ⟷ School: ユーザーは1つの学校に所属（多対1関連）
- User ⟷ Permission: UserPermissionテーブルを介した多対多関連
- User ⟷ DesiredSchool: ユーザーは複数の志望校を持つ（1対多関連）
- User ⟷ TokenBlacklist: ユーザーは複数の無効化されたトークンを持つ（1対多関連）
- User ⟷ LoginHistory: ユーザーは複数のログイン履歴を持つ（1対多関連）
- User ⟷ UserVerification: ユーザーは複数の検証記録を持つ（1対多関連）
- User ⟷ TwoFactorAuth: ユーザーは1つの2FA設定を持つ（1対1関連）
- Role ⟷ RolePermission: ロールは複数の権限関連を持つ（1対多関連）
- RolePermission ⟷ Permission: 各ロール権限関連は1つの権限を参照（多対1関連）

### コンテンツと学習関連
- User ⟷ ContentViewHistory: ユーザーは複数のコンテンツ閲覧履歴を持つ（1対多関連）
- User ⟷ ContentRating: ユーザーは複数のコンテンツ評価を行う（1対多関連）
- User ⟷ ContentBookmark: ユーザーは複数のコンテンツをブックマークできる（1対多関連）
- User ⟷ ContentNote: ユーザーは複数のコンテンツノートを作成できる（1対多関連）
- Content ⟷ ContentCategory: ContentCategoryRelationを介した多対多関連
- Content ⟷ ContentTag: コンテンツは複数のタグを持つ（1対多関連）
- Content ⟷ ContentAttachment: コンテンツは複数の添付ファイルを持つ（1対多関連）
- Content ⟷ ContentViewHistory: コンテンツは複数のユーザーに閲覧される（1対多関連）
- Content ⟷ ContentRating: コンテンツは複数のユーザーに評価される（1対多関連）
- ContentCategory ⟷ ContentCategory: カテゴリーは階層構造を持つ（自己参照関連）
- LearningPath ⟷ LearningPathItem: 学習パスは複数の学習アイテムを含む（1対多関連）
- LearningPathItem ⟷ Content: 学習アイテムは1つのコンテンツを参照（多対1関連）
- Quiz ⟷ QuizQuestion: クイズは複数の質問を含む（1対多関連）
- QuizQuestion ⟷ QuizAnswer: 質問は複数の回答選択肢を持つ（1対多関連）
- User ⟷ QuizAttempt: ユーザーは複数のクイズ挑戦を行う（1対多関連）
- QuizAttempt ⟷ QuizAttemptAnswer: クイズ挑戦は複数の回答を含む（1対多関連）

### 学習計画と目標関連
- User ⟷ StudyPlan: ユーザーは複数の学習計画を持つ（1対多関連）
- User ⟷ StudyGoal: ユーザーは複数の学習目標を持つ（1対多関連）
- StudyPlan ⟷ StudyGoal: 学習計画と学習目標の多対多関連（StudyPlanGoalテーブルを介して）
- StudyPlan ⟷ StudyProgress: 学習計画は複数の進捗記録を持つ（1対多関連）
- StudyPlanTemplate ⟷ StudyPlan: テンプレートから複数の学習計画が作成される（1対多関連）

### 個人情報と志望理由書関連
- User ⟷ PersonalStatement: ユーザーは複数の志望理由書を持つ（1対多関連）
- PersonalStatement ⟷ PersonalStatementVersion: 志望理由書は複数のバージョンを持つ（1対多関連）
- PersonalStatement ⟷ Feedback: 志望理由書は複数のフィードバックを受ける（1対多関連）
- User ⟷ Feedback: ユーザーは複数のフィードバックを行う（1対多関連）

### 通信とメッセージング関連
- User ⟷ Conversation: 
  - ユーザーは複数の会話に参加できる（user1またはuser2として）
  - 各会話には2人のユーザーが関与する
- User ⟷ Message:
  - ユーザーは複数のメッセージを送信できる
  - 各メッセージには1人の送信者がいる
- Conversation ⟷ Message:
  - 会話は複数のメッセージを含む（1対多関連）
  - 各メッセージは1つの会話に属する

### ChatGPT関連
- User ⟷ ChatSession: ユーザーは複数のチャットセッションを持つ（1対多関連）
- ChatSession ⟷ ChatMessage: チャットセッションは複数のメッセージを含む（1対多関連）
- ChatMessage ⟷ ChatAttachment: チャットメッセージは複数の添付ファイルを持つ（1対多関連）
- User ⟷ AIPromptTemplate: ユーザーは複数のAIプロンプトテンプレートを作成できる（1対多関連）

### フォーラム関連
- User ⟷ ForumTopic: ユーザーは複数のフォーラムトピックを作成できる（1対多関連）
- User ⟷ ForumPost: ユーザーは複数のフォーラム投稿を作成できる（1対多関連）
- User ⟷ ForumPostReaction: ユーザーは複数の投稿にリアクションできる（1対多関連）
- User ⟷ ForumTopicSubscription: ユーザーは複数のトピックを購読できる（1対多関連）
- ForumCategory ⟷ ForumCategory: カテゴリーは階層構造を持つ（自己参照関連）
- ForumCategory ⟷ ForumTopic: カテゴリーは複数のトピックを含む（1対多関連）
- ForumTopic ⟷ ForumPost: トピックは複数の投稿を含む（1対多関連）
- ForumPost ⟷ ForumPost: 投稿は返信構造を持つ（自己参照関連）
- ForumPost ⟷ ForumPostReaction: 投稿は複数のリアクションを受ける（1対多関連）
- ForumPost ⟷ ForumPostAttachment: 投稿は複数の添付ファイルを持つ（1対多関連）
- ForumTopic ⟷ ForumTopicView: トピックは複数の閲覧記録を持つ（1対多関連）
- ForumTopic ⟷ ForumTopicSubscription: トピックは複数のユーザーに購読される（1対多関連）
- ForumTopic ⟷ ForumTopicTag: トピックは複数のタグを持つ（1対多関連）

### 通知関連
- User ⟷ Notification: ユーザーは複数の通知を受け取る（1対多関連）
- User ⟷ NotificationSetting: ユーザーは複数の通知設定を持つ（1対多関連）
- Notification ⟷ NotificationMetaData: 通知は複数のメタデータを持つ（1対多関連）
- BroadcastNotification ⟷ Notification: 全体通知は複数の個別通知を生成する（1対多関連）
- BroadcastNotification ⟷ BroadcastTargetRole: 全体通知は複数の対象ロールを持つ（1対多関連）
- BroadcastNotification ⟷ BroadcastTargetSchool: 全体通知は複数の対象学校を持つ（1対多関連）
- BroadcastNotification ⟷ BroadcastNotificationMetaData: 全体通知は複数のメタデータを持つ（1対多関連）
- Role ⟷ BroadcastTargetRole: ロールは複数の全体通知ターゲットに含まれる（1対多関連）
- School ⟷ BroadcastTargetSchool: 学校は複数の全体通知ターゲットに含まれる（1対多関連）

### 監査関連
- User ⟷ AuditLog: ユーザーに関連する複数の監査ログが存在する（1対多関連）
- AuditLog ⟷ AuditLogDetails: 監査ログは複数の詳細情報を持つ（1対多関連）
- AuditLog ⟷ AuditLogAdditionalInfo: 監査ログは複数の追加情報を持つ（1対多関連）

## 列挙型（Enum）定義

### NotificationType (通知タイプ)
- SYSTEM_MESSAGE - システムメッセージ
- PAYMENT_SUCCESS - 決済成功
- PAYMENT_FAILED - 決済失敗
- SUBSCRIPTION_EXPIRING - サブスクリプション期限間近
- NEW_CONTENT - 新コンテンツ追加
- STUDY_REMINDER - 学習リマインダー
- ACCOUNT_ALERT - アカウントアラート
- DIRECT_MESSAGE - ダイレクトメッセージ
- PLAN_COMPLETED - 学習プラン完了
- GOAL_REMINDER - 目標リマインダー
- FORUM_MENTION - フォーラムでの言及
- FORUM_REPLY - フォーラム返信
- FORUM_TOPIC_ACTIVITY - フォーラムトピックアクティビティ

### NotificationPriority (通知優先度)
- HIGH - 高
- MEDIUM - 中
- LOW - 低

### ReactionType (リアクションタイプ)
- LIKE - いいね
- HELPFUL - 役立つ
- LAUGH - 笑
- THANKS - ありがとう
- INSIGHTFUL - 洞察力のある

### NotificationLevel (通知レベル)
- NONE - 通知なし
- WATCHING - ウォッチ中（すべての投稿で通知）
- TRACKING - トラッキング中（メンションと返信のみ通知）
- NORMAL - 通常（メンションのみ通知）
- MUTED - ミュート（通知なし）

### AuditLogAction (監査ログアクション)
- USER_CREATE - ユーザー作成
- USER_UPDATE - ユーザー更新
- USER_DELETE - ユーザー削除
- USER_PASSWORD_CHANGE - ユーザーパスワード変更
- USER_EMAIL_VERIFY - ユーザーメール検証
- USER_LOCK - ユーザーロック
- USER_UNLOCK - ユーザーアンロック
- USER_LOGIN - ユーザーログイン
- USER_LOGIN_FAILED - ユーザーログイン失敗
- USER_LOGOUT - ユーザーログアウト
- USER_ROLE_ASSIGN - ユーザーロール割り当て
- USER_ROLE_REMOVE - ユーザーロール削除
- TOKEN_ISSUE - トークン発行
- TOKEN_REFRESH - トークン更新
- TOKEN_REVOKE - トークン失効
- SUBSCRIPTION_CREATE - サブスクリプション作成
- SUBSCRIPTION_UPDATE - サブスクリプション更新
- SUBSCRIPTION_CANCEL - サブスクリプションキャンセル
- PAYMENT_PROCESS - 決済処理
- PAYMENT_REFUND - 決済返金
- CONTENT_CREATE - コンテンツ作成
- CONTENT_UPDATE - コンテンツ更新
- CONTENT_DELETE - コンテンツ削除
- FORUM_TOPIC_CREATE - フォーラムトピック作成
- FORUM_TOPIC_DELETE - フォーラムトピック削除
- PERSONAL_STATEMENT_CREATE - 志望理由書作成
- PERSONAL_STATEMENT_UPDATE - 志望理由書更新
- SYSTEM_CONFIG_CHANGE - システム設定変更
- SECURITY_BREACH - セキュリティ侵害

### AuditLogStatus (監査ログステータス)
- SUCCESS - 成功
- FAILURE - 失敗
- PENDING - 処理中
- COMPLETED - 完了

## データベース初期化と管理

システムはAlembicを使用してデータベースマイグレーションを管理しています。マイグレーションファイルは`alembic/versions/`ディレクトリに保存されています。

### 操作手順

1. Dockerコンテナを起動:
   ```
   docker-compose up -d
   ```

2. マイグレーションファイルを作成:
   ```
   docker-compose exec backend alembic revision --autogenerate -m "説明を入力"
   ```

3. マイグレーションを適用:
   ```
   docker-compose exec backend alembic upgrade head
   ```

4. デモデータを挿入（必要に応じて）:
   ```
   docker-compose exec backend python -m app.database.init_db
   ```

データベースの初期化とデモデータの挿入は`app/database/init_db.py`で行われます。デモデータの内容は`app/migrations/demo_data.py`に定義されています。

## インデックス

パフォーマンス向上のため、以下のインデックスを設定します：

- `conversations`: `user1_id`, `user2_id`の複合インデックス
- `messages`: `conversation_id`と`created_at`の複合インデックス、`sender_id`のインデックス

## 実装上の注意

通信機能を実装する際、以下の点に注意してください：

1. 会話の作成時には必ず2人のユーザーを指定する必要があります
2. メッセージは必ず特定の会話に属し、送信者を持つ必要があります
3. 既読管理は`read`フラグで行います
4. `message_type`は将来的に拡張できるよう、単純な文字列型としています（例: "text", "image", "file"など）
5. ユーザーはメッセージを削除できませんが、管理者は必要に応じて削除できるようにします
