# MONONO Agent 詳細設計

## 1. 概要

MONONO Agentは、ユーザーからの指示に基づき、大規模言語モデル（LLM）との対話、外部ツールの利用、および他のエージェントとの連携（ハンドオフ）を通じて、タスクを実行する自律型AIエージェントです。

このドキュメントは、MONONO Agentの内部構造、主要コンポーネント、処理フロー、およびデータ構造について詳細に記述します。

## 2. MONONO Agentの役割と責務

- ユーザーからの自然言語による指示を理解し、適切なアクションを計画・実行する。
- 必要に応じて、登録されたツール（API連携、データ処理など）を利用する。
- タスクの性質に応じて、他の専門エージェントに処理を委譲（ハンドオフ）し、結果を受け取る。
- 対話の文脈を記憶し、一貫性のある応答を生成する。
- 処理の進捗や結果をストリーミング形式でリアルタイムに提供する。

## 3. 主要コンポーネント

MONONO Agentは、以下の主要コンポーネントから構成されます。`base_agent.py` はこれらのコンポーネントの基本的なインターフェースや連携の枠組みを提供します。

### 3.1. LLM Adapter

- **責務**: 特定のLLM（例: GPT-4o, Claude 3）との通信を抽象化し、統一されたインターフェースを提供します。
- **機能**:
    - LLMへのリクエスト送信（プロンプト、モデルパラメータ等）。
    - LLMからのレスポンス受信（テキスト生成、ツールコール指示）。
    - ストリーミングレスポンスの処理。
    - 使用トークン数などのメタデータ取得。
- **実装**:
    - `base_agent.py` の `llm_adapter` 属性にインスタンスが設定される想定です。
    - 各LLMプロバイダーに対応した具体的なアダプタークラス（例: `OpenAIAdapter`, `AnthropicAdapter`）を別途実装し、エージェント初期化時に注入します。
    - `_default_llm_adapter` メソッドは、デフォルトのアダプターを初期化する役割を担うことを意図していますが、現状は `NotImplementedError` となっています。

### 3.2. Tool Registry (および Tools)

- **責務**: エージェントが利用可能なツールを管理し、実行します。
- **機能**:
    - ツールの登録（関数やクラスベースのツール）。
    - LLMが生成したツールコール指示に基づき、対応するツールを特定。
    - ツールの入力パラメータのバリデーション（Pydanticモデルを利用想定）。
    - ツールの実行と結果の取得。
- **実装**:
    - `base_agent.py` の `tool_registry` 属性にインスタンスが設定される想定です。
    - エージェント初期化時に渡される `tools` リスト（`_tools_definitions`）は、Tool Registryによって処理され、実行可能な形式（`_tools`）に変換される想定です。
    - `_execute_tool_and_get_response` メソッド内で、Tool Registryを通じてツールが実行されます（現在はスタブ実装）。

### 3.3. Memory

- **責務**: 対話の履歴や重要な情報を記憶し、エージェントの意思決定に利用します。
- **機能**:
    - 短期記憶: 直近の対話履歴（ユーザーの発言、エージェントの応答、ツール実行結果など）を保持します。
    - 長期記憶（拡張機能として）: より永続的な情報や知識をベクトルデータベースなどに保存し、検索可能にします。
- **実装**:
    - `base_agent.py` では、`_memory` 属性（Pythonのリスト）として短期記憶が実装されています。
    - `_add_to_memory` メソッドでメッセージがメモリに追加されます。
    - `_preprocess_messages` メソッドで、LLMに渡すプロンプトにメモリの内容が挿入されます。
    - `extra_cfg` を通じて、メモリのウィンドウサイズ（`memory_window_size`）や最大アイテム数（`max_memory_items`）を設定できます。

### 3.4. Guardrail

- **責務**: エージェントの入出力や行動が、定義されたポリシーや倫理基準に準拠していることを保証します。
- **機能**:
    - 入力ガードレール: ユーザーからの不適切な入力（例: 有害なコンテンツ、機密情報）を検知・フィルタリング。
    - 出力ガードレール: エージェントが生成する応答が、不適切または有害でないことを検証。
    - ツール使用ガードレール（TokenGuardなど）: 特定のツールの使用許可や頻度を制御。
