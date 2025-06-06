# MONONO Agent LLM アダプター利用ガイド

# MONONO Agent 使い方ガイド

MONONO Agent フレームワークの主要コンポーネントと基本的な利用手順をまとめた概要です。以下のステップで開始してください。

## 0. セットアップ
1. リポジトリをクローンし、依存パッケージをインストール:
   ```bash
   git clone <repo-url>
   cd react_ai_chatapp/backend/app/services/agents/monono_agent
   pip install -r requirements.txt
   ```
2. 必要な API キーを環境変数に設定:
   ```bash
   export OPENAI_API_KEY=your_openai_key
   export ANTHROPIC_API_KEY=your_anthropic_key
   ```

## 1. BaseAgent の初期化
LLM Adapter や各種コンポーネントを注入して `BaseAgent` を生成します。
```python
from monono_agent.base_agent import BaseAgent
# 例: OpenAIAdapter を用意済み
agent = BaseAgent(
    name="MyAgent",
    instructions="あなたは親切なアシスタントです。",
    llm_adapter=openai_adapter,
    tools=[simple_calculator, get_current_weather],   # 任意のツール登録
    guardrail=my_guardrail,                          # 入力/出力ガード
    context_manager=ContextManager(),                # 対話コンテキスト
    planning_engine=PlanningEngine(),                # プランニングエンジン
    workflow_engine=WorkflowEngine(),                # ワークフローエンジン
    resource_manager=ResourceManager(),              # リソース管理
    learning_engine=LearningEngine(),                # 学習エンジン
    error_recovery_manager=ErrorRecoveryManager(),    # エラー回復
    multi_modal_processor=MultiModalProcessor(),      # マルチモーダル
    security_manager=SecurityManager(),              # セキュリティ管理
    performance_optimizer=PerformanceOptimizer(),    # 性能最適化
    collaboration_manager=CollaborationManager()     # 協調管理
)
```

## 2. 対話の実行
- 非同期ストリーミング応答:
```python
async for chunk in agent.stream(messages=[{"role":"user","content":"こんにちは"}], session_id=session_id):
    print(chunk)
```
- 一括実行して最終結果取得:
```python
response = await agent.run(messages=[{"role":"user","content":"こんにちは"}], session_id=session_id)
print(response)
```

## 3. 主なコンポーネント利用例
- **LLM Adapter**: `llm_adapter` パラメータで注入。
- **ツール**: `tools` リストに関数を渡して登録。
- **Guardrail**: `guardrail` パラメータで入力/出力/ツール実行を保護。
- **ContextManager**: 対話履歴を自動管理し、プロンプトに注入。
- **PlanningEngine**: 複雑タスクをサブタスク化・実行。
- **WorkflowEngine**: 定義済みワークフローを順次/並列実行。
- **ResourceManager**: APIクォータやコストを監視・制御。
- **LearningEngine**: 成功/失敗パターンを学習して改善。
- **ErrorRecoveryManager**: リトライ、フォールバック、サーキットブレーカー。
- **MultiModalProcessor**: 画像・音声・動画の処理。
- **SecurityManager**: PIIマスキング、アクセス制御、監査ログ。
- **PerformanceOptimizer**: キャッシュ管理、ツール選択最適化。
- **CollaborationManager**: セッション共有、タスク委譲、結果統合。

詳細は以下セクションを参照してください。

## 3. コンポーネント詳細

### 3.1. LLM Adapter
- 注入方法: `BaseAgent(llm_adapter=your_adapter)`
- 主なメソッド:
  - `await adapter.chat_completion(messages, stream=True, model=...)`: 非同期ストリーミング応答取得
  - `adapter.parse_llm_response_chunk(raw_chunk)`: 生チャンクを共通形式に変換
  - `adapter.get_latest_usage()`: 最終トークン使用量を取得
- サンプル:
  ```python
  response_stream = await agent.llm_adapter.chat_completion(
      messages=[{'role':'user','content':'こんにちは'}],
      stream=True,
      model='gpt-4o'
  )
  async for chunk in response_stream:
      print(chunk)
  ```

### 3.2. ToolRegistry
- ツール登録: `agent.tool_registry.register_tool(your_function)` または `BaseAgent(tools=[...])`
- 引数検証: `tool_registry.parse_arguments(tool_name, json_args)`
- 定義取得: `tool_registry.get_tool_definitions()` を `llm_kwargs['tools']` に渡す
- 実行: `tool_registry.execute_tool(tool_name, parsed_args)`

### 3.3. Guardrail
- 注入方法: `BaseAgent(guardrail=your_guardrail)`
- 主なメソッド:
  - `await guardrail.check_input(messages, ...)`：入力検証
  - `await guardrail.check_output(chunk, ...)`：出力検証
  - `await guardrail.can_execute_tool(tool_name, args, ...)`：ツール実行許可チェック
- ガードレール違反時は `GuardrailViolationError` を発生

### 3.4. ContextManager
- 対話履歴とユーザー情報を管理
- `update_context(session_id, data)` で履歴登録
- `get_relevant_context(query, session_id, user_id)` で関連情報文字列取得

