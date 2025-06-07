# **独自エージェント・フレームワーク詳細仕様書 v1.1**

（SDK 依存なし／Python 3.11 — Kortix-AI Suna をベースに機能分割を明文化）

---

## 目次

1. 目的とスコープ
2. 全体アーキテクチャ
3. コアレイヤ：クラス定義と責務
   3-1. `BaseAgent`
   3-2. `Tool` & `ToolRegistry`
   3-3. `LLMAdapter`
   3-4. `Guardrail` & `TokenGuard`
   3-5. `Router`
   3-6. `TraceLogger`
4. ドメインレイヤ：SmartAO 専用エージェント
5. 通信・ストリーミング仕様
6. 非同期処理とスレッドセーフ設計
7. エラー／リトライ／フォールバック戦略
8. テスト指針
9. 拡張ポイント一覧
10. 付録 A – 型定義（pydantic）
    付録 B – 時系列シーケンス図完全版
    付録 C – トレース JSONL サンプル

---

## 1. 目的とスコープ

* **SDK ロックインを避け**、LLM／Tool／メモリ層を自由に交換できる。
* **ストリーミング**・**ハンドオフ**・**ツール並列**を標準サポート。
* Suna の実装で採られている「Adapter + Registry + Trace」構造を踏襲しつつ、
  AO 向けワークロード（Rubric 評価・大量パッチ・コスト制御）を前提とした拡張を加える。

---

## 2. 全体アーキテクチャ

```
App (FastAPI)
 ├─ AgentRouter   ← リクエストを Coordinator.stream() へ
 └─ HTTP SSE Out  ← Chunk をそのまま転送
Core Layer
 ├─ BaseAgent        抽象ライフサイクル実装
 │   ├─ Router       子 Agent / Tool call の選択
 │   ├─ ToolRegistry Tool メタ情報管理
 │   ├─ Guardrail    I/O 検証
 │   ├─ LLMAdapter   OpenAI / Anthropic… 各実装
 │   └─ TraceLogger  JSONL / OTLP
 └─ Memory Store     短期 (deque) / 長期 (pgvector)
Domain Layer
 ├─ CoordinatorAgent
 ├─ DraftAgent
 ├─ StyleAgent
 ├─ RefAgent
 ├─ GuardAgent
 └─ EvalAgent (handoff)
```

---

## 3. コアレイヤ詳細

### 3-1. `BaseAgent`

| カテゴリ               | 詳細説明                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **コンストラクタ**        | ①名前とプロンプトは必須。②`tools` は `Tool` か関数（自動ラップ）を渡す。<br>③`extra_cfg` は dict を丸ごと保存し、DB コネクションなど外部依存を注入に使う。                                                                                                                                                                                                                                                                                        |
| **内部状態**           | *immutable* 属性… `name`, `instructions`<br>*runtime mutable*… `model`, `_handoff_depth`, `_memory`                                                                                                                                                                                                                                                                                          |
| **run()/stream()** | *run* は `.stream()` を内部で起動して全チャンクを結合。<br>*stream* は以下 6 段階を `async for` で実行：<br>1. `_preprocess_messages`<br>2. `LLMAdapter.chat(stream=True)` で delta / tool\_call を取得<br>3. delta → `Chunk` 化→ yield<br>4. tool\_call → `_choose_tool` → `_execute_tool` → `Tool` 戻り値を LLM へ返送<br>5. LLM が `assistant` 完了を返したら `_postprocess_response`<br>6. `_trace_logger.trace(\"agent_end\", usage)` |
| **並列実行**           | 同一ターンで複数 tool\_call が入れ子になる場合、`asyncio.TaskGroup` で gather。                                                                                                                                                                                                                                                                                                                                |
| **ハンドオフ**          | - `self._handoff_depth` をインクリメントし `MAX=3` を超えたら例外<br>- ハンドオフ先の stream に `yield from` し、`\"agent\": target.name` に置換<br>- 手戻り時は `on_handoff_return()`（必要なら override）                                                                                                                                                                                                                        |
| **トークン計算**         | デフォルト実装：`LLMAdapter.count_tokens(system+messages)` + tool I/O。<br>TokenGuard 呼び出しは `_execute_tool` 内で行う。                                                                                                                                                                                                                                                                                   |

### 3-2. `Tool` & `ToolRegistry`

* **Tool** は **不変オブジェクト**。coro は引数を **pydantic BaseModel** にキャスト後呼ぶ。
* `ToolRegistry` は `LoadedTool` (namedtuple `(tool, schema_json)`) を LRU (size=256) キャッシュ。
* 発番は `registry.get_prompt_stub()` が `"\"name\": {\"type\":\"object\", ...}"` を返し LLM Prompt に挿入。

### 3-3. `LLMAdapter`

| メソッド                           | 詳細                                                                  |                            |
| ------------------------------ | ------------------------------------------------------------------- | -------------------------- |
| `chat(messages, stream, **kw)` | *stream=False* → dict<br>*stream=True* → AsyncIterator\[raw\_chunk] |                            |
| \`count\_tokens(text           | msgs)\`                                                             | tiktoken / 快速正規表現 fallback |
| `normalize_model_name()`       | OpenAI=snake\_case→`gpt-4o`、Anthropic=`claude-3-opus`               |                            |

失敗時は `LLMTimeoutError` or `LLMRateLimitError` を基地として raise。

### 3-4. `Guardrail`

```python
class Guardrail:
    def __init__(self, *, input_schema=None, output_schema=None,
                 regex_blocks=None, custom_funcs=None): ...
    async def validate_input(self, data): ...
    async def validate_output(self, data): ...
