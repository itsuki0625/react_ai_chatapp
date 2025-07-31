# 志望理由書 AI全体添削機能 仕様書

## 概要
志望理由書の品質向上を目的とした包括的AI添削システム。6段階の専門的分析により、構造・内容・表現・一貫性・仕上げの観点から改善案を提供する。

## INPUT情報

### 必須入力データ
- **志望理由書テキスト**: 添削対象の文章（800-1000文字推奨）
- **statement_id**: 志望理由書の一意識別子
- **ユーザー認証情報**: JWT トークンによる認証

### 任意入力データ
- **focus_areas**: 重点改善分野の指定
  - 選択肢: `文章構造`, `説得力`, `具体性`, `表現力`, `論理性`, `独自性`
- **大学情報**: 志望大学の特色・アドミッションポリシー
- **自己分析結果**: 過去のチャット履歴からの文脈情報

### APIエンドポイント
```
POST /api/v1/statements/{statement_id}/ai-improve
Content-Type: application/json
Authorization: Bearer {jwt_token}

Body:
{
  "focus_areas": ["文章構造", "説得力"],
  "include_context": true
}
```

## 処理内容

### 6段階処理フロー

#### 1. ANALYSIS（分析）ステップ
- **目的**: 志望理由書の総合評価と問題点の特定
- **処理内容**:
  - 構造・内容・表現・一貫性の4観点評価（1-10点）
  - 読みやすさ・文化的適切性・オリジナリティ評価
  - 大学アドミッションポリシーとの適合性チェック
- **使用ツール**: 
  - `evaluation_tool`: 総合評価
  - `readability_assessment_tool`: 読みやすさ評価
  - `cultural_appropriateness_tool`: 文化的適切性
  - `plagiarism_check_tool`: オリジナリティ評価
  - `university_policy_fetch_tool`: 大学ポリシー取得

#### 2. STRUCTURE（構成）ステップ
- **目的**: 論理的構成と段落配置の最適化
- **処理内容**:
  - 段落数・文字数・バランス評価
  - 導入・本論・結論の流れ分析
  - 段落間の論理的繋がり確認
- **使用ツール**:
  - `token_guard_tool`: 文字数制限確認
  - `structure_analysis_tool`: 構成分析
  - `diff_generation_tool`: 改善案の差分生成

#### 3. CONTENT（内容）ステップ
- **目的**: 内容の深度と説得力の強化
- **処理内容**:
  - キーワード分析と主要テーマ抽出
  - 具体例・エピソードの充実度評価
  - 大学との関連性強化提案
- **使用ツール**:
  - `keyword_tag_extractor_tool`: キーワード抽出
  - `search_reference_tool`: 参考文献検索
  - `web_search_tool`: 最新情報検索
  - `generate_draft_tool`: 改善文案生成

#### 4. EXPRESSION（表現）ステップ
- **目的**: 語彙・文法・語調の改善
- **処理内容**:
  - 語調・文体の一貫性確認
  - 文法・語法の正確性チェック
  - 表現力向上のための語彙提案
- **使用ツール**:
  - `tone_style_adjust_tool`: 語調調整
  - `grammar_check_tool`: 文法チェック
  - `cultural_context_check_tool`: 文化的文脈確認

#### 5. COHERENCE（一貫性）ステップ
- **目的**: 論理的一貫性と整合性の確保
- **処理内容**:
  - 論理的流れの一貫性評価
  - テーマの統一性確認
  - 自己分析結果との整合性チェック
- **使用ツール**:
  - `evaluate_draft_tool`: 一貫性評価

#### 6. POLISH（仕上げ）ステップ
- **目的**: 最終品質向上と完成度チェック
- **処理内容**:
  - 技術的品質確認（誤字脱字、フォーマット）
  - 内容充実度・大学適合性・個性表現の総合評価
  - 最終グレード算出（A+〜D）