### 3.5. PlanningEngine
- 複雑タスク分解用エンジン
- `plan = await engine.create_plan(messages, session_id)`
- `result = await engine.execute_sub_task(task, agent, session_id)`

### 3.6. WorkflowEngine
- 定義済みワークフロー実行
- `await engine.execute_workflow(workflow_def, agent, initial_data, session_id)`

### 3.7. ResourceManager
- APIクォータ・コスト管理
- `can_execute(tool_name, estimated_cost, resources)` で実行可否
- `track_usage(component, usage_data)` で使用量記録

### 3.8. LearningEngine
- 実行パターン学習・改善
- `track_success_patterns(desc, details, was_successful, feedback)`
- `suggest_improvements(failed_context)`
- `personalize_responses(user_id, history, prefs)`

### 3.9. ErrorRecoveryManager
- エラー回復・リトライ・フォールバック
- `await manager.handle_failure(error, context, agent)`

### 3.10. MultiModalProcessor
- 画像／音声／動画処理
- `await mmp.process_image(data, task_type)`
- `await mmp.process_audio(data, task_type)`
- `await mmp.process_video(data, task_type)`

### 3.11. SecurityManager
- PII サニタイズ: `sanitize_data(data)`
- 権限チェック: `check_permissions(user, action, resource)`
- 監査ログ: `log_audit_event(event)`

### 3.12. PerformanceOptimizer
- キャッシュ・最適ツール選択
- `await optimizer.get_or_set_cache(key, func, ttl)`
- `await optimizer.optimize_tool_selection(desc, tools_meta)`

### 3.13. CollaborationManager
- セッション共有: `await collab.share_session_with_users(session_id, user_ids)`
- タスク委譲: `await collab.delegate_task_to_human(details, reason, role)`
- 結果統合: `await collab.merge_agent_outputs(results, strategy)`

## `BaseAgent` における LLM アダプターの切り替え

`BaseAgent` は、使用する LLM プロバイダーを柔軟に選択できるように設計されています。これは、`BaseAgent` の初期化時に、特定の LLM アダプターのインスタンスを `llm_adapter` パラメータに渡すことで実現されます。

### コアコンセプト: 依存性の注入 (Dependency Injection)

このエージェントフレームワークは、依存性の注入という手法を採用しています。`BaseAgent` 自身が特定の LLM クライアントを作成するのではなく、事前に設定されたアダプターインスタンスを提供します。これにより、`BaseAgent` は具体的な LLM の実装詳細から独立します。

### 利用可能なアダプター

現在、以下のアダプターが実装されています。

*   `OpenAIAdapter`: OpenAI モデル (例: GPT-4o, GPT-3.5-turbo) との対話用。
*   `AnthropicAdapter`: Anthropic モデル (例: Claude 3 Opus, Claude 3 Sonnet) との対話用。

## 利用方法

以下に、OpenAI または Anthropic アダプターを使用して `BaseAgent` を初期化する例を示します。

### 1. OpenAI アダプターの使用

OpenAI モデルを使用するには、`OpenAIAdapter` のインスタンスを作成し、それを `BaseAgent` に渡します。

```python
from backend.app.services.agents.monono_agent.base_agent import BaseAgent
from backend.app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter

# ステップ1: OpenAIAdapter インスタンスの設定と作成
# OpenAI API キーが利用可能であることを確認してください。
openai_api_key = "YOUR_OPENAI_API_KEY"  # 実際のキーに置き換えるか、環境変数から読み込みます
openai_adapter = OpenAIAdapter(
    model_name="gpt-4o",  # または他の OpenAI モデル
    api_key=openai_api_key
)

# ステップ2: OpenAIAdapter を使用して BaseAgent を初期化
my_openai_agent = BaseAgent(
    name="MyOpenAIPoweredAgent",
    instructions="あなたは OpenAI を利用した親切なアシスタントです。",
    llm_adapter=openai_adapter,  # 設定済みのアダプターを注入
    # ... その他の BaseAgent パラメータ (ツールなど)
)

# これで `my_openai_agent` は LLM 対話に OpenAI API を使用します。
# 利用例 (概念):
# async for response_chunk in my_openai_agent.stream(messages=[{"role": "user", "content": "こんにちは OpenAI!"}]):
#     print(response_chunk)
```

### 2. Anthropic アダプターの使用

Anthropic モデルを使用するには、`AnthropicAdapter` のインスタンスを作成し、それを `BaseAgent` に渡します。

```python
from backend.app.services.agents.monono_agent.base_agent import BaseAgent
from backend.app.services.agents.monono_agent.llm_adapters.anthropic_adapter import AnthropicAdapter

# ステップ1: AnthropicAdapter インスタンスの設定と作成
# Anthropic API キーが利用可能であることを確認してください。
anthropic_api_key = "YOUR_ANTHROPIC_API_KEY"  # 実際のキーに置き換えるか、環境変数から読み込みます
anthropic_adapter = AnthropicAdapter(
    model_name="claude-3-opus-20240229",  # または他の Anthropic モデル
    api_key=anthropic_api_key
)

# ステップ2: AnthropicAdapter を使用して BaseAgent を初期化
my_anthropic_agent = BaseAgent(
    name="MyAnthropicPoweredAgent",
    instructions="あなたは Anthropic Claude を利用した親切なアシスタントです。",
    llm_adapter=anthropic_adapter,  # 設定済みのアダプターを注入
    # ... その他の BaseAgent パラメータ (ツールなど)
)

# これで `my_anthropic_agent` は LLM 対話に Anthropic API を使用します。
# 利用例 (概念):
# async for response_chunk in my_anthropic_agent.stream(messages=[{"role": "user", "content": "こんにちは Anthropic!"}]):
#     print(response_chunk)
```