- **実装**:
    - `base_agent.py` の `guardrail` 属性にインスタンスが設定される想定です。
    - `stream` メソッド内のコメントアウトされた箇所で、入力・出力ガードレールの呼び出しが示唆されています。
    - 具体的なガードレールロジックは、別途 `Guardrail` クラスとして実装し、注入する必要があります。

### 3.5. Trace Logger

- **責務**: エージェントの処理ステップ、内部状態、エラー情報などを記録し、デバッグや監査に利用します。
- **機能**:
    - 処理開始・終了、ツール呼び出し、ハンドオフ、エラー発生などのイベントを記録。
    - ログレベルや出力先（コンソール、ファイル、外部監視システム）の設定。
- **実装**:
    - `base_agent.py` の `trace_logger` 属性にインスタンスが設定される想定です。
    - `stream` メソッドや `_execute_tool_and_get_response` メソッド内のコメントアウトされた箇所で、`trace_logger.trace()` の呼び出しが示唆されています。
    - 具体的なロギング実装は、別途 `TraceLogger` クラスとして実装し、注入する必要があります。

### 3.6. Planning & Task Decomposition Engine

- **責務**: 複雑なユーザーリクエストやタスクを、実行可能なより小さなサブタスクに分解し、実行計画を立案します。
- **機能**:
    - 複雑なタスクのステップバイステップへの分解。
    - サブタスク間の依存関係の管理（例: タスクAの完了後にタスクBを実行）。
    - 並列実行が可能なサブタスクの特定とスケジューリング。
    - 計画の進捗追跡と、必要に応じた計画の再調整。
- **概念図**:
  ```mermaid
  graph TD
    A[複雑なタスク] --> B[Planning Engine]
    B --> C[サブタスク1]
    B --> D[サブタスク2]
    B --> E[サブタスク3]
    C --> F[実行・結果統合]
    D --> F
    E --> F
  ```
- **実装**:
    - LLM自身が計画能力を持つ場合、その能力を活用します。
    - より明示的な制御が必要な場合、専用のプランニングモジュールを実装し、LLMと連携させます。`base_agent.py` の `extra_cfg` や専用の属性を通じて設定・制御される可能性があります。

### 3.7. Context Manager

- **責務**: 対話のコンテキスト、ユーザー情報、セッション状態などを効果的に管理し、LLMやツールが必要とする情報を適切に提供します。
- **機能**:
    - セッション管理: 複数のユーザーや会話を並行して処理し、それぞれのコンテキストを分離・維持します。
    - ユーザープロファイル管理: ユーザーの過去の対話履歴、設定、嗜好などの情報を保持し、パーソナライズに活用します。
    - プロジェクト・タスクコンテキストの維持: 長期にわたるプロジェクトや複数ステップのタスクにおいて、関連情報を保持し続けます。
    - 関連情報の自動取得と注入: 現在のクエリやタスクに応じて、必要な情報をメモリや外部ソース（例: ドキュメント、データベース）から動的に取得し、LLMのプロンプトやツールの入力に含めます。
- **概念的なクラス構造**:
  ```python
  class ContextManager:
      def __init__(self):
          self.active_contexts = {}  # セッションID -> コンテキストデータ
          self.global_context = {}   # 全セッション共通のグローバル情報
          self.user_profiles = {}    # ユーザーID -> プロファイルデータ
      
      def get_relevant_context(self, query, session_id, user_id=None):
          # クエリ、セッション、ユーザー情報に基づいて関連性の高いコンテキストを選択・構築
          # 例: セッションコンテキスト + ユーザープロファイル + グローバルコンテキストの一部
          pass
  ```
- **実装**:
    - `base_agent.py` の `_memory` は短期的なセッションコンテキストの一部を担いますが、より高度なContext Managerは、セッションID、ユーザーIDと連携し、永続化ストレージも活用する形で実装されます。

### 3.8. Workflow Engine

- **責務**: 事前に定義された、または動的に生成されたワークフロー（一連のタスクやツールの実行順序）を管理し、実行します。
- **機能**:
    - ワークフロー定義の解釈: YAMLやJSONなどで記述されたワークフロー定義を読み込み、実行計画に変換します。
    - ステップ実行: ワークフロー内の各ステップ（ツール実行、条件分岐、ループなど）を順次または並列に実行します。
    - 依存関係管理: ステップ間の依存関係（例: "データ収集"ステップ完了後に"前処理"ステップを実行）を解決します。
    - 条件付き実行: 特定の条件に基づいてステップの実行を制御します。
    - 状態管理: ワークフロー全体の進捗と各ステップの状態を追跡します。