- **使用ツール**:
  - `list_revisions_tool`: リビジョン履歴
  - `apply_reflexion_tool`: リフレクション分析
  - `diff_versions_tool`: バージョン比較
  - `save_revision_tool`: 改訂保存

### 処理アーキテクチャ
```python
CorrectionOrchestrator
├── AnalysisStepAgent (LLM: gpt-4o-mini, temp: 0.3)
├── StructureStepAgent (LLM: gpt-4o-mini, temp: 0.4)
├── ContentStepAgent (LLM: gpt-4o-mini, temp: 0.6)
├── ExpressionStepAgent (LLM: gpt-4o-mini, temp: 0.4)
├── CoherenceStepAgent (LLM: gpt-4o, temp: 0.2)
└── PolishStepAgent (LLM: gpt-4o, temp: 0.3)
```

## OUTPUT情報

### APIレスポンス構造
```json
{
  "statement_id": "uuid",
  "improvements": {
    "analysis": {
      "content": "要約メッセージ",
      "suggestions": ["改善提案1", "改善提案2"],
      "changes": [
        {
          "original": "変更前のテキスト",
          "improved": "変更後のテキスト", 
          "reason": "変更理由"
        }
      ]
    },
    "structure": { /* 同様の構造 */ },
    "content": { /* 同様の構造 */ },
    "expression": { /* 同様の構造 */ },
    "coherence": { /* 同様の構造 */ },
    "polish": { /* 同様の構造 */ }
  },
  "overall_score": 75,
  "processing_time": "32.5s",
  "timestamp": "2025-01-10T02:51:11Z"
}
```

### 各ステップの出力内容

#### ANALYSISステップ
- **総合スコア**: 1-100点での評価
- **分野別スコア**: 構造/内容/表現/一貫性の個別評価
- **優先改善エリア**: 重点的に改善すべき分野
- **改善提案**: 具体的な改善方向性

#### STRUCTUREステップ  
- **構成改善案**: 段落の再構成提案
- **論理的流れ**: 導入→本論→結論の最適化
- **接続詞提案**: 段落間の繋がり強化

#### CONTENTステップ
- **内容強化提案**: エピソードの具体化
- **大学関連性**: 志望校との関連付け
- **動機深掘り**: より説得力のある動機表現

#### EXPRESSIONステップ
- **語彙改善**: より適切な表現への置換
- **文法修正**: 助詞・敬語・文体の統一
- **語調調整**: 自信に満ちた表現への変更

#### COHERENCEステップ
- **論理性改善**: 一貫した論理展開
- **テーマ統一**: 主張の一貫性確保
- **整合性確認**: 自己分析との整合性

#### POLISHステップ
- **最終グレード**: A+〜Dでの評価
- **完成度**: 提出可能レベルかの判定
- **次のアクション**: さらなる改善の必要性

## 表示手法

### フロントエンド表示コンポーネント

#### 1. 全体添削ボタン
```tsx
<Button className="w-full bg-gradient-to-r from-purple-600 to-purple-700">
  <Zap className="w-4 h-4 mr-2" />
  全体添削を実行
</Button>
```

#### 2. 重点分野選択UI
- チップ形式の選択可能ボタン
- 複数選択対応
- 選択状態の視覚的フィードバック

#### 3. チャット画面での結果表示
```tsx
{/* ステップ別 suggestions のみ表示 */}
<div className="space-y-4">
  {Object.entries(improvements).map(([step, improvement]) => (
    <div key={step} className="bg-white p-4 rounded-lg border">
      <div className="flex items-center mb-3">
        <Badge className={getStepColor(step)}>
          {improvement.title}
        </Badge>
        <span className="ml-2 text-sm text-gray-600">
          {improvement.suggestions.length}件の提案
        </span>
      </div>
      
      {/* 改善提案リスト - クリック可能 */}
      <div className="space-y-2">
        {improvement.suggestions.map((suggestion, index) => (
          <div 
            key={index}
            className="p-3 bg-gray-50 rounded-md cursor-pointer hover:bg-gray-100 transition-colors"
            onClick={() => handleSuggestionClick(step, index)}
          >
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-700">{suggestion}</p>
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </div>
          </div>
        ))}
      </div>
    </div>
  ))}
</div>
```