## 3. ツールの利用

`BaseAgent` は、`ToolRegistry` を通じてカスタムツールを登録し、LLM の指示に基づいてそれらを実行する機能を提供します。これにより、エージェントは外部システムとの連携や、特定のデータ処理タスクを実行できます。

### 3.1. ツールの定義

ツールは Python の関数として定義します。関数の引数には型ヒントを付与することを推奨します。`ToolRegistry` はこれらの型ヒントを利用して、LLM が生成した引数のバリデーションを行うための Pydantic モデルを自動的に生成します。関数の docstring は、LLM に対してツールの説明として提供されます。

```python
# 例: 簡単な電卓ツール
def simple_calculator(expression: str) -> str:
    """
    簡単な算術式を評価して結果を返します。
    例: "2 + 2", "10 * 5 / 2"
    注意: eval() を使用するため、安全な入力のみを想定しています。
    Args:
        expression: 評価する算術式 (文字列)。
    Returns:
        評価結果 (文字列)、またはエラーメッセージ。
    """
    try:
        # 注意: eval() の使用はセキュリティリスクを伴うため、実際の運用ではより安全な評価方法を検討してください。
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

def get_current_weather(location: str, unit: str = "celsius") -> str:
    """
    指定された場所の現在の天気を取得します。
    Args:
        location: 天気を取得する都市名など (例: "Tokyo, JP")。
        unit: 温度の単位。"celsius" または "fahrenheit" を指定できます。デフォルトは "celsius"。
    Returns:
        天気の情報 (文字列)、またはエラーメッセージ。
    """
    # ここに実際の天気API呼び出しなどのロジックを実装
    if location.lower() == "tokyo, jp":
        if unit == "celsius":
            return "東京の天気は晴れ、25℃です。"
        else:
            return "東京の天気は晴れ、77°Fです。"
    return f"{location}の天気情報は見つかりませんでした。"

```

### 3.2. ツールの登録とエージェントの初期化

定義したツールは、`BaseAgent` の初期化時に `tools` パラメータに関数のリストとして渡すことで登録されます。`BaseAgent` 内部で `ToolRegistry` がこれらの関数を処理し、LLM が利用できる形式に変換します。

```python
from backend.app.services.agents.monono_agent.base_agent import BaseAgent
from backend.app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter # 例としてOpenAIを使用

# (上記で定義した simple_calculator と get_current_weather 関数があるとする)

# LLMアダプターの準備 (前述の通り)
openai_api_key = "YOUR_OPENAI_API_KEY"
openai_adapter = OpenAIAdapter(model_name="gpt-4o", api_key=openai_api_key)

# ツールリストの準備
my_tools = [simple_calculator, get_current_weather]

# ツールを登録して BaseAgent を初期化
calculator_agent = BaseAgent(
    name="CalculatorAndWeatherAgent",
    instructions="あなたは計算や天気予報が得意なアシスタントです。必要に応じてツールを呼び出してください。",
    llm_adapter=openai_adapter,
    tools=my_tools  # 定義したツールのリストを渡す
)

# これで `calculator_agent` は LLM からの指示に基づき、
# `simple_calculator` や `get_current_weather` を実行できます。
```

### 3.3. エージェントによるツールの呼び出しフロー (概念)

1.  ユーザーがエージェントにタスクを指示します (例: 「東京の天気を教えて」)。
2.  エージェント (`BaseAgent`) は、LLM (例: GPT-4o) に対し、ユーザーの指示と登録されているツールの情報 (名前、説明、パラメータスキーマ) を渡します。
3.  LLM は、ユーザーの指示を達成するためにツールが必要だと判断した場合、特定のツール (例: `get_current_weather`) を、必要な引数 (例: `{"location": "Tokyo, JP", "unit": "celsius"}`) と共に呼び出すよう指示します。
4.  `BaseAgent` はこの指示を受け取り、`ToolRegistry` を介して指定されたツール (`get_current_weather`) を対応する引数で実行します。
5.  ツールの実行結果が `BaseAgent` に返されます。
6.  `BaseAgent` は、ツールの実行結果を LLM に渡し、最終的なユーザーへの応答を生成するよう促します。
7.  LLM はツールの結果を踏まえて、ユーザーへの最終的な応答 (例: 「東京の天気は晴れ、25℃です。」) を生成します。
8.  この応答がユーザーに返されます。

このプロセスは、エージェントがより複雑なタスクや情報取得を自律的に行うことを可能にします。詳細なツール呼び出しのシーケンスやエラーハンドリングは `BaseAgent` 内部で処理されます。