- **ワークフロー定義例 (`workflow.yaml`)**:
  ```yaml
  workflow:
    name: "データ分析パイプライン"
    steps:
      - name: "データ収集"
        tool: "data_collector" # Tool Registryに登録されたツール名
        condition: "always"   # 実行条件
      - name: "前処理"
        tool: "data_preprocessor"
        depends_on: ["データ収集"] # 依存するステップ
      - name: "分析"
        tool: "analyzer"
        depends_on: ["前処理"]
        parallel: true # 並列実行の可否
      - name: "レポート生成"
        tool: "report_generator"
        depends_on: ["分析"]
  ```
- **実装**:
    - Planning & Task Decomposition Engineと密接に連携します。プランナーが生成したタスクリストをワークフローとして実行したり、定義済みのワークフローを呼び出したりします。
    - Tool Registryを利用して各ステップのツールを実行します。

### 3.9. Resource Manager

- **責務**: エージェントが利用するリソース（APIコール回数、計算リソース、コストなど）を監視・管理し、効率的かつ制限内で動作するように制御します。
- **機能**:
    - APIクォータ管理: 外部APIの呼び出し回数やレート制限を追跡し、超過しないように調整します。
    - 計算リソース監視: CPU、メモリ、GPUなどの使用状況を監視し、必要に応じてタスクの優先度調整やスケーリングを行います。
    - コスト追跡と予算管理: LLMの利用料、ツールの実行コストなどを追跡し、設定された予算を超えないように制御します。
    - 実行可否判断: タスクやツールの実行前に、利用可能なリソースやコストを評価し、実行の可否を判断します。
- **概念的なクラス構造**:
  ```python
  class ResourceManager:
      def __init__(self):
          self.api_quotas = {"openai": {"limit": 1000, "used": 0}}
          self.compute_resources = {"cpu_limit": "80%", "memory_limit": "4GB"}
          self.cost_tracking = {"budget": 10.0, "spent": 0.0} # 単位はUSDなど
      
      def can_execute(self, tool_name, estimated_cost, required_resources):
          # APIクォータ、予算、計算リソースを確認し、実行可否を返す
          # self.check_quotas(tool_name)
          # self.check_budget(estimated_cost)
          # self.check_compute(required_resources)
          return True # 仮
  ```
- **実装**:
    - 各コンポーネント（LLM Adapter, Tool Registryなど）と連携し、リソース消費情報を収集します。
    - `base_agent.py` の `extra_cfg` を通じて、リソース制限や予算を設定できるようにします。

### 3.10. Learning & Adaptation Engine

- **責務**: エージェントの過去の経験（成功・失敗事例、ユーザーフィードバックなど）から学習し、将来のパフォーマンスを向上させます。
- **機能**:
    - 成功パターンの学習: どのようなタスクや入力に対して、どのアプローチ（ツール選択、プロンプト戦略など）が成功しやすいかを学習します。
    - 失敗からの学習と改善提案: タスクの失敗原因を分析し、同様の失敗を繰り返さないための改善策（例: プロンプトの修正、代替ツールの使用）を提案または自動適用します。
    - ユーザーへの応答パーソナライゼーション: ユーザーの過去の対話、明示的な設定、フィードバックに基づいて、応答スタイルや情報提供の仕方を調整します。
    - 強化学習ループの導入（高度な機能）: 報酬シグナルに基づいてエージェントの行動ポリシーを継続的に最適化します。
- **概念的なクラス構造**:
  ```python
  class LearningEngine:
      def track_success_patterns(self, task_description, approach_details, was_successful, user_feedback=None):
          # 実行されたタスク、取られたアプローチ、結果、フィードバックを記録・分析
          pass
      
      def suggest_improvements(self, failed_task_context):
          # 失敗したタスクのコンテキストから改善点を推論
          return "Consider rephrasing the prompt or using the 'search_web' tool." # 例
      
      def personalize_responses(self, user_id, interaction_history, preferences):
          # ユーザー情報に基づいて応答生成戦略を調整
          pass
  ```
- **実装**:
    - Trace Loggerからのログデータや、ユーザーからの直接的なフィードバックを利用します。
    - 学習結果は、プロンプト生成ロジック、ツール選択アルゴリズム、Context Managerの挙動などに反映されます。