#### 4. エディタ画面での変更内容表示
```tsx
{/* 選択された suggestion の変更内容を左エディタに表示 */}
{selectedSuggestion && (
  <div className="absolute inset-0 bg-white/95 backdrop-blur-sm z-10 p-4 overflow-y-auto">
    <div className="max-w-4xl mx-auto">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">変更内容の詳細</h3>
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => setSelectedSuggestion(null)}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
      
      {/* 変更内容表示 */}
      <div className="space-y-4">
        {selectedSuggestion.changes.map((change, index) => (
          <div key={index} className="border rounded-lg overflow-hidden">
            {/* 変更前（赤背景） */}
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex items-center mb-2">
                <Minus className="w-4 h-4 text-red-600 mr-2" />
                <span className="text-sm font-medium text-red-800">変更前</span>
              </div>
              <p className="text-gray-700 whitespace-pre-wrap">
                {change.original}
              </p>
            </div>
            
            {/* 変更後（緑背景） */}
            <div className="bg-green-50 border-l-4 border-green-400 p-4">
              <div className="flex items-center mb-2">
                <Plus className="w-4 h-4 text-green-600 mr-2" />
                <span className="text-sm font-medium text-green-800">変更後</span>
              </div>
              <p className="text-gray-700 whitespace-pre-wrap">
                {change.improved}
              </p>
            </div>
            
            {/* 変更理由（吹き出し） */}
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
              <div className="flex items-start">
                <MessageCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5" />
                <div>
                  <span className="text-sm font-medium text-blue-800 block mb-1">
                    変更理由
                  </span>
                  <p className="text-sm text-blue-700">
                    {change.reason}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* アクションボタン */}
      <div className="flex justify-end space-x-3 mt-6">
        <Button 
          variant="outline" 
          onClick={() => setSelectedSuggestion(null)}
        >
          キャンセル
        </Button>
        <Button 
          onClick={() => handleApplyAllChanges(selectedSuggestion.changes)}
          className="bg-green-600 hover:bg-green-700"
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          すべての変更を適用
        </Button>
      </div>
    </div>
  </div>
)}
```

#### 5. アクションボタン
```tsx
{/* 個別適用・拒否 */}
<Button onClick={() => handleApplySuggestion(id)}>
  <CheckCircle className="w-3 h-3 mr-1" />
  適用
</Button>
<Button variant="outline" onClick={() => handleRejectSuggestion(id)}>
  <XCircle className="w-3 h-3 mr-1" />
  拒否
</Button>

{/* 状態表示 */}
<Badge className="bg-green-100 text-green-800">
  <CheckCircle className="w-3 h-3 mr-1" />
  適用済み
</Badge>
```

#### 6. ステップカラーコーディング
- **分析**: 青系 (`bg-blue-100 text-blue-800`)
- **構成**: 緑系 (`bg-green-100 text-green-800`) 
- **内容**: 紫系 (`bg-purple-100 text-purple-800`)
- **表現**: 黄系 (`bg-yellow-100 text-yellow-800`)
- **一貫性**: ピンク系 (`bg-pink-100 text-pink-800`)
- **仕上げ**: グレー系 (`bg-gray-100 text-gray-800`)

### UX設計原則

#### 1. 階層的情報表示
- **Level 1**: チャット画面 - ステップ名 + 提案件数
- **Level 2**: チャット画面 - クリック可能な提案リスト
- **Level 3**: エディタ画面 - 変更内容の詳細表示
- **Level 4**: エディタ画面 - Before/After + 理由の表示

#### 2. プログレッシブディスクロージャー
- **初期状態**: チャット画面でsuggestions一覧表示
- **提案選択**: エディタ画面にオーバーレイで変更内容表示
- **詳細確認**: 変更前後の比較 + 理由の説明
- **適用決定**: 一括適用またはキャンセル