## 4. Guardrail の利用

`BaseAgent` は、エージェントの**入力**、**出力**、および**ツール実行**の各ポイントで Guardrail メソッドを呼び出し、安全性と信頼性を担保します。

1. **入力検証 (`check_input`)**  
   - `stream` メソッド開始時に呼び出され、LLM に渡す前のメッセージを検証・修正します。  
   - 例: 有害ワードを検知して例外を投げる、機密情報をマスキングする。

2. **出力検証 (`check_output`)**  
   - ストリーミングで LLM の応答チャンクを受信するたびに呼び出され、ユーザーへ送信する前に各チャンクを検証・修正します。  
   - 例: 不適切表現のマスキング、プライバシー情報の削除。

3. **ツール実行制御 (`can_execute_tool`)**  
   - `_execute_tool_and_get_response` 内でツールを実行する直前に呼び出され、ツール名と引数を受け取り、その実行を許可 (`True`) するか否 (`False`) を判断します。  
   - `False` の場合は `GuardrailViolationError` を投げて処理を中断します。

```python
# Guardrail を指定して BaseAgent を初期化
from backend.app.services.agents.monono_agent.base_agent import BaseAgent
from backend.app.services.agents.monono_agent.components.guardrail import MyCustomGuardrail
from backend.app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter

guardrail = MyCustomGuardrail(config={"restricted_tools": ["dangerous_tool"]})
openai_adapter = OpenAIAdapter(model_name="gpt-4o", api_key="YOUR_API_KEY")
agent = BaseAgent(
    name="SecureAgent",
    instructions="安全第一のアシスタントです。",
    llm_adapter=openai_adapter,
    guardrail=guardrail,
)
```

### 呼び出しタイミング

- **`check_input`**: `await guardrail.check_input(messages, agent_name=..., session_id=..., user_id=...)`  
- **`check_output`**: `await guardrail.check_output(chunk, agent_name=..., session_id=..., user_id=...)`  
- **`can_execute_tool`**: `await guardrail.can_execute_tool(tool_name, tool_args, agent_name=..., session_id=..., user_id=..., tool_registry=...)`

### エラー時の挙動

- `GuardrailViolationError` が発生すると、`stream` では `error` タイプのチャンクとして中断、`run` では最終レスポンスに `error` フィールドが追加されます。

## 5. TraceLogger の利用

`TraceLogger` は、エージェントの処理ステップや内部状態、エラーなどをログとして記録するためのコンポーネントです。デバッグやモニタリング、監査追跡などの目的で使用できます。

### 5.1. 基本的な使用方法

`TraceLogger` はデフォルトで `BaseAgent` に組み込まれており、特別な設定なしで基本的なログ記録が可能です。

```python
from backend.app.services.agents.monono_agent.base_agent import BaseAgent
from backend.app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter

openai_adapter = OpenAIAdapter(model_name="gpt-4o", api_key="YOUR_API_KEY")
agent = BaseAgent(
    name="MyAgent",
    instructions="手助けを行うアシスタントです。",
    llm_adapter=openai_adapter
    # trace_logger パラメータを省略すると、デフォルトのTraceLoggerが使用されます
)

# エージェントの実行時に自動的にログが記録されます
```

### 5.2. カスタムロガーの設定

特定のログレベルやフォーマット、出力先を持つカスタムロガーを使用することも可能です。

```python
import logging
from backend.app.services.agents.monono_agent.base_agent import BaseAgent
from backend.app.services.agents.monono_agent.components.trace_logger import TraceLogger
from backend.app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter

# カスタムロガーの設定
custom_logger = logging.getLogger("my_custom_trace")
handler = logging.FileHandler("agent_traces.log")
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
custom_logger.addHandler(handler)
custom_logger.setLevel(logging.DEBUG)  # より詳細なログレベル

# カスタムTraceLoggerの作成
trace_logger = TraceLogger(logger=custom_logger)

# カスタムTraceLoggerを使用してBaseAgentを初期化
openai_adapter = OpenAIAdapter(model_name="gpt-4o", api_key="YOUR_API_KEY")
agent = BaseAgent(
    name="MyAgent",
    instructions="手助けを行うアシスタントです。",
    llm_adapter=openai_adapter,
    trace_logger=trace_logger  # カスタムTraceLoggerを指定
)
```

### 5.3. 手動でのトレースの記録

`TraceLogger` は `BaseAgent` の内部処理で自動的に呼び出されますが、必要に応じて手動でトレースを記録することもできます。

```python
# BaseAgentのインスタンスからTraceLoggerにアクセス
agent.trace_logger.trace("custom_event", {"detail": "重要な情報", "value": 42})

# または直接TraceLoggerを使用
from backend.app.services.agents.monono_agent.components.trace_logger import TraceLogger

logger = TraceLogger()
logger.trace("app_startup", {"version": "1.0.0", "environment": "production"})
```

### 5.4. 重要なトレースイベント

`BaseAgent` は以下のような重要なポイントでトレースイベントを記録します：

