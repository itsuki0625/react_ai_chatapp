# 自己分析エージェント (AO入試対策版) — *LangChain Agent SDK Edition*

> **ステータス:** `alpha` — 旧 *monono_agent* SDK から **LangChain Agent SDK 0.2.x** および **LangGraph** へ移行しました。
> 公開APIは **実験的** であり、予告なく変更される可能性があります。

---

## 1 プロジェクト概要

このリポジトリは、日本の**AO入試（総合型選抜）**における強力な*志望理由書*作成に特化した**自動自己分析ワークフロー**を提供します。
現在、**LangChainエコシステム**を活用しています。

| レイヤー        | LangChainコンポーネント                                   | 目的                                                                 |
| --------------- | -------------------------------------------------------- | -------------------------------------------------------------------- |
| **LLM**         | `openai.ChatOpenAI` (`gpt-4o` デフォルト)                | コアとなる推論・生成処理                                               |
| **ツール**        | `langchain.tools.Tool` ラッパー                          | 内部ヘルパー (`note_store`, `list_notes` など)                       |
| **エージェント**    | `langchain.agents.create_openai_functions_agent`         | ツールを呼び出し可能な関数呼び出しエージェント                             |
| **プランナー**      | `langchain.experimental.plan_and_execute.PlanAndExecute` | 高レベルな目標を実行可能なツール呼び出しに分割                             |
| **メモリ**        | `ConversationBufferWindowMemory`                         | 最新*N*ターン (約10) の会話履歴を保持                                |
| **オーケストレーター** | **LangGraph** `StateGraph` 有向非巡回グラフ                | ステップ固有のエージェントを接続し、遷移ロジックを制御                      |
| **バリデーター**    | `GuardrailsValidator` (オプション)                       | JSONスキーマと個人情報フィルターを強制                                |
| **トレーシング**    | LangSmith                                                | 完全なイベントトレースとメトリクス                                        |

---

## 2 インストール

```bash
# 1. クローン
git clone https://github.com/your-org/self-analysis-agent.git
cd self-analysis-agent

# 2. 環境作成
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# 3. キー設定
export OPENAI_API_KEY=sk-...
# オプション
export LANGCHAIN_API_KEY=<langsmith-key>
```

> **Python ≥ 3.11** が必要です。

---

## 3 ステップフロー

教育的なフローは変更ありません。

```text
FUTURE (未来) → MOTIVATION (動機) → HISTORY (過去) → GAP (ギャップ) → VISION (ビジョン) → REFLECT (内省)
```

各**ステップ**はLangGraphのノードです。
ノードは`SelfAnalysisStepAgent`として実装されており、これはステップの目標に特化した`PlanAndExecute`エージェントエクゼキュータの薄いラッパーです。

| ステップ     | クラス名              | 責務                                                               | 次のステップ |
| ------------ | --------------------- | ------------------------------------------------------------------ | ------------ |
| FUTURE       | `FutureStepAgent`     | 未来のビジョンと主要な価値観を抽出                                        | MOTIVATION   |
| MOTIVATION   | `MotivationStepAgent` | 「なぜなぜ分析」による原体験の深掘り                                      | HISTORY      |
| HISTORY      | `HistoryStepAgent`    | 包括的なインタビューと**Markdownタイムライン**生成                       | GAP          |
| GAP          | `GapStepAgent`        | ギャップ、根本原因、優先順位の特定                                      | VISION       |
| VISION       | `VisionStepAgent`     | エッセイ用の一文ビジョンの作成                                          | REFLECT      |
| REFLECT      | `ReflectStepAgent`    | ミクロとマクロの内省                                                  | `None`       |

### 3.1 エージェントのスケルトン

`SelfAnalysisStepAgent` は、実際には各ステップファイル (`steps/future.py` など) で `utils/agent_builder.py` 内の `build_step_agent` ファクトリ関数を呼び出すことで構築されます。

