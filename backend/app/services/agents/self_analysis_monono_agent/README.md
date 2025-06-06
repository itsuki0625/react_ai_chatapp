# Self‑Analysis Agent (AO Admissions Version)

## はじめに

本プロジェクトは **総合型選抜（AO 入試）の志望理由書** を作成するために必要な自己分析フローを自動化するエージェント群です。エージェント基盤には自社開発の **monono\_agent SDK**（`backend/app/services/agents/monono_agent/`）を採用しており、各ステップ専用エージェントは *BaseAgent ➜ BaseSelfAnalysisAgent* を継承して実装されています。fileciteturn3file0

---

## 0. monono\_agent SDK 概要

| コンポーネント                     | 役割                                   | 本プロジェクトでの利用例                                |   |
| --------------------------- | ------------------------------------ | ------------------------------------------- | - |
| **BaseAgent**               | LLM 呼び出し・ツール実行・ストリーム処理の共通ロジック        | `BaseSelfAnalysisAgent` が継承                 |   |
| **LLM Adapter**             | OpenAI / Anthropic などモデルごとの呼び出し差分を吸収 | `OpenAIAdapter` (`gpt-4.1`) を使用             |   |
| **ToolRegistry**            | Python 関数をツール化し LLM から実行             | `note_store`, `list_notes` など内部ストレージ操作ツール   |   |
| **PlanEngine**              | **提示されたゴールからタスク分割・順序決定を自動生成**        | 各 SelfAnalysisAgent が `run_with_plan()` で利用 |   |
| **Guardrail**               | 入出力/ツール実行のポリシー検査                     | `gap_guardrail`, `motivation_guardrail` など  |   |
| **ContextManager / Memory** | セッション履歴注入                            | 直近 10 メッセージを短期記憶として保持                       |   |
| **TraceLogger**             | 重要イベントを JSON で記録                     | ステップ完了時に gap 数・平均 severity をログ              |   |
| **Guardrail**               | 入出力/ツール実行のポリシー検査                     | `gap_guardrail`, `motivation_guardrail` など  |   |
| **ContextManager / Memory** | セッション履歴注入                            | 直近 10 メッセージを短期記憶として保持                       |   |
| **TraceLogger**             | 重要イベントを JSON で記録                     | ステップ完了時に gap 数・平均 severity をログ              |   |

SDK の詳細と拡張方法は `reference.md` を参照してください。fileciteturn3file1

---

## 1. ステップフロー

```
STEP_FLOW = [
    "FUTURE",      # 将来像と言語化テーマの選定
    "MOTIVATION",  # 動機・原体験の深掘り
    "HISTORY",     # 年表形式で経験を整理（詳細ヒアリング & Markdown 出力）
    "GAP",         # 理想と現状の差分と原因分析
    "VISION",      # 志望理由書の核となる 1 行ビジョン確定
    "REFLECT",     # 振り返り（マイクロ／マクロ）
]
```

### エージェント実装

| STEP        | クラス                | 継承                      | 主な責務                                       |
| ----------- | ------------------ | ----------------------- | ------------------------------------------ |
| FUTURE      | `FutureAgent`      | `BaseSelfAnalysisAgent` | 将来像＆価値観キーワード抽出                             |
| MOTIVATION  | `MotivationAgent`  | ↑                       | 原体験の因果関係を 5 Whys で深掘り                      |
| **HISTORY** | `HistoryAgent`     | ↑                       | **関係なさそうな情報も含め詳細ヒアリングし、Markdown 形式の年表を生成** |
| GAP         | `GapAnalysisAgent` | ↑                       | ギャップ特定＋根本原因分析＋優先度付け                        |
| VISION      | `VisionAgent`      | ↑                       | 志望理由書の 1 行ビジョン確定                           |
| REFLECT     | `ReflectAgent`     | ↑                       | マイクロ / マクロリフレクション                          |

---

## 1.1 HistoryAgent – 詳細ヒアリング & Markdown 年表

HistoryAgent では以下の追加仕様を実装します。

1. **深掘りヒアリング**

   * 一見関係なさそうなアルバイト・趣味・家庭環境なども網羅的に質問
   * 質問テンプレは `history_questions.yml` に定義（学年別／活動種別）
2. **年表データ構造**

   ```jsonc
   [
     {
       "year_range": "2019-04 – 2020-03",
       "grade": "高校 1 年",
       "event": "生徒会執行部 副会長",
       "achievement": "文化祭で来場者数を 1.5 倍に増加",
       "keywords": ["リーダーシップ", "企画力"]
     },
     ...
   ]
   ```
3. **Markdown 変換**

   * `render_markdown_timeline()` ユーティリティで表変換
   * 例：

     ```markdown
     | 期間 | 学年 | 出来事 | 実績/学び |
     |------|------|--------|-----------|
     | 2019/04 – 2020/03 | 高1 | 生徒会副会長 | 文化祭来場 +50% |
     ```
4. **可視化トリガー**

   * HistoryAgent `final_output` に `"timeline_md"` フィールドを含める
   * Orchestrator で受信後、ユーザーにそのまま提示

---

## 2. オーケストレーター (`SelfAnalysisOrchestrator`)

PlanEngine を利用するため、各エージェント呼び出しは **`run_with_plan()`** を使用します。