### 3.11. Error Recovery & Resilience Manager

- **責務**: システム内で発生する可能性のある様々なエラー（ツールの失敗、APIエラー、ネットワーク問題など）を検知し、適切に対処することで、エージェントの安定性と信頼性を高めます。
- **機能**:
    - リトライポリシーの実装: 一時的なエラー（例: ネットワーク瞬断）に対して、設定された回数や間隔で処理を再試行します。
    - フォールバック戦略の実行: 主要なツールや手段が失敗した場合に、代替のツールやアプローチ（例: 別のAPIエンドポイント、より単純な処理）に切り替えます。
    - サーキットブレーカー: 特定のコンポーネントや外部サービスで障害が頻発する場合、一時的にそのコンポーネントへのリクエストを停止し、システム全体の負荷増大や連鎖的な障害を防ぎます。
    - 部分的な結果の提供: 完全なタスク遂行が不可能な場合でも、達成できた部分的な結果や中間成果をユーザーに提供します。
    - ユーザーへの状況説明とガイダンス: エラー発生時、ユーザーに状況を分かりやすく説明し、可能な対処法や次のステップを案内します。
- **概念的なクラス構造**:
  ```python
  class ErrorRecoveryManager:
      def __init__(self):
          self.retry_policies = {"default": {"max_attempts": 3, "delay": 1}} # 秒
          self.fallback_strategies = {"tool_A_failure": "try_tool_B"}
          self.circuit_breakers = {"service_X": {"is_open": False, "failure_threshold": 5}}

      def handle_failure(self, error, context_of_failure):
          # エラーの種類とコンテキストに応じてリトライ、フォールバックなどを試みる
          # if should_retry(error, context_of_failure, self.retry_policies): ...
          # elif can_fallback(error, context_of_failure, self.fallback_strategies): ...
          # else: report_to_user_and_log(error, context_of_failure)
          pass
  ```
- **実装**:
    - 各主要コンポーネント（LLM Adapter, Tool Registryなど）の呼び出し箇所に組み込まれ、例外処理と連携します。
    - `base_agent.py` の `stream` メソッド内のエラーハンドリングロジックを拡張する形で統合されます。

### 3.12. Multi-modal Processor

- **責務**: テキストだけでなく、画像、音声、動画などの多様なモダリティの情報を処理し、エージェントがこれらの情報を理解したり生成したりできるようにします。
- **機能**:
    - 画像処理: 画像の内容理解（オブジェクト検出、シーン認識）、光学文字認識（OCR）、画像生成、画像編集。
    - 音声処理: 音声認識（Speech-to-Text）、音声合成（Text-to-Speech）、話者識別。
    - 動画処理: 動画の内容解析（アクション認識、オブジェクト追跡）、字幕生成、動画要約。
    - マルチモーダルLLMとの連携: GPT-4Vのようなマルチモーダル対応LLMを活用し、複数モダリティにまたがる情報を統合的に扱います。
- **概念的なクラス構造**:
  ```python
  class MultiModalProcessor:
      def process_image(self, image_data, task_type="describe"): # task_type: "describe", "ocr", "generate"
          # 画像処理ロジック (例: 外部API呼び出し、専用モデル使用)
          pass
      
      def process_audio(self, audio_data, task_type="transcribe"): # task_type: "transcribe", "synthesize"
          # 音声処理ロジック
          pass
      
      def process_video(self, video_data, task_type="summarize"): # task_type: "summarize", "caption"
          # 動画処理ロジック
          pass
  ```
- **実装**:
    - 対応するLLM Adapterがマルチモーダル入出力をサポートする場合、それを利用します。
    - 必要に応じて、特定のモダリティ処理に特化した外部APIやライブラリ（例: OpenAI Vision API, Google Cloud Vision AI, ElevenLabs API, OpenCV）と連携する専用ツールとしてTool Registryに登録されます。

### 3.13. Security & Privacy Manager

- **責務**: エージェントの動作全体を通じて、データのセキュリティとユーザーのプライバシーを保護します。
- **機能**:
    - データサニタイズ: ユーザー入力やツールからの出力に含まれる個人を特定できる情報（PII）や機密情報を検出し、マスキング、匿名化、または削除します。
    - アクセス制御と権限チェック: ユーザーや他のエージェントが特定のリソース（ツール、データ、機能）にアクセスする際の権限を検証します。
    - 暗号化: 機密性の高いデータ（APIキー、ユーザー認証情報、保存データなど）を保管時および転送時に暗号化します。
    - 監査ログ: セキュリティに関連するイベント（ログイン試行、権限変更、データアクセスなど）を記録し、追跡可能性を確保します。
    - コンプライアンス対応: GDPR、CCPAなどのデータ保護規制に準拠するための機能を提供します。
