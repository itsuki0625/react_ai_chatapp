# Self Analysis Agent 仕様

## 概要
- 自己分析フローを一貫して実行するオーケストレーターと各ステップ用エージェントで構成。
- 入力: ユーザーからの質問（user_input）
- 出力: ユーザー向けに整形された応答（polite & friendly tone、一度の返答につき質問は1つまで）

## フロー
1. セッション開始／継続管理 (`get_progress`, `SelfAnalysisSession` テーブル)
2. 現在ステップに対応するエージェントを取得（`VALUES_PROBE` → `STORY` → `GAP` → `ACTION` → `UNIV` → `VISION`）
3. エージェント実行 (`BaseSelfAnalysisAgent.run`)
   - **Plan** → **ReAct**（最大3回）→ **FinalAnswer & Micro-Reflexion**
   - プロンプト先頭に「日本語で、敬語かつフレンドリーな口調で回答してください。また、一度の返答につき質問は必ず1つだけ含めるようにしてください。」を付加
   - モデル: `gpt-4o-mini`
   - ツール: 現在ノーツ（`note_store`）やリフレクション（`reflection_store`）のみ
   - Guardrail: 最大プラントークン数120、最大ReAct反復3回、PIIブロック
4. 応答取得後、`note_store` でファイナルノート保存
5. `next_step` があれば `_advance` でセッションのステップ更新
6. 全ステップ完了後、`PostSessionReflexionAgent` でマクロリフレクション実行・保存
7. クライアントには `user_visible` または LLM出力の `content` を返却

## データ永続化
- `self_analysis_sessions`：セッションIDと現在ステップ管理
- `self_analysis_notes`：各ステップのノート（JSON）保存
- `self_analysis_cots`：Chain-of-Thought （COT）保存
- `self_analysis_reflections`：マイクロ・マクロリフレクション保存
- `self_analysis_summaries`：セッションサマリー保存
- DB: SQLAlchemy AsyncSessionLocal を使用

## 提供ツール
- `note_store(session_id: str, step: str, content: dict) → str`
- `list_notes(session_id: str, step?: str) → List[dict]`
- `get_summary(session_id: str) → dict`
- `reflection_store(session_id: str, step: str, level: str, content: str) → str`

## 各エージェントの詳細
- VALUES_PROBE (ValuesProbeAgent)
  - 目的: 価値観3語抽出
  - 概要: ユーザーのこれまでの経験から、自分にとって大切な価値観を3語で抽出する。PlanフェーズでChain-of-Thoughtを生成し、ReActループで具体的な質問を投げかけ、FinalAnswerで3つのキーワードを返却。
- STORY (StoryAgent)
  - 目的: 原体験年表生成
  - 概要: ユーザーの過去の経験を時系列で整理・可視化し、自己理解を深めるストーリーを生成。
- GAP (GapAnalysisAgent)
  - 目的: ギャップ&原因抽出
  - 概要: 現状と将来目標のギャップを特定し、その原因を深掘りする分析を実施。
- ACTION (ActionPlanAgent)
  - 目的: 短中長期プラン策定
  - 概要: 抽出したギャップを埋めるための短期・中期・長期の具体的な行動計画を提案。
- UNIV (UniversityMapperAgent)
  - 目的: 大学マッピング
  - 概要: 自己分析の結果を踏まえ、適切な大学や学部をマッピングし推薦。
- VISION (VisionAgent)
  - 目的: 1行ビジョン確定
  - 概要: 自己分析を経て得られた気づきを一行でまとめ、今後のビジョンを明確化。
- ALL (PostSessionReflexionAgent)
  - 目的: マクロリフレクション
  - 概要: セッション全体を振り返り、学びや改善点をまとめて提供。

----
### 参考ファイル
- `