```python
# utils/agent_builder.py の内容 (簡略化)
from langchain_experimental.plan_and_execute import PlanAndExecute
from langchain_experimental.plan_and_execute.planners.chat_planner import load_chat_planner
from langchain_experimental.plan_and_execute.executors.base import ChainExecutor
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import PromptTemplate
# from langchain.memory import ConversationBufferWindowMemory # PlanAndExecuteレベルで管理される場合

def build_step_agent(step_prompt: str, tools: list):
    # プロンプトテンプレートに会話履歴やセッションIDなどのコンテキストを追加
    template_content = f"""{step_prompt}

--- Agent向け追加コンテキスト ---
会話履歴 ('messages' として渡されます):
{{messages}}

セッションID ('session_id' として渡されます):
{{session_id}}

エージェントスクラッチパッド (エージェントの内部思考とツール使用のため):
{{agent_scratchpad}}
"""
    prompt = PromptTemplate(
        template=template_content,
        input_variables=["messages", "session_id", "agent_scratchpad"]
    )

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    func_agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
    
    # PlanAndExecute の内部 executor として使われる AgentExecutor
    agent_executor_for_chain = AgentExecutor(
        agent=func_agent,
        tools=tools,
        return_intermediate_steps=False,
        handle_parsing_errors=True,
    )
    
    planner = load_chat_planner(llm=llm)
    executor_for_plan_and_execute = ChainExecutor(chain=agent_executor_for_chain)

    return PlanAndExecute(planner=planner, executor=executor_for_plan_and_execute)

# steps/future.py での呼び出し例
# from ..utils.agent_builder import build_step_agent
# from ..tools import note_store, list_notes
# from ..prompts import FUTURE_PROMPT

# class FutureStepAgent:
#     def __init__(self):
#         self.agent = build_step_agent(FUTURE_PROMPT, [note_store, list_notes])

#     async def __call__(self, params: dict):
#         return await self.agent.ainvoke({"input": params})
```

---

## 4 グラフオーケストレーター

```python
# main.py より抜粋
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# ステートスキーマ定義
class SelfAnalysisState(TypedDict):
    messages: list
    session_id: str
    next_step: str | None

# Graphオーケストレーターの構築
builder = StateGraph(SelfAnalysisState)

builder.add_node("FUTURE", FutureStepAgent())
builder.add_node("MOTIVATION", MotivationStepAgent())
builder.add_node("HISTORY", HistoryStepAgent())
builder.add_node("GAP", GapStepAgent())
builder.add_node("VISION", VisionStepAgent())
builder.add_node("REFLECT", ReflectStepAgent())

# ノード間の順序付け
builder.add_edge(START, "FUTURE")
builder.add_edge("FUTURE", "MOTIVATION")
builder.add_edge("MOTIVATION", "HISTORY")
builder.add_edge("HISTORY", "GAP")
# builder.add_edge("GAP", "VISION") # 条件分岐で処理されるためコメントアウト
builder.add_edge("VISION", "REFLECT")
builder.add_edge("REFLECT", END)

# GAPからの条件分岐
builder.add_conditional_edges(
    "GAP",
    # stateからgapsの有無を確認して分岐 (実際のロジックに合わせて調整)
    condition=lambda state: "REFLECT" if not state.get("messages", [{}])[-1].get("chat", {}).get("gaps") else "VISION",
    edges={"REFLECT": "REFLECT", "VISION": "VISION"},
)

orchestrator = builder.compile()

# SelfAnalysisOrchestrator クラス (main.py 内) で以下のように呼び出される想定
# async def run(self, messages: list, session_id: str):
#     initial_state = SelfAnalysisState(messages=messages, session_id=session_id, next_step=None)
#     result = await self.orchestrator.ainvoke(initial_state)
#     # ... (セッション情報の更新など)
#     return result
```

ターンを処理するには `SelfAnalysisOrchestrator().run(messages, session_id)` を呼び出します。

---

## 5 データ永続化

永続化はstanza互換を維持しており、SDK呼び出しを`Tool`内で使用されるバニラPythonヘルパーに置き換えるだけです。

| ストア                      | ツール         | スキーマ                     |
| --------------------------- | ------------ | ---------------------------- |
| `self_analysis_sessions`    | `note_store` | `{session_id, current_step}` |
| `self_analysis_notes`       | `note_store` | ステップスコープのJSON Blob    |
| `self_analysis_timeline_md` | 自動         | 生のMarkdownタイムライン     |

---

## 6 ガードレールと検証