- **run_start / stream_start**: エージェントの実行/ストリーム開始時
- **llm_request_start**: LLMへのリクエスト開始時
- **parsed_chunk**: LLMからの応答チャンク処理時
- **tool_execution_start**: ツール実行開始時
- **stream_end / run_end**: エージェントの実行/ストリーム終了時

これらのイベントを監視することで、エージェントの動作フローや性能特性を把握できます。

## 6. 学習 & 適応エンジン (Learning & Adaptation Engine) の利用

`LearningEngine` を利用することで、過去の実行パターンを学習し、失敗からの改善案作成やユーザー応答のパーソナライズが可能になります。以下のようにインポートして使用します。

```python
from backend.app.services.agents.monono_agent.components.learning_engine import LearningEngine

# インスタンス生成
learning_engine = LearningEngine()

# タスク実行結果の記録
learning_engine.track_success_patterns(
    task_description="データ解析",
    approach_details={"method": "統計モデル"},
    was_successful=False,
    user_feedback="精度が低かった"
)

# 失敗からの改善提案を取得
improvement = learning_engine.suggest_improvements({"task_description": "データ解析"})
print(improvement)
# => タスク「データ解析」の失敗を踏まえ、アプローチ {'method': '統計モデル'} の代替手法を検討してください。プロンプトの再構成や別のツールの使用をお勧めします。

# ユーザー応答パーソナライズ設定
prefs = {"tone": "friendly", "verbosity": "concise"}
personalization = learning_engine.personalize_responses(
    "user123",
    interaction_history=[],
    preferences=prefs
)
print(personalization)
# => {'tone': 'friendly', 'verbosity': 'concise'}
```

## 7. エラー回復 & レジリエンスマネージャ (Error Recovery & Resilience Manager) の利用

`ErrorRecoveryManager` は、ツール実行やAPI呼び出しなど、外部サービスとの連携時に発生するエラーに対して、自動的に回復処理を試みるコンポーネントです。このマネージャーは以下の3つの主要な回復メカニズムを提供します：

1. **リトライ機能**: 一時的な障害に対して、指定回数・間隔で自動的に再試行
2. **フォールバック戦略**: 特定のツールが失敗した場合に代替ツールを使用
3. **サーキットブレーカー**: 障害が頻発するコンポーネントへのアクセスを一時的に遮断し、連鎖的な障害を防止

### 7.1. 基本的な設定と初期化

```python
from backend.app.services.agents.monono_agent.components.error_recovery_manager import ErrorRecoveryManager

# デフォルト設定でマネージャーを初期化
error_mgr = ErrorRecoveryManager()

# BaseAgent初期化時に注入
agent = BaseAgent(
    name="ResilientAgent",
    instructions="障害に強いエージェントです",
    llm_adapter=openai_adapter,
    error_recovery_manager=error_mgr
)
```

### 7.2. リトライポリシーの設定

リトライポリシーは、コンポーネント（ツール名）ごとに最大試行回数と再試行間隔を指定できます。

```python
# カスタムリトライポリシーを設定
error_mgr = ErrorRecoveryManager(
    retry_policies={
        "default": {"max_attempts": 3, "delay": 1.0},  # デフォルト: 3回まで1秒間隔
        "api_call_tool": {"max_attempts": 5, "delay": 2.0},  # API呼び出しは5回まで2秒間隔
        "db_query_tool": {"max_attempts": 2, "delay": 0.5}   # DB問い合わせは2回まで0.5秒間隔
    }
)
```

| パラメータ | 説明 | 単位 | 推奨値 |
|----------|-----|------|--------|
| `max_attempts` | 最大試行回数（初回実行を除く） | 回数 | 2-5 |
| `delay` | リトライ間の待機時間 | 秒 | 0.5-3.0 |

### 7.3. フォールバック戦略の設定

フォールバック戦略は、特定のツールが失敗した場合に、代替のツールを自動的に呼び出す仕組みです。

```python
# フォールバック戦略を設定
error_mgr = ErrorRecoveryManager(
    fallback_strategies={
        "primary_weather_api": "backup_weather_api",  # 主要天気APIが失敗したら予備APIを使用
        "google_search_tool": "bing_search_tool",     # Google検索が失敗したらBing検索へ
        "gpt4_tool": "gpt35_tool"                     # GPT-4が応答しない場合GPT-3.5へ
    }
)
```

フォールバック時、引数は元のツール呼び出しと同じものが使用されるため、互換性のあるツール間で設定することが重要です。

### 7.4. サーキットブレーカーの設定

サーキットブレーカーは、特定のサービスへの呼び出しが繰り返し失敗する場合に、一時的にそのサービスへのアクセスを遮断し、システム全体のパフォーマンス低下を防ぎます。

```python
# サーキットブレーカーを設定
error_mgr = ErrorRecoveryManager(
    circuit_breakers={
        "unstable_service": {
            "failure_count": 0,           # 現在の失敗カウント
            "failure_threshold": 5,       # このカウントを超えるとブレーカーが開く
            "is_open": False              # ブレーカーの状態（Falseは閉じている＝通常状態）
        },
        "external_api": {
            "failure_count": 0,
            "failure_threshold": 3,
            "is_open": False
        }
    }
)
```