```python
from monono_agent.base_agent import BaseAgent
from agents.future import FutureAgent
from agents.motivation import MotivationAgent
from agents.history import HistoryAgent
from agents.gap import GapAnalysisAgent
from agents.vision import VisionAgent
from agents.reflect import ReflectAgent

AGENTS = {
    "FUTURE":  FutureAgent(),
    "MOTIVATION": MotivationAgent(),
    "HISTORY": HistoryAgent(),
    "GAP": GapAnalysisAgent(),
    "VISION": VisionAgent(),
    "REFLECT": ReflectAgent(),
}

class SelfAnalysisOrchestrator:
    def __init__(self):
        self.current_step = "FUTURE"
    async def run(self, messages, session_id):
        agent = AGENTS[self.current_step]
        # PlanEngine を介してサブタスクを自動計画・実行
        result = await agent.run_with_plan(messages, session_id=session_id)
        # --- ステップ遷移ロジック ---
        # 各エージェントの NEXT_STEP (定数) が result["next_step"] として返る
        # それをセッション状態に保存し、次回呼び出し時に参照する
        self.current_step = result.get("next_step", self.current_step)
        return result
```

### 2.1 ステップ遷移ロジック

1. **NEXT\_STEP 定数** – すべての `BaseSelfAnalysisAgent` 派生クラスに `NEXT_STEP` というクラス属性を定義。
2. **エージェント実行** – `run_with_plan()` の最後で `{"next_step": self.NEXT_STEP, ...}` を返却。
3. **オーケストレーターで更新** – 上記コードの `self.current_step = result.get("next_step" ...)` で状態を更新。
4. **永続化** – `note_store` 経由で `self_analysis_sessions.current_step` 列に保存（リロード対策）。

> 💡 **判断主体は各エージェント** です。条件分岐が必要な場合（例: GAP でギャップが 0 件 → VISION をスキップ）は、エージェント側で `next_step` を動的に書き換えて返すことで制御できます。python
> from monono\_agent.base\_agent import BaseAgent
> from agents.future import FutureAgent
> from agents.motivation import MotivationAgent
> from agents.history import HistoryAgent
> from agents.gap import GapAnalysisAgent
> from agents.vision import VisionAgent
> from agents.reflect import ReflectAgent

AGENTS = {
"FUTURE":  FutureAgent(),
"MOTIVATION": MotivationAgent(),
"HISTORY": HistoryAgent(),
"GAP": GapAnalysisAgent(),
"VISION": VisionAgent(),
"REFLECT": ReflectAgent(),
}

class SelfAnalysisOrchestrator:
def **init**(self):
self.current\_step = "FUTURE"
async def run(self, messages, session\_id):
agent = AGENTS\[self.current\_step]
\# PlanEngine を介してサブタスクを自動計画・実行
result = await agent.run\_with\_plan(messages, session\_id=session\_id)
self.current\_step = result.get("next\_step", self.current\_step)
return result

```python
from monono_agent.base_agent import BaseAgent
from agents.future import FutureAgent
from agents.motivation import MotivationAgent
from agents.history import HistoryAgent
from agents.gap import GapAnalysisAgent
from agents.vision import VisionAgent
from agents.reflect import ReflectAgent

AGENTS = {
    "FUTURE":  FutureAgent(),
    "MOTIVATION": MotivationAgent(),
    "HISTORY": HistoryAgent(),
    "GAP": GapAnalysisAgent(),
    "VISION": VisionAgent(),
    "REFLECT": ReflectAgent(),
}

class SelfAnalysisOrchestrator:
    def __init__(self):
        self.current_step = "FUTURE"
    async def run(self, messages, session_id):
        agent = AGENTS[self.current_step]
        result = await agent.run(messages, session_id=session_id)
        self.current_step = result.get("next_step", self.current_step)
        return result
```

---

## 3. データ永続化

| ストア                         | 用途                  | ツール                        |
| --------------------------- | ------------------- | -------------------------- |
| `self_analysis_sessions`    | 現在ステップ・セッション管理      | `note_store`               |
| `self_analysis_notes`       | 各ステップの JSON ノート     | `note_store`, `list_notes` |
| `self_analysis_cots`        | Chain‑of‑Thought ログ | 自動保存                       |
| `self_analysis_reflections` | リフレクション結果           | `reflection_store`         |

---

## 4. ガードレール / モデル設定

* **モデル**: `gpt-4.1`（プランニング・推論ともに同一モデル）
* **最大 Plan トークン**: 120
* **ReAct 反復**: 3 回
* **Guardrails**: `motivation_guardrail`, `gap_guardrail` ほか

---

## 5. 開発 & 拡張 Tips

1. **コンポーネント追加**

   * monono\_agent の `extra_cfg` で `resource_manager` や `error_recovery_manager` を注入可能。
2. **ツール拡張**

   * `tools/` ディレクトリに Python 関数を追加し、各エージェントの `tools` 引数に渡すだけ。
3. **ドラフト生成**

   * 志望理由書ドラフトが欲しい場合は `ESDraftAgent` を新規追加し `VISION → ESDRAFT → REFLECT` として挿入。

---

© 2025 – Self‑Analysis Agent Project (powered by monono\_agent)