- **概念的なクラス構造**:
  ```python
  class SecurityManager:
      def __init__(self):
          self.encryption_handler = EncryptionHandler() # 暗号化・復号処理
          self.access_control = AccessControlList()    # アクセス制御リスト
          self.audit_logger = AuditLogger()            # 監査ログ記録

      def sanitize_data(self, data, pii_patterns):
          # データからPIIを検出しマスキング/削除
          return "sanitized_data" # 仮
      
      def check_permissions(self, user_identity, action, resource_id):
          # ユーザーのアクションが許可されているか確認
          return self.access_control.is_allowed(user_identity, action, resource_id) # 仮
  ```
- **実装**:
    - Guardrailコンポーネントと密接に連携します。Guardrailがポリシー違反を検知するのに対し、Security & Privacy Managerはより具体的なセキュリティ操作（暗号化、アクセス制御など）を実行します。
    - 全てのデータ入出力ポイント（ユーザーインターフェース、LLM Adapter、Tool Registry、Memoryなど）にフックする形で統合されます。

### 3.14. Performance Optimizer

- **責務**: エージェントの応答速度、処理効率、リソース使用率を最適化し、ユーザーエクスペリエンスを向上させます。
- **機能**:
    - キャッシュ管理: 頻繁にアクセスされるデータや高コストな処理結果（LLM応答、ツール実行結果など）をキャッシュし、再利用することで応答時間を短縮します。
    - ロードバランシング（複数エージェントインスタンス運用時）: 複数のエージェントインスタンスにリクエストを均等に分散し、単一インスタンスへの負荷集中を防ぎます。
    - クエリオプティマイザ: LLMへのプロンプトやツールへのリクエストを、より効率的に処理されるように最適化（例: 不要な情報の削除、バッチ処理の適用）します。
    - 最適なツール選択: 同じ目的を達成できる複数のツールが存在する場合、現在のコンテキストやパフォーマンス要件（速度、コスト、精度など）に基づいて最適なツールを選択します。
    - 遅延読み込みと非同期処理の活用: 重い処理やI/Oバウンドな操作を非同期に実行し、エージェント全体の応答性を維持します。
- **概念的なクラス構造**:
  ```python
  class PerformanceOptimizer:
      def __init__(self):
          self.cache_manager = CacheManager(max_size="1GB", default_ttl=3600) # 秒
          # self.load_balancer = LoadBalancer(strategy="round_robin") # 複数インスタンス構成の場合
          # self.query_optimizer = QueryOptimizer()

      def optimize_tool_selection(self, task_description, available_tools_with_metadata):
          # タスクと利用可能なツールのメタデータ (コスト、速度など) から最適なツールを選択
          return "selected_tool_name" # 仮
      
      def get_or_set_cache(self, cache_key, computation_function, ttl=None):
          # キャッシュの取得または設定
          return self.cache_manager.get_or_set(cache_key, computation_function, ttl)
  ```
- **実装**:
    - ResourceManagerと連携し、リソース効率も考慮した最適化を行います。
    - `base_agent.py` の `stream` メソッドや `_execute_tool_and_get_response` など、主要な処理パスにキャッシュ機構や最適化ロジックを組み込みます。

### 3.15. Collaboration Manager

- **責務**: 複数のエージェント間、またはエージェントと人間の間での協調作業を促進し、より複雑なタスクの達成を支援します。
- **機能**:
    - セッション共有: 複数のユーザーやエージェントが同じ対話セッションやタスクコンテキストを共有し、共同で作業を進められるようにします。
    - 人間への作業委譲（Human-in-the-loop）: エージェントが判断に迷う場合や、人間の専門知識が必要な場合に、タスクを人間にエスカレーションし、指示や承認を仰ぎます。
    - 複数エージェントの結果統合: 異なるエージェントが並行して処理した結果や意見を集約し、矛盾を解消したり、より質の高い最終結果を生成したりします。
    - 役割ベースのタスク割り当て: 複雑なタスクをサブタスクに分解し、それぞれの専門性を持つエージェントや人間に割り当てます。
