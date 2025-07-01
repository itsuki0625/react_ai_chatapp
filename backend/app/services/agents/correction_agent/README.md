# 志望理由書添削エージェント (Correction Agent)

## 概要

志望理由書の添削を行うAIエージェントシステムです。`self_analysis_langchain`を参考に、LangGraphを使用してマルチステップの添削ワークフローを実装しています。

## 設計思想

- **AIはアドバイザー**: 代筆ではなく、学生が自分で改善できるよう具体的なアドバイスを提供
- **インタラクティブな改善**: 提案ごとに承認・拒否を選択可能
- **差分ビュー**: 修正案を現在の文章と比較して表示
- **複数セッション対応**: 目的別のチャット管理が可能

## アーキテクチャ

### ステップ構成

1. **ANALYSIS** - 総合的な分析とスコアリング
2. **STRUCTURE** - 文章構成と論理的な流れの改善
3. **CONTENT** - 内容の深掘りと説得力の強化
4. **EXPRESSION** - 表現力と語彙の改善
5. **COHERENCE** - 一貫性と論理性の確認
6. **POLISH** - 最終仕上げと完成度チェック

### 主要コンポーネント

```
correction_agent/
├── main.py                    # オーケストレーター
├── prompts.py                 # 各ステップ用プロンプト
├── tools.py                   # 添削専用ツール
├── steps/                     # ステップエージェント
│   ├── analysis.py
│   ├── structure.py
│   ├── content.py
│   ├── expression.py
│   ├── coherence.py
│   └── polish.py
└── utils/
    └── agent_builder.py       # エージェント構築ユーティリティ
```

## 使用方法

### 基本的な使用例

```python
from app.services.agents.correction_agent import CorrectionOrchestrator

# オーケストレーターを初期化
orchestrator = CorrectionOrchestrator()

# 添削を実行
result = await orchestrator.run(
    statement_text="私は医学部を志望します。理由は...",
    messages=[{"content": "志望理由書を添削してください", "role": "user"}],
    session_id="session_123",
    university_info="東京大学医学部",
    self_analysis_context="自己分析の結果: 医療への関心が高い"
)

# 結果を取得
user_message = result["user_message"]
step_results = result["step_results"]
```

### 個別ステップの使用

```python
from app.services.agents.correction_agent.steps import AnalysisStepAgent

# 分析ステップのみを実行
agent = AnalysisStepAgent()
analysis_result = await agent({
    "statement_text": "志望理由書の内容",
    "messages": [],
    "session_id": "session_123",
    "university_info": "東京大学医学部",
    "self_analysis_context": "自己分析の結果"
})
```

## ツール

### 構造分析ツール
- 段落構成の分析
- 論理的な流れの評価
- 大学との関連性チェック
- 自己分析との統合度評価

### 差分生成ツール
- 元の文章と修正案の比較
- 変更点の詳細分析
- 改善タイプの分類

### フィードバック保存ツール
- 添削結果の永続化
- セッション管理
- 進捗追跡

## レスポンス形式

各ステップは以下の形式でレスポンスを返します：

```json
{
  "cot": "分析の思考過程",
  "analysis|structure|content|expression|coherence|polish": {
    // ステップ固有のデータ
  },
  "chat": {
    "summary": "ユーザー向けの要約",
    "question": "次の質問やアクション"
  }
}
```

## 特徴

### 1. ユーザー中心の設計
- 学生の主体性を尊重
- 選択可能な改善提案
- 段階的な改善プロセス

### 2. 高度な分析機能
- 多角的な文章分析
- 志望大学との適合性評価
- 自己分析結果の活用

### 3. 柔軟なワークフロー
- ユーザーリクエストに基づく動的ステップ選択
- 各ステップの独立実行も可能
- カスタマイズ可能なエージェント設定

### 4. 拡張性
- 新しいステップの追加が容易
- カスタムツールの組み込み可能
- プロンプトの調整・改善が簡単

## 設定可能項目

### LLMパラメーター
- `temperature`: 創造性のレベル（ステップごとに最適化）
- `max_tokens`: 出力トークン数の制限
- `max_iterations`: エージェントの最大反復回数

### ワークフロー設定
- ステップの順序変更
- 条件付きステップスキップ
- 並列処理の対応

## パフォーマンス

- **レスポンス時間**: 各ステップ30-60秒
- **精度**: 構造化されたプロンプトによる一貫した品質
- **拡張性**: ステップ並列実行による高速化可能

## 今後の改善予定

1. **リアルタイム差分表示**
2. **より高度な文章評価指標**
3. **大学別の専門的なアドバイス**
4. **機械学習による改善提案の精度向上**
5. **ユーザーフィードバックによる学習機能** 