| パラメータ | 説明 | 推奨値 |
|----------|-----|--------|
| `failure_threshold` | ブレーカーが開くまでの連続失敗回数 | 3-10 |
| `is_open` | 初期状態では通常False | False |
| `failure_count` | 初期値は通常0 | 0 |

### 7.5. 全機能を組み合わせた例

```python
# 全ての回復メカニズムを組み合わせた設定
error_mgr = ErrorRecoveryManager(
    # リトライポリシー
    retry_policies={
        "default": {"max_attempts": 2, "delay": 1.0},
        "weather_api": {"max_attempts": 3, "delay": 2.0}
    },
    # フォールバック戦略
    fallback_strategies={
        "primary_search": "backup_search",
        "weather_api": "local_weather_cache"
    },
    # サーキットブレーカー
    circuit_breakers={
        "weather_api": {"failure_count": 0, "failure_threshold": 5, "is_open": False}
    }
)

# BaseAgentに注入
agent = BaseAgent(
    name="HighlyResilientAgent",
    instructions="複数の回復メカニズムを備えたエージェントです",
    llm_adapter=openai_adapter,
    error_recovery_manager=error_mgr
)
```

エージェント実行中にツール呼び出しでエラーが発生すると、以下の順序で回復処理が試みられます：

1. まずリトライポリシーに基づき再試行
2. リトライでも失敗した場合、フォールバック戦略に基づき代替ツールを実行
3. 失敗が続く場合、サーキットブレーカーのカウンターが増加し、閾値を超えるとそのコンポーネントへのアクセスをブロック

これにより、エージェントは一時的な障害に対して堅牢に動作し、システム全体の安定性が向上します。

## 8. Planning & Task Decomposition Engine の利用

### 8.1. 概要
- `PlanningEngine` は、複雑なユーザー指示をサブタスクに分解し、依存関係を解決しながら順序に沿って実行できるコンポーネントです。

### 8.2. 初期化例
```python
from backend.app.services.agents.monono_agent.llm_adapters.openai_adapter import OpenAIAdapter
from backend.app.services.agents.monono_agent.components.planning_engine import PlanningEngine

# LLM アダプターを用意
openai_adapter = OpenAIAdapter(model_name="gpt-4o", api_key="YOUR_API_KEY")

# PlanningEngine を初期化
engine = PlanningEngine(llm_adapter=openai_adapter, model="gpt-4o")
```

### 8.3. プラン生成 (`create_plan`)
```python
messages = [{"role": "user", "content": "ウェブサイトの更新手順を教えてください"}]
plan = await engine.create_plan(messages, session_id)
print(plan.json(indent=2))
```

### 8.4. サブタスク実行 (`execute_sub_task`)
```python
from backend.app.services.agents.monono_agent.base_agent import BaseAgent

# BaseAgent を用意（LLMAdapter やツール等を注入）
agent = BaseAgent(name="SubtaskAgent", instructions="サブタスク実行用エージェントです。", llm_adapter=openai_adapter)

# 生成されたプランの最初のタスクを実行
result = await engine.execute_sub_task(plan.tasks[0], agent, session_id)
print(result)
```

### 8.5. 一括実行 (`execute_plan`)
```python
execution = await engine.execute_plan(messages, agent, session_id)
# execution["plan"]: Plan オブジェクト
# execution["results"]: {subtask_id: 実行結果} の辞書
```

### 8.6. 注意点
- サブタスク間の循環依存がある場合は実行が停止します。
- 実運用では、エラー処理やタイムアウト制御、ログ機能の強化を検討してください。

## 9. Context Manager の利用

### 9.1. 概要
- `ContextManager` は、セッションごとの会話履歴やユーザープロファイル、グローバルコンテキストを管理し、LLM プロンプトに関連情報を自動的に注入するコンポーネントです。

### 9.2. 初期化
```python
from backend.app.services.agents.monono_agent.components.context_manager import ContextManager

# コンテキストマネージャーを生成
cm = ContextManager()
```

### 9.3. コンテキストの更新 (`update_context`)
```python
# セッションIDと追加データを渡して履歴に登録
cm.update_context(session_id, {
    "user_id": user_id,                   # ユーザー固有情報を登録
    "global_context": {"foo": "bar"}, # グローバルコンテキストの追記
    "last_message": message               # 任意のキーで履歴を拡張
})
```

### 9.4. 関連コンテキストの取得 (`get_relevant_context`)
```python
# クエリに応じた関連情報を文字列で取得
ctx_str = cm.get_relevant_context(
    query="ユーザーの現在の質問の文字列",
    session_id=session_id,
    user_id=user_id
)
# LLM の system プロンプトとして注入可能
system_prompt = {"role":"system","content":f"Relevant context:\n{ctx_str}"}
```

### 9.5. BaseAgent との連携
- `BaseAgent` の `_preprocess_messages` 内で `get_relevant_context` を呼び出し、システムプロンプトに自動注入します。
- `_add_to_memory` 内でメモリ追加ごとに `update_context` を呼び出し、セッション履歴を追跡します。

## 10. Workflow Engine の利用