LangChainは[GuardrailsAI](https://github.com/guardrails-ai/guardrails)との統合をサポートしています。
有効にするには：

```python
from langchain.validation.guardrails import GuardrailsValidator
validator = GuardrailsValidator.from_rail("rails/motivation.rail")
func_agent = create_openai_functions_agent(llm, tools, prompt, validators=[validator])
```

---

## 7 クイック実行 (ローカル)

```bash
uvicorn app.main:app --reload
# ➜  http://localhost:5050 を開いてチャット
```

---

## 8 拡張

1.  **新しいステップの追加**
    `YourStepAgent`を作成し、`NEXT_STEP`を宣言し、ノードとエッジをグラフに追加します。
2.  **ツールの追加**

    ```python
    from langchain.tools import Tool
    def fetch_stats(): ...
    stats_tool = Tool.from_function(fetch_stats, name="stats_tool", description="統計情報を取得...")
    ```
3.  **LLMの切り替え**
    `build_step_agent()`ファクトリに異なる`ChatOpenAI`または`ChatAnthropic`を渡します。

---

## 9 ディレクトリ構成

```
.
├─ app/
│  ├─ steps/
│  │  ├─ future.py
│  │  ├─ motivation.py
│  │  └─ ...
│  ├─ tools/
│  ├─ prompts/
│  ├─ utils/  # <--- 追加
│  │  └─ agent_builder.py
│  └─ main.py
└─ rails/
```

---

## 10 ライセンス

© 2025 Self-Analysis Agent Project.
Apache 2.0 License の下でリリースされています。

---

# 詳細技術仕様

## システム全体アーキテクチャ

### アーキテクチャ構成
- **オーケストレーター**: LangGraph StateGraphによる有向非巡回グラフ
- **エージェント**: 各ステップ専用のAgentExecutor（当初PlanAndExecute予定から簡略化）
- **LLM**: OpenAI GPT-4o（温度0、最大1000トークン制限）
- **ツール**: 4つの非同期ツール（note_store, list_notes, get_summary, render_markdown_timeline）
- **データ永続化**: PostgreSQL（セッション管理・ノート保存）

### 状態管理スキーマ

```python
class SelfAnalysisState(TypedDict):
    messages: list          # 会話履歴
    session_id: str        # セッション識別子
    next_step: str | None  # 次のステップ名
    current_response: str | None  # 現在のエージェント生レスポンス
    user_message: str | None      # ユーザー向けメッセージ
```

## 各ステップの詳細仕様

### FUTURE ステップ

**インプット**
- `messages`: 会話履歴配列
- `session_id`: セッション識別子
- `input`: 最新メッセージ内容（デフォルト: "自己分析を開始してください"）

**処理内容**
- プロンプト: `FUTURE_PROMPT`（将来のビジョンと価値観抽出）
- 利用ツール: note_store, list_notes, get_summary, render_markdown_timeline
- LLM温度: 0（一貫性重視）
- 最大反復回数: 5回

**期待アウトプット（JSON）**
```json
{
  "cot": "ユーザーの意図を要約し、価値観を抽出しました。",
  "chat": {
    "future": "テクノロジーで地域医療格差を解消する",
    "values": ["公平性","医療DX","地域貢献"],
    "question": "次に、具体的にどのような医療DX技術に興味がありますか？"
  }
}
```

**バリデーション基準**
- `future`: 30文字以内、主語含む能動表現、手段or対象含有
- `values`: 名詞1語×3、行動指針レベルの抽象度
- `question`: フレンドリー敬語、1文のみ

### MOTIVATION ステップ

**インプット**
- 前ステップからの状態継承
- ユーザーの体験談・エピソード

**処理内容**
- プロンプト: `MOTIVATION_PROMPT`（5W1H + 感情分析）
- 「なぜなぜ分析」による原体験の深掘り

**期待アウトプット（JSON）**
```json
{
  "cot": "<思考過程>",
  "chat": {
    "episode": {
      "when": "高校2年の夏",
      "where": "地方都市", 
      "who": "祖父と私",
      "what": "病院探しに半日費やした",
      "why": "適切な情報が無かった",
      "how": "口コミサイトを徹底的に検索",
      "emotion": "焦り",
      "insight": "医療情報の非対称性が高齢者の負担になると痛感した"
    },
    "question": "その時最も大変だった瞬間を具体的に教えてください"
  }
}
```

**バリデーション基準**
- `episode`: 全フィールド非空
- `emotion`: 単語1つ（喜び/悔しさ/焦り等）  
- `insight`: 40字以内
- `question`: 敬語1文

### HISTORY ステップ

**インプット**
- 前ステップからの状態継承
- ユーザーの経歴・体験

**処理内容**
- プロンプト: `HISTORY_PROMPT`（時系列整理）
- タイムライン生成とMarkdown変換

**期待アウトプット（JSON）**
```json
{
  "cot": "<思考過程>",
  "chat": {
    "timeline": [
      {
        "year": 2023,
        "event": "プログラミング部立ち上げ",
        "detail": "高校で医療レビューアプリを開発し全国大会入賞",
        "skills": ["Python","リーダーシップ"],
        "values": ["挑戦","協働"]
      }
    ],
    "question": "<次に聞く1文>"
  }
}
```

**バリデーション基準**
- `timeline`: 昇順ソート
- `skills`: 英単語1-3個
- `values`: 日本語1語1-3個
- `question`: 敬語1文

### GAP ステップ

**インプット**
- FUTURE + HISTORYステップの蓄積データ
- 現在の状況

**処理内容**
- プロンプト: `GAP_PROMPT`（ギャップ分析 + 5Whys）
- 原因分析と優先度付け

**期待アウトプット（JSON）**
```json
{
  "cot": "<思考過程>",
  "chat": {
    "gaps": [
      {
        "gap": "医療業界の専門知識不足",
        "category": "knowledge",
        "root_causes": [
          "医療従事者ネットワークがない",
          "学術論文を読む習慣が無い"
        ],
        "severity": 4,
        "urgency": 3,
        "recommend": "医工連携ゼミ参加を今学期内に申し込む"
      }
    ],
    "question": "上記の中で最も優先的に解決したいギャップはどれですか？"
  }
}
```

**バリデーション基準**
- `gaps`: 3-6件
- `root_causes`: 各gap につき1-3件
- `severity`・`urgency`: 整数1-5
- `category`: knowledge/skill/resource/network/mindset

### VISION ステップ

**インプット**
- 全前ステップの蓄積データ
- ギャップ分析結果

**処理内容**
- プロンプト: `VISION_PROMPT`（ビジョン策定）
- トーン分析と独自性スコア算出

**期待アウトプット（JSON）**
```json
{
  "cot": "<思考過程>",
  "chat": {
    "vision": "医療格差をAIでゼロにする",
    "tone_scores": {"excitement":6,"social":7,"feasible":5},
    "uniq_score": 0.42,
    "alt_taglines": [
      "誰もが医療に届く社会を創る",
      "医療アクセスの壁を壊すAIリーダー"
    ],
    "question": "このビジョンはあなたの言葉としてしっくり来ますか？"
  }
}
```

**バリデーション基準**
- `vision`: 30字以内、語尾「する/なる」
- `tone_scores`: 各1-7
- `uniq_score`: 0-1（低いほど独自）
- `question`: 敬語1文

### REFLECT ステップ

**インプット**
- 全ステップの蓄積データ
- 完全な自己分析セッション

**処理内容**
- プロンプト: `REFLECT_PROMPT`（包括的振り返り）
- マイルストーン設定とアクションプラン

**期待アウトプット（JSON）**
```json
{
  "cot": "<思考過程>",
  "chat": {
    "insights": ["行動が最速の学習である"],
    "strengths": ["課題発見力"],
    "growth_edges": ["仮説検証の頻度"],
    "milestones": [
      {"days":30,"kpi":"医工ゼミ出願完了"},
      {"days":90,"kpi":"TOEFL 80→90"},
      {"days":365,"kpi":"医療DXインターン1社経験"}
    ],
    "tips": ["Notionで週レビュー","友人と月1共有"],
    "summary": "...(140字)",
    "question": "本日の学びを一言で表すと何ですか？"
  }
}
```

**バリデーション基準**
- `insights`: 3-5行
- `strengths`・`growth_edges`: 各3行
- `milestones`: KPI数値/状態変化含有
- `summary`: 140字以内

## データフロー制御

### 状態遷移パターン
```
START → FUTURE → MOTIVATION → HISTORY → GAP → VISION → REFLECT → END
```

### 条件分岐ロジック
- `decide_after_gap()`: GAPステップ後の分岐判定
  - ギャップ検出あり → VISION
  - ギャップ検出なし → REFLECT（実装上は常にVISION）
- `decide_after_vision()`: VISIONステップ後は常にREFLECT

## エラーハンドリング

### レート制限対策
- `max_retries: 3`
- `request_timeout: 60秒`
- `max_tokens: 1000`

### フォールバック機構
- パースエラー時: 構造化されたデフォルトレスポンス
- DB接続エラー時: 処理継続（ログ記録のみ）
- LLM応答エラー時: ステップ固有のフォールバックメッセージ

## パフォーマンス特性

### 処理時間
- 各ステップ: 平均3-10秒（LLM応答時間依存）
- 全フロー: 約60-120秒

### リソース消費
- トークン使用量: ステップあたり500-1000トークン
- メモリ使用量: 状態管理で約1-5MB
- DB接続: セッションあたり2-3回のトランザクション

## 利用可能ツール詳細

### note_store (AsyncNoteTool)
- **機能**: 自己分析セッションおよびステップのノートを保存
- **インプット**: `session_id: str`, `step: str`, `content: dict`
- **アウトプット**: 保存確認メッセージ `str`

### list_notes (AsyncListNotesTool)
- **機能**: 自己分析セッションのノート一覧を取得
- **インプット**: `session_id: str`, `step: Optional[str]`
- **アウトプット**: ノート一覧 `List[dict]`

### get_summary (AsyncGetSummaryTool)
- **機能**: 自己分析セッションのサマリーを取得
- **インプット**: `session_id: str`
- **アウトプット**: サマリーテキスト `str`

### render_markdown_timeline (StructuredTool)
- **機能**: 履歴タイムラインのJSONをMarkdownテーブルに変換
- **インプット**: `timeline_json: str`
- **アウトプット**: Markdownフォーマットされたタイムライン