#### 3. インタラクションフロー
```
チャット画面                     エディタ画面
┌──────────────────┐            ┌─────────────────────┐
│ 1. ステップ別表示    │            │                     │
│ 2. 提案リスト表示    │ ─クリック─→ │ 3. 変更内容オーバーレイ │
│ 3. 矢印アイコン      │            │ 4. Before/After表示   │
└──────────────────┘            │ 5. 変更理由表示       │
                                │ 6. 適用/キャンセル     │
                                └─────────────────────┘
```

#### 4. ビジュアルフィードバック
- **ホバー効果**: 提案にマウスオーバーで背景色変更
- **矢印アイコン**: 詳細表示可能を示唆
- **色分け**: 
  - 変更前: 赤系背景（`bg-red-50`）
  - 変更後: 緑系背景（`bg-green-50`）
  - 変更理由: 青系背景（`bg-blue-50`）

#### 5. エラーハンドリング
- **適用失敗**: エラーメッセージ表示 + 元の状態に復帰
- **部分適用**: 成功した変更のみ反映 + 失敗分は通知
- **キャンセル**: 変更を破棄してオーバーレイを閉じる

#### 6. フィードバック設計
- 成功: `toast.success("○件の変更を適用しました")`
- エラー: `toast.error("変更の適用に失敗しました")`
- 情報: `toast.info("変更をキャンセルしました")`

### 状態管理

#### React State構造
```tsx
interface StepImprovement {
  step: string;           // ステップ識別子 
  title: string;          // 表示名
  content: string;        // 要約メッセージ
  suggestions: string[];  // 改善提案リスト
  changes: Change[];      // 具体的変更案
}

interface Change {
  original: string;       // 変更前のテキスト
  improved: string;       // 変更後のテキスト
  reason: string;         // 変更理由
}

interface SelectedSuggestion {
  step: string;           // ステップ識別子
  suggestionIndex: number;// 提案のインデックス
  suggestionText: string; // 提案テキスト
  changes: Change[];      // 関連する変更案
}

// コンポーネント状態
const [improvements, setImprovements] = useState<Record<string, StepImprovement>>({});
const [selectedSuggestion, setSelectedSuggestion] = useState<SelectedSuggestion | null>(null);
const [appliedChanges, setAppliedChanges] = useState<Set<string>>(new Set());
```

#### 処理フロー
1. **全体添削実行**: API呼び出し → ローディング表示
2. **結果受信**: パース処理 → チャット画面にsuggestions表示
3. **提案選択**: `handleSuggestionClick(step, index)` → エディタ画面にchanges表示
4. **変更適用**: `handleApplyAllChanges(changes)` → エディタ内容更新
5. **自動保存**: 変更適用時に文章更新

#### 主要ハンドラー関数
```tsx
// 提案クリック時の処理
const handleSuggestionClick = (step: string, index: number) => {
  const improvement = improvements[step];
  const suggestionText = improvement.suggestions[index];
  
  // 該当する変更案を取得（実装依存）
  const relatedChanges = getRelatedChanges(step, index, improvement.changes);
  
  setSelectedSuggestion({
    step,
    suggestionIndex: index,
    suggestionText,
    changes: relatedChanges
  });
};

// すべての変更を適用
const handleApplyAllChanges = (changes: Change[]) => {
  let updatedContent = editorContent;
  
  changes.forEach(change => {
    updatedContent = updatedContent.replace(change.original, change.improved);
  });
  
  setEditorContent(updatedContent);
  setSelectedSuggestion(null);
  
  // 適用済みマークを付ける
  const changeIds = changes.map(c => `${c.original}-${c.improved}`);
  setAppliedChanges(prev => new Set([...prev, ...changeIds]));
};
```

この仕様により、ユーザーは直感的に志望理由書の品質向上を図ることができ、AI添削の恩恵を最大限に活用できます。
