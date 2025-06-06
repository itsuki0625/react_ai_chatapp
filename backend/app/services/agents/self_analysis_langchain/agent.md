# SelfAnalysisLangChain エージェント仕様

## 1. 概要
- エージェント名: `SelfAnalysisOrchestrator`
- 目的: 学生の自己分析を段階的にガイドし、構造化されたJSON出力を生成する
- 使用技術:
  - LangGraph (`StateGraph` による状態マシン)
  - LangChain PlanAndExecute + OpenAI Functions（`gpt-4o`）
  - 非同期DB (`AsyncSessionLocal`, モデル `SelfAnalysisSession`)

## 2. 入力
- **messages**: List of `{ "role": "user"|"assistant", "content": "..." }`
- **session_id**: セッション識別用の文字列

## 3. 処理フロー
1. **初期状態作成**
   ```python
   initial_state = SelfAnalysisState(
     messages=messages,
     session_id=session_id,
     next_step=None
   )
   ```
2. **状態マシン実行** (`orchestrator.ainvoke`)
   - ステップ: `FUTURE` → `MOTIVATION` → `HISTORY` → `GAP` → `VISION` → `REFLECT`
   - `GAP`ステップで `gaps=[]` の場合、`VISION` をスキップして直接 `REFLECT` に遷移
3. **ステップエージェント呼び出し**
   - 各プロンプト: `FUTURE_PROMPT`, `MOTIVATION_PROMPT`, `HISTORY_PROMPT`, `GAP_PROMPT`, `VISION_PROMPT`, `REFLECT_PROMPT`
   - ツール: `note_store`, `list_notes`
   - 入力形式: `{"input": params}`
   - レスポンスが `AgentFinish` なら直接出力、`AgentAction` 時はツール実行後に再度 `ainvoke` して最終出力を取得
4. **DB永続化**
   - `SelfAnalysisSession.current_step` を最新の `next_step` で更新・保存

## 4. ステップ詳細

### 4.1 FUTURE（将来像抽出）
- 出力JSON:
  ```json
  {"cot":"...",
   "chat":{
     "future":"...",
     "values":["価値観1","価値観2","価値観3"],
     "question":"..."
   }
  }
  ```
- 評価基準: `future` は30字以内／能動表現、`values` 名詞1語×3、`question` 敬語1文

### 4.2 MOTIVATION（動機深掘り）
- 出力JSON:
  ```json
  {"cot":"...",
   "chat":{
     "episode":{...},
     "question":"..."
   }
  }
  ```
- 評価基準: episode 各フィールド非空、`emotion` 1語、`insight` 40字以内、質問は敬語1文

### 4.3 HISTORY（時系列整理）
- 出力JSON:
  ```json
  {"cot":"...",
   "chat":{
     "timeline":[{ "year":2023, ... }],
     "question":"..."
   }
  }
  ```
- 評価基準: timeline 昇順、`skills` 1–3英単語、`values` 1–3日本語1語

### 4.4 GAP（ギャップ分析）
- 出力JSON:
  ```json
  {"cot":"...",
   "chat":{
     "gaps":[
       {"gap":"...","category":"knowledge|skill|resource|network|mindset", ...}
     ],
     "question":"..."
   }
  }
  ```
- 評価基準: `gaps` 3–6件、`root_causes` 1–3件、`severity`/`urgency` 1–5整数

### 4.5 VISION（ビジョン策定）
- 出力JSON:
  ```json
  {"cot":"...",
   "chat":{
     "vision":"...",
     "tone_scores":{"excitement":1-7,...},
     "uniq_score":0.0-1.0,
     "alt_taglines":["..."],
     "question":"..."
   }
  }
  ```
- 評価基準: `vision` 30字以内／「する」または「なる」、`tone_scores` 1–7、`uniq_score` 0–1

### 4.6 REFLECT（振り返り）
- 出力JSON:
  ```json
  {"cot":"...",
   "chat":{
     "insights":["..."],
     "strengths":["..."],
     "growth_edges":["..."],
     "milestones":[{"days":30,"kpi":"..."}],
     "tips":["..."],
     "summary":"...",
     "question":"..."
   }
  }
  ```
- 評価基準: `insights` 3–5行、`strengths`/`growth_edges` 各3行、`summary` 140字以内

## 5. SelfAnalysisState の定義
`SelfAnalysisState` は TypedDict で以下のフィールドを持ちます:
- `messages: list`
  - 各ステップの出力結果を格納する会話履歴リスト。要素は `{ "role": "assistant", "content": "...", "chat": { ... } }` の形式で追加される。
- `session_id: str`
  - セッションを一意に識別する文字列。
- `next_step: str | null`
  - 次に実行すべきステップの識別子。状態遷移の結果によって設定される。

## 6. ステップエージェントへの情報受け渡し
各ステップエージェント（例: `FutureStepAgent`）は、`build_step_agent` により以下のプロンプトテンプレートを組み立て、前ステップの情報を受け取ります:
```text
{step_prompt}

--- Additional Context for Agent ---
Conversation History (passed as 'messages'):
{messages}

Session ID (passed as 'session_id'):
{session_id}

Agent Scratchpad (for agent's internal thoughts and tool usage):
{agent_scratchpad}
```
- `step_prompt`: 各ステップ専用の JSON 出力フォーマット定義
- `messages`: これまでの全会話履歴。前ステップの出力が含まれ、エージェントは参照・分析可能
- `session_id`: セッション継続のための識別子
- `agent_scratchpad`: PlanAndExecute が中間思考やツール呼び出し計画を保存する領域

## 7. PlanAndExecute の役割
`PlanAndExecute` は以下の２つのコンポーネントで成り立ち、複雑な推論とツール利用を統合します:
1. **プランナー (Planner)**
   - `load_chat_planner` を用いて、LLM による『どのように考え、どのツールをいつ呼び出すか』という高レベルなプランを生成。
2. **実行者 (Executor)**
   - `ChainExecutor` + `AgentExecutor` を組み合わせ、プランに従ってツール呼び出し (`note_store`, `list_notes` 等) と最終出力生成を実行。

このアーキテクチャにより、各ステップで『連続した CoT 推論』と『必要に応じたツール呼び出し』を一貫して扱える柔軟性が得られます。

---

以上が SelfAnalysisLangChain エージェントの仕様です。