```

* `TokenGuard` は `Guardrail` のサブクラス。Redis カウンタでセッション累計を持つ。
* `action:"warn"` 時は Coordinator が Chat バブルに変換。`"block"` はツール実行前に即返却。

### 3-5. `Router`

* **RuleRouter**：`rules: list[(pattern:str, agents:list[str])]` を先勝。
* **LLMRouter**：軽量モデル (`o3-mini`) に `{"question": <user_text>, "agents": [...]}` を返させる。

  * JSON parse 失敗時は RuleRouter fallback。

### 3-6. `TraceLogger`

* イベント種別：`agent_start`, `tool_start`, `tool_end`, `handoff_start`, `handoff_end`, `agent_end`。
* JSONL フォーマット例（付録 C）。
* `OTLPExporter` は env `TRACE_OTLP_ENDPOINT` が設定されていれば gRPC Push。

---

## 4. ドメインレイヤ

| Agent           | 専用メソッド / 特記事項                                                                            |
| --------------- | ---------------------------------------------------------------------------------------- |
| **Coordinator** | `router: BaseRouter`、`merge_patches()`（Draft+Style を 1 つに）                               |
| **DraftAgent**  | プロンプトは “見出し維持ルール + 深掘り depth” を System に含める                                              |
| **StyleAgent**  | `grammar_check` → issue を `change_map` へ変換 (`util.patch_from_issues`)                    |
| **RefAgent**    | `vector_search` が pgvector fallback 時は `SELECT id, cos_sim(...) ORDER BY 2 DESC LIMIT k` |
| **GuardAgent**  | `plagiarism_check` 0.28–0.4 → warn, >0.4 → block                                         |
| **EvalAgent**   | Rubric JSON をキャッシュ。`apply_reflexion` は Celery Beat で夜間一括。                                |

---

## 5. 通信仕様

### 5-1. SSE Chunk 定義

| key     | 必須 | 説明                       |              |                  |         |           |
| ------- | -- | ------------------------ | ------------ | ---------------- | ------- | --------- |
| `time`  | ✔  | ISO-8601                 |              |                  |         |           |
| `agent` | ✔  | 送信エージェント名                |              |                  |         |           |
| `type`  | ✔  | \`'delta'                | 'tool\_call' | 'tool\_response' | 'usage' | 'error'\` |
| `data`  | 可  | ペイロード（構造化）               |              |                  |         |           |
| `seq`   | ✔  | uint64, monotonically 増加 |              |                  |         |           |

> フロントは `seq` ギャップ検出で再接続／リジュームを実装可能。

---

## 6. 非同期とスレッドセーフ

* LLM 呼び出しは I/O バウンド、Tool 内で CPU ヘビー処理がある場合は `run_in_executor`.
* Tool 実行で DB への write が必要な場合、`asyncpg` + 1 connection / Agent を持つ。
* `TraceLogger` は `anyio.aiofiles`で async write、OTLP Export は background TaskGroup。

---

## 7. エラー＆フォールバック詳細

| 原因                   | 自動処理                                         | エージェント実装者が行うこと       |
| -------------------- | -------------------------------------------- | -------------------- |
| LLM 408 / 502        | ① same-model retry (3) → ② fallback\_model へ | fallback 未設定時のハンドリング |
| GuardrailViolation   | Coordinator が `type:error` chunk 作成          | ユーザ向けエラーメッセージ整形      |
| ToolValidationError  | 自動で error chunk & trace                      | ツール戻り値のスキーマ修正        |
| HandoffDepthExceeded | Coordinator abort                            | 再帰ルーティングバグの修正        |

---

## 8. テスト指針

| レイヤ             | 目的                  | 使用ヘルパ                                 |
| --------------- | ------------------- | ------------------------------------- |
| Unit (Tool)     | スキーマ整合／副作用          | `pytest`, `pydantic.parse_obj_as`     |
| Unit (Agent)    | Router → Tool 呼び出し順 | `FakeLLM`, `FakeTool`                 |
| Integration API | SSE 順序／差分           | `httpx.AsyncClient`, `pytest-asyncio` |
| Load            | 同時 100 セッション        | `locust` with SSE plugin              |
| Trace           | ロギング完全性             | Snapshot test vs golden JSONL         |

---

## 9. 拡張ポイント

1. **Prompt Library**：`core/prompt.py` にテンプレ ID → テキストを登録し i18n。
2. **Plugin Loader**：`entrypoints` 経由で外部パッケージが Tool を自動登録。
3. **Memory Router**：チャット履歴を長期メモリ検索で LLM に渡す（ReAct スタイル）。

---

## 10. 付録

### 付録 A – 型定義抜粋（Draft）

```python
class ChangeOp(str, Enum):
    insert = "insert"
    delete = "delete"
    replace = "replace"

class Change(BaseModel):
    op: ChangeOp
    start: int
    end: int
    text: str | None = None

class PatchJSON(BaseModel):
    new_text: str
    change_map: list[Change]
```

### 付録 B – フルシーケンス図

（肉付け＋Rubric 評価＋Warn トークン超過）
*図は省略。*

### 付録 C – Trace 1 行サンプル

```json
{"event":"tool_end","time":"2025-05-23T04:14:33.892Z",
 "session":"f3a…","agent":"DraftAgent","tool":"generate_draft",
 "tok_prompt":812,"tok_completion":74,"duration_ms":940,
 "result":{"new_text":"...", "change_map":[...]}}
```

---

これで **SDK に依存しない完全自前フレームワーク**の詳細仕様を網羅しました。
クラス階層やストリーミング仕様など、どの部分をコード化する段階でも参照できます。
さらに具体的な API シグネチャやサンプル実装が必要な場合はお知らせください！