- **概念的なクラス構造**:
  ```python
  class CollaborationManager:
      def share_session_with_users(self, session_id, user_ids_to_share_with):
          # 指定されたユーザーとセッションを共有
          pass
      
      def delegate_task_to_human(self, task_details, reason_for_delegation, human_expert_role=None):
          # タスクを適切な人間の専門家に委譲し、その応答を待つ
          return "human_response" # 仮
      
      def merge_agent_outputs(self, list_of_agent_results, merge_strategy="majority_vote"):
          # 複数のエージェントからの結果を統合
          # merge_strategy: "majority_vote", "summation", "average", "llm_based_synthesis" など
          return "merged_result" # 仮
  ```
- **実装**:
    - `base_agent.py` の `handoff` 機能はエージェント間連携の基礎となりますが、Collaboration Managerはより高度な協調シナリオ（複数エージェントによる同時作業、人間とのインタラクションなど）を扱います。
    - Context Managerと連携し、共有セッションのコンテキストを管理します。
    - Workflow Engineと連携し、人間による承認ステップを含むワークフローを実行します。

## 4. 処理フロー

### 4.1. 基本的な対話フロー (ストリーミング)

1.  **ユーザー入力**: ユーザーがメッセージを送信します。
2.  **エージェント実行 (`run` または `stream`)**:
    - `run` メソッドが呼び出された場合、内部で `stream` メソッドを呼び出します。
    - `session_id` が提供される場合、セッション管理に利用されます。
3.  **ストリーム開始 (`stream` メソッド)**:
    - 内部シーケンスカウンター (`_seq_counter`) を初期化。
    - `_create_internal_chunk` ヘルパー関数を定義（SSEチャンク生成用）。
4.  **メッセージ前処理 (`_preprocess_messages`)**:
    - システムプロンプト（エージェントの指示 `self.instructions`）を作成。
    - 短期メモリ (`self._memory`) から過去の対話履歴を取得。
    - システムプロンプト、メモリ、現在のユーザーメッセージを結合して、LLMに渡すメッセージリストを構築。
5.  **LLM Adapterによる対話 (`llm_adapter.chat`)**: (現状はスタブ実装)
    - 準備されたメッセージリスト、モデル名 (`self.model`)、ストリーミングフラグなどをLLM Adapterに渡してチャットを開始。
    - LLM AdapterはLLMからの応答をチャンク単位で非同期に返します。
6.  **チャンク処理ループ**:
    - **テキスト差分 (`delta`)**: LLMがテキストを生成すると、`delta` タイプのチャンクが生成され、`content` として部分的なテキストが含まれます。これらのチャンクはそのままクライアントに中継されます。
        ```json
        {"time": "...", "agent": "...", "type": "delta", "data": {"content": "some text"}, "seq": N}
        ```
    - **ツールコール (`tool_call`)**: LLMがツール使用を指示すると、`tool_call` タイプのチャンクが生成されます。これには、呼び出す関数の名前、引数、ユニークなコールIDが含まれます。
        ```json
        {"time": "...", "agent": "...", "type": "tool_call", "data": {"id": "call_xyz", "function": {"name": "tool_name", "arguments": "{"param": "value"}"}}, "seq": N}
        ```
    - **ツール実行 (`_execute_tool_and_get_response`)**: (現状はスタブ実装)
        - `tool_call` チャンクを受け取ると、Tool Registryを通じて対応するツールを実行。
        - ツール実行結果（成功またはエラー）を準備。
    - **ツール応答 (`tool_response`)**: ツール実行後、`tool_response` タイプのチャンクが生成されます。これには、元のツールコールID、ツール名、および結果のプレビュー（または全体）が含まれます。
        ```json
        {"time": "...", "agent": "...", "type": "tool_response", "data": {"tool_call_id": "call_xyz", "name": "tool_name", "content_preview": "Tool output..."}, "seq": N}
        ```
        - ツール実行結果は、次のLLMへの入力として `{"role": "tool", "tool_call_id": ..., "name": ..., "content": ...}` の形式で追加される想定です。
    - **使用状況 (`usage`)**: 対話の最後に、LLMからトークン使用量などの情報が `usage` タイプのチャンクとして送信されることがあります。
        ```json
        {"time": "...", "agent": "...", "type": "usage", "data": {"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z}, "seq": N}
        ```
    - **エラー (`error`)**: 処理中にエラーが発生した場合、`error` タイプのチャンクが生成されます。
        ```json
        {"time": "...", "agent": "...", "type": "error", "data": {"message": "Error details", "type": "ErrorType"}, "seq": N}
        ```