### 10.1. 概要
ワークフローエンジンは、事前に定義した一連のタスク（ステップ）を依存関係に従って順序実行したり、並列実行したりするためのコンポーネントです。

### 10.2. 初期化
`WorkflowEngine` 自体を直接使うか、`BaseAgent` 経由で利用できます。以下は直接初期化例です。
```python
from app.services.agents.monono_agent.components.workflow_engine import WorkflowEngine
from app.services.agents.monono_agent.base_agent import BaseAgent
# agent は既存の BaseAgent インスタンス
engine = WorkflowEngine()
```

### 10.3. ワークフロー定義
ワークフロー定義は JSON/YAML 相当の辞書で記述します。例：
```json
{
  "workflow": {
    "steps": [
      {"name": "step1", "tool": "tool_name1"},
      {"name": "step2", "tool": "tool_name2", "depends_on": ["step1"], "parallel": false},
      {"name": "step3", "tool": "tool_name3", "depends_on": ["step1"], "parallel": true}
    ]
  }
}
```
- `name`: ステップ識別子
- `tool`: `ToolRegistry` に登録済みのツール名
- `depends_on`: 先行タスクのリスト
- `parallel` (省略可): `true` で並列実行
- `condition` (省略可): 実行条件（デフォルト `"always"`）
- `parameters` (省略可): ツール実行時の追加パラメータ

### 10.4. ワークフローの実行
#### 10.4.1. 直接 `WorkflowEngine` 経由
```python
result = await engine.execute_workflow(
    workflow_definition=wf_def,
    agent=agent,
    initial_data={"foo": "bar"},
    session_id=None
)
print(result["results"])
```
#### 10.4.2. `BaseAgent` 経由
```python
# BaseAgent の execute_workflow メソッドを呼び出し
result = await agent.execute_workflow(
    workflow_definition=wf_def,
    initial_data={"foo": "bar"},
    session_id=None
)
print(result)
```

### 10.5. 注意点
- ツール名は必ず `ToolRegistry` に登録されている必要があります。
- ステップ間で同じ `session_id` を使うことで、メモリやガードレールが一貫して適用されます。
- サイクル依存がある場合、実行は停止します。
- 大規模ワークフローではリトライやタイムアウト制御を検討してください。

## 11. Resource Manager の利用

### 11.1. 概要
Resource Managerは、APIコール回数やツール実行コスト、LLMトークン使用量などのリソース消費を監視・管理し、設定された予算やクォータ内でエージェントが動作できるよう制御するコンポーネントです。

### 11.2. 初期化例
```python
from app.services.agents.monono_agent.components.resource_manager import ResourceManager
from app.services.agents.monono_agent.base_agent import BaseAgent

# 明示的にResourceManagerを生成して注入する例
rm = ResourceManager(
    api_quotas={"openai": {"limit": 1000, "used": 0}},
    cost_tracking={"budget": 5.0, "spent": 0.0},
    token_cost_per_token=0.00002  # USD／トークン
)

agent = BaseAgent(
    name="ResourceAgent",
    instructions="リソース管理テスト用エージェントです。",
    llm_adapter=None,
    resource_manager=rm,
    extra_cfg={"tool_costs": {"tool1": 0.5, "tool2": 1.0}}
)
```

### 11.3. BaseAgentとの連携
`BaseAgent` は以下のタイミングでResourceManagerを利用します。
- **ツール実行前**: `_execute_tool_and_get_response` 内で `can_execute(tool_name, estimated_cost)` を呼び、予算オーバー時には `ToolExecutionError` を発生させ処理を中断します。
- **ツール実行後**: `track_usage("tool:<tool_name>", {"cost": estimated_cost})` を呼び、消費コストを記録します。
- **LLM使用時**: `stream` メソッド内の `usage` チャンク受信時に `track_usage("llm", {"prompt_tokens": ..., "completion_tokens": ...})` を呼び、トークン使用量に応じたコストを追跡します。

### 11.4. 注意点
- `extra_cfg["tool_costs"]` でツールごとのコストを設定してください。
- `token_cost_per_token` は利用するLLMプロバイダーや契約プランに応じて調整可能です。
- CPU/メモリなどのコンピュートリソース制限は未実装のため、必要に応じて拡張してください。

## 12. マルチモーダルプロセッサ (Multi-modal Processor) の利用

`MultiModalProcessor` をエージェントに注入し、画像、音声、動画の処理機能を利用できます。以下は設定例です。

```python
from backend.app.services.agents.monono_agent.components.multi_modal_processor import MultiModalProcessor

# マルチモーダルプロセッサを生成
mm_processor = MultiModalProcessor()

# BaseAgent初期化時にmulti_modal_processorを指定
agent = BaseAgent(
    name="MMAgent",
    instructions="マルチモーダル対応エージェントです",
    llm_adapter=openai_adapter,
    multi_modal_processor=mm_processor
)

# 画像OCR
ocr_text = await agent.multi_modal_processor.process_image(
    "path/to/image.png", task_type="ocr"
)
print(ocr_text)

# 画像概要生成
description = await agent.multi_modal_processor.process_image(
    image_data_bytes, task_type="describe"
)
print(description)

# 画像生成
image_url = await agent.multi_modal_processor.process_image(
    None, task_type="generate"
)
print(image_url)

# 音声文字起こし
transcript = await agent.multi_modal_processor.process_audio(
    "path/to/audio.wav", task_type="transcribe"
)
print(transcript)

# 音声合成
audio_bytes = await agent.multi_modal_processor.process_audio(
    "こんにちは、今日はいい天気ですね。", task_type="synthesize"
)
# audio_bytes は WAV/MP3 データ

# 動画要約
summary = await agent.multi_modal_processor.process_video(
    "path/to/video.mp4", task_type="summarize"
)
print(summary)
```