7.  **応答後処理 (`_postprocess_response`)**:
    - LLMからの最終的なアシスタントメッセージ（ツール使用がない場合や、ツール使用後の最終応答）をメモリ (`_memory`) に追加します。
8.  **ストリーム終了**: すべてのチャンクが送信されるとストリームが終了します。
    - `run` メソッドの場合、収集された `delta` チャンクの `content` を結合し、最終的な応答オブジェクト（ロール、コンテンツ、使用状況、ツールコール情報などを含む）を返します。

### 4.2. ツール呼び出しの詳細フロー (LLM Adapter/Tool Registry 実装時)

1.  LLMがツール呼び出しを決定し、`tool_call` 形式のデータを生成します (例: OpenAIのFunction Calling/Tool Calling)。
2.  LLM Adapterがこのデータをパースし、`base_agent.py` の `stream` メソッドに `tool_call` チャンクとして渡します。
3.  `stream` メソッドは `_execute_tool_and_get_response` を呼び出します。
4.  `_execute_tool_and_get_response`:
    a.  Tool Registryの `parse_arguments` を使用して、LLMが生成した引数文字列をツールの期待する型にパース・検証します。
    b.  (オプション) Guardrail (TokenGuardなど) でツールの実行可否をチェックします。
    c.  Tool Registryの `execute` を呼び出し、指定されたツールを実行します。引数にはパース済みの引数、セッションID、エージェント名などが渡されます。
    d.  ツールの実行結果（成功時の返り値、または例外）を取得します。
    e.  結果を適切な文字列形式（JSONなど）にシリアライズします。
    f.  ツール名、ツールコールIDと共に、この文字列化された結果を返します。
5.  `stream` メソッドは、ツール実行結果を含む `tool_response` チャンクを生成してyieldします。
6.  さらに、ツール実行結果を `{"role": "tool", ...}` の形式でメッセージリストに追加し、LLM Adapterを通じてLLMに送信し、対話を継続します。LLMはツール結果を踏まえて次の応答を生成します。

### 4.3. ハンドオフフロー (`handoff`, `on_handoff_return`)

- **目的**: 現在のエージェントでは処理できない、または他のエージェントの方が適任であるタスクを、別のエージェントに委譲します。
- **`handoff` メソッド**:
    1.  **深度チェック**: 最大ハンドオフ深度 (`MAX_HANDOFF_DEPTH`) を超えていないか確認します。超えている場合はエラーを返します。
    2.  **深度更新**: 現在のエージェントのハンドオフ深度 (`_handoff_depth`) をインクリメントします。
    3.  **ターゲットエージェント実行**: `target_agent.stream()` (または `run()`) を呼び出し、現在のメッセージとコンテキストを渡します。
    4.  **結果ストリーミング**: ターゲットエージェントからのチャンクを、自身の名前に「中継元」として付加（または `agent_override` でターゲットエージェント名に設定）しつつ、呼び出し元にストリーミングします。
        ```json
        // チャンクの agent フィールドが handoff 先のエージェント名になることが期待される
        {"time": "...", "agent": "target_agent_name", "type": "delta", "data": {"content": "text from target"}, "seq": N}
        ```
    5.  ターゲットエージェントの処理が完了したら、深度をデクリメントします (`on_handoff_return` で行う想定)。
- **`on_handoff_return` メソッド**:
    - ターゲットエージェントからの処理が完了（正常終了またはエラー）した際に呼び出されるコールバック的な役割を想定。
    - ハンドオフ深度 (`_handoff_depth`) をデクリメントします。
    - 必要に応じて、ターゲットエージェントからの最終結果を自身のメモリに追加したり、後続処理を決定したりします。
- **循環ハンドオフ防止**: ハンドオフ深度だけでなく、ハンドオフの経路（どのエージェントからどのエージェントへ委譲されたか）を追跡するメカニズムも、複雑なシナリオでは必要になる場合があります。

## 5. データ構造

### 5.1. メッセージオブジェクト

LLMとの対話やメモリに保存されるメッセージは、以下の形式を基本とします。

```typescript
interface Message {
  role: "system" | "user" | "assistant" | "tool";
  content: string; // user, assistant, system の場合
  tool_calls?: ToolCall[]; // assistant がツール使用を指示する場合
  tool_call_id?: string; // roleがtoolの場合、対応するtool_callsのID
  name?: string; // roleがtoolの場合、ツールの名前
}

interface ToolCall {
  id: string; // ツールコールのユニークID
  type: "function"; // 現状はfunctionのみ想定
  function: {
    name: string; // 呼び出す関数/ツール名
    arguments: string; // JSON文字列形式の引数
  };
}
```
`base_agent.py` の `_preprocess_messages` や `_add_to_memory` はこの構造を部分的に扱っています。

### 5.2. ツール定義

エージェント初期化時に渡される `tools` (内部で `_tools_definitions`) は、関数オブジェクトそのもの、または以下のような辞書形式を想定できます (OpenAIのFunction Calling/Tool Callingスキーマに類似)。

```typescript
interface ToolDefinition {
  type: "function";
  function: {
    name: string;
    description?: string;
    parameters: JsonSchema; // Pydanticモデルから生成可能なJSON Schema
  };
}
```
Tool Registryはこれらの定義をパースし、実行可能な状態にします。

### 5.3. ストリーミングチャンク (SSE)

`_create_internal_chunk` で生成されるチャンクは、`AgentSDK.md` (仮称) で定義されるSSE形式に準拠することを想定します。
`base_agent.py` の `stream` メソッドでyieldされるチャンクの各タイプ (`delta`, `tool_call`, `tool_response`, `usage`, `error`) は、このSSE仕様に基づきます。

```json
// 例: delta チャンク
{
  "time": "2023-10-27T10:30:00.123Z", // ISO 8601 タイムスタンプ
  "agent": "MononoAgent",            // チャンクを生成したエージェント名
  "type": "delta",                   // チャンクの種類
  "data": {                          // チャンク固有のデータ
    "content": "これは応答の断片です。"
  },
  "seq": 12                          // セッション内でのチャンクのシーケンス番号
}
```

## 6. 拡張性

-   **新しいLLM**: 新しいLLMプロバイダーに対応するには、`LLMAdapter` の新しいサブクラスを作成し、設定ファイルや初期化時に指定することで容易に追加できます。
-   **新しいツール**:
    -   Python関数としてツールを定義し、必要であればPydanticモデルで入力パラメータの型アノテーションを行います。
    -   これらのツールをエージェント初期化時に `tools` リストに追加することで、Tool Registryが自動的に認識し、LLMに提示できるようになります。
-   **新しいエージェント**: `BaseAgent` を継承し、特定の役割に特化した `instructions`、`tools`、`model` を設定することで、新しいエージェントタイプを作成できます。

## 7. エラーハンドリング

-   **LLM APIエラー**: LLM Adapter内でリトライ処理やエラー通知を行います。エラーは `error` タイプのチャンクとしてストリーミングされます。
-   **ツール実行エラー**: `_execute_tool_and_get_response` 内でキャッチされ、エラー情報を含む `tool_response` (または専用のエラーチャンク) がLLMに返されるか、`error` チャンクとしてストリーミングされます。LLMはエラー情報に基づいて次の行動を決定できます。
-   **設定エラー**: 初期化時の設定不備（例: 不明なモデル名）は、エージェント開始前に検知されます。
-   **ハンドオフエラー**: 最大深度超過などのエラーは `handoff` メソッドで処理され、`error` チャンクとして通知されます。
-   **タイムアウト**: 長時間応答がない場合やツール実行が長すぎる場合に備え、適切なタイムアウト機構をLLM AdapterやTool Registryレベルで設ける必要があります。

## 8. 未実装・要検討事項

-   `LLMAdapter`, `ToolRegistry`, `Guardrail`, `TraceLogger` の具体的な実装。
-   長期記憶の実装方法（ベクトルDB連携など）。
-   より高度なハンドオフ戦略と循環ハンドオフの堅牢な防止策。
-   非同期処理におけるリソース管理とキャンセル処理。
-   設定ファイルによるエージェント構成の外部化。
-   詳細なテスト戦略。
-   `AgentSDK.md` との整合性確保と、SSEチャンク仕様の最終化。

---
*このドキュメントは `base_agent.py` のコードと一般的なエージェント設計に基づいて作成されました。*