## 13. セキュリティ & プライバシーマネージャ (Security & Privacy Manager) の利用

`SecurityManager` を利用すると、PII サニタイズ、アクセス制御、監査ログ機能をエージェントに統合できます。以下は設定例と各機能の詳細です。

```python
from backend.app.services.agents.monono_agent.components.security_manager import SecurityManager

# PII 検出用正規表現リスト例: メールアドレス、電話番号
pii_patterns = [r"[\w\.-]+@[\w\.-]+", r"\b\d{2,4}-\d{2,4}-\d{4}\b"]
# アクセス制御リスト例: ユーザーごとに許可された操作を定義
acl = {
    "user_admin": ["read", "write", "delete"],
    "user_viewer": ["read"]
}
# 監査ロガーを利用 (デフォルトで 'security_audit' ロガーを使用)
sec_mgr = SecurityManager(
    access_control_list=acl,
    pii_patterns=pii_patterns
)

# BaseAgent初期化時に注入
agent = BaseAgent(
    name="SecureAgent",
    instructions="機密データを扱う安全重視のエージェントです",
    llm_adapter=openai_adapter,
    security_manager=sec_mgr
)
```

### 13.1. PII サニタイズ (`sanitize_data`)
- data: str/dict/list を再帰的に処理
- パターンにマッチした部分を `[REDACTED]` に置換

```python
raw = "ユーザーのメール: user@example.com"
safe = agent.security_manager.sanitize_data(raw)
print(safe)  # => ユーザーのメール: [REDACTED]
```

### 13.2. アクセス制御 (`check_permissions`)
- access_control_list にルールがないユーザーはデフォルトで許可
- リソースID とアクションを渡して権限を判定

```python
if agent.security_manager.check_permissions("user_viewer", "write", "resource_123"):
    # 実行
else:
    # アクセス拒否
```

### 13.3. 監査ログ (`log_audit_event`)
- event_details を JSON 形式でログ出力 (INFO レベル)

```python
agent.security_manager.log_audit_event({
    "user": "user_admin",
    "action": "delete",
    "resource": "resource_123",
    "time": "2025-05-..."
})
```

エージェント内部で、たとえばツール呼び出し前後や実行結果後に手動で呼び出すことで、監査証跡を残せます。

```python
# ツール呼び出し前に権限チェックと監査
user = "user123"
if sec_mgr.check_permissions(user, "invoke_tool", "tool_xyz"):
    sec_mgr.log_audit_event({"user": user, "action": "invoke_tool", "tool": "tool_xyz"})
    # ツール実行...
else:
    raise PermissionError("ツール実行権限がありません。")
```

## 14. Collaboration Manager の利用

`CollaborationManager` を利用すると、複数のユーザーや他エージェント、人間専門家と協調してタスクを処理できます。以下は基本的な使い方です。

### 14.1. 初期化

```python
from backend.app.services.agents.monono_agent.components.collaboration_manager import CollaborationManager
from backend.app.services.agents.monono_agent.base_agent import BaseAgent

# LLMAdapter等の準備は省略
collab_mgr = CollaborationManager()
agent = BaseAgent(
    name="CollaborativeAgent",
    instructions="協調機能を持つエージェントです。",
    llm_adapter=openai_adapter,
    collaboration_manager=collab_mgr
)
```

### 14.2. セッション共有 (`share_session_with_users`)

指定したセッションIDを複数のユーザーに共有します。

```python
import uuid
session_id = uuid.uuid4()
user_ids = ["userA", "userB", "userC"]
await agent.collaboration_manager.share_session_with_users(session_id, user_ids)
```

### 14.3. 人間へのタスク委譲 (`delegate_task_to_human`)

タスクを人間専門家に委譲し、プレースホルダー応答を取得します。

```python
task_details = {"task": "複雑なデータ分析", "data": {...}}
reason = "自動分析では精度が不十分なため"
response = await agent.collaboration_manager.delegate_task_to_human(task_details, reason, human_expert_role="data_scientist")
print(response["response"])
```

### 14.4. 他エージェント結果の統合 (`merge_agent_outputs`)

複数のエージェント結果を指定戦略で統合します。

```python
results = ["A", "B", "A"]
merged = await agent.collaboration_manager.merge_agent_outputs(results, merge_strategy="majority_vote")
print(merged)  # "A"
```

サポートする `merge_strategy`:
- `majority_vote`: 最頻値
- `summation`: 数値の合計
- `average`: 数値の平均
- `llm_based_synthesis`: 文字列の連結
- その他: 最初の結果
