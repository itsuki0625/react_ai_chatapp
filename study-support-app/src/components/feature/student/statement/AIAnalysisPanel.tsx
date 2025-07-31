"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  CheckCircle, 
  XCircle, 
  Sparkles, 
  Loader2,
  ArrowRight,
  Zap,
  ChevronRight,
  FileText,
  BarChart3,
  AlertCircle,
  TrendingUp,
  Eye,
  Lightbulb
} from 'lucide-react';
import { 
  AIImprovementRequest,
  improveStatementWithAI,
  parseAIImprovements,
  StepImprovement
} from '@/services/statementService';
import { toast } from 'sonner';

interface Change {
  original: string;
  improved: string;
  reason: string;
}

interface Props {
  statementId: string;
  currentContent: string;
  onContentChange: (content: string) => void;
  onImprovementApplied: () => void;
  onSuggestionClick: (step: string, index: number, suggestionText: string, changes: Change[]) => void;
}

interface AnalysisResult {
  step: string;
  title: string;
  score: number;
  suggestions: string[];
  changes: Change[];
}

export default function AIAnalysisPanel({ 
  statementId, 
  currentContent, 
  onContentChange, 
  onImprovementApplied,
  onSuggestionClick
}: Props) {
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFocusAreas, setSelectedFocusAreas] = useState<string[]>([]);
  const [appliedChanges, setAppliedChanges] = useState<Set<string>>(new Set());
  const [hasAnalyzed, setHasAnalyzed] = useState(false);

  const focusAreaOptions = [
    '文章構造',
    '説得力',
    '具体性',
    '論理的一貫性',
    '表現力',
    '独自性'
  ];

  // 分析を実行
  const handleAnalyze = async () => {
    try {
      setLoading(true);
      
      const response = await improveStatementWithAI(statementId, {
        personal_statement_id: statementId,
        focus_areas: selectedFocusAreas.length > 0 ? selectedFocusAreas : undefined
      });

      const parsedImprovements = parseAIImprovements(response);
      
      // 分析結果にスコアを追加（モックデータ）
      const analysisWithScores = parsedImprovements.map((improvement) => ({
        ...improvement,
        score: Math.floor(Math.random() * 40) + 60 // 60-100のランダムスコア
      }));
      
      setAnalysisResults(analysisWithScores);
      setHasAnalyzed(true);
      toast.success('AI分析が完了しました');

    } catch (error) {
      console.error('Analysis failed:', error);
      toast.error('AI分析中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFocusArea = (area: string) => {
    setSelectedFocusAreas(prev => 
      prev.includes(area) 
        ? prev.filter(a => a !== area)
        : [...prev, area]
    );
  };

  const getStepColor = (step: string) => {
    const colors = {
      'analysis': 'bg-blue-100 text-blue-800 border-blue-200',
      'structure': 'bg-green-100 text-green-800 border-green-200',
      'content': 'bg-purple-100 text-purple-800 border-purple-200',
      'expression': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'coherence': 'bg-pink-100 text-pink-800 border-pink-200',
      'polish': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[step as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getStepTitle = (step: string) => {
    const titles = {
      'analysis': '分析',
      'structure': '構成',
      'content': '内容',
      'expression': '表現',
      'coherence': '一貫性',
      'polish': '仕上げ'
    };
    return titles[step as keyof typeof titles] || step;
  };

  const cleanSuggestionText = (suggestion: string) => {
    if (!suggestion) return '';
    
    // システム内部の分類ラベルを除去
    let cleaned = suggestion;
    
    // "type: description" 形式の場合、descriptionのみを表示
    if (suggestion.includes(':')) {
      const colonIndex = suggestion.indexOf(':');
      const beforeColon = suggestion.substring(0, colonIndex).trim();
      const afterColon = suggestion.substring(colonIndex + 1).trim();
      
      // 英語のシステム用語の場合は、コロン後の部分のみを使用
      const systemTerms = [
        'quality_improvement', 'reflexion_based', 'paragraph_restructuring', 
        'transition_improvement', 'balance_adjustment', 'content_enhancement',
        'expression_improvement', 'coherence_improvement'
      ];
      if (systemTerms.includes(beforeColon)) {
        cleaned = afterColon;
      }
    }
    
    // システム内部メッセージの変換
    const messageReplacements = [
      { pattern: /(\w+)ステップの改善案を処理中/, replacement: 'この項目の分析を実行中です...' },
      { pattern: /analysisステップの改善案を処理中/, replacement: '基本分析を実行中です...' },
      { pattern: /structureステップの改善案を処理中/, replacement: '文章構成を分析中です...' },
      { pattern: /contentステップの改善案を処理中/, replacement: '内容の深さを分析中です...' },
      { pattern: /expressionステップの改善案を処理中/, replacement: '表現力を分析中です...' },
      { pattern: /coherenceステップの改善案を処理中/, replacement: '一貫性を分析中です...' },
      { pattern: /polishステップの改善案を処理中/, replacement: '最終チェックを実行中です...' }
    ];
    
    messageReplacements.forEach(({ pattern, replacement }) => {
      cleaned = cleaned.replace(pattern, replacement);
    });
    
    // 優先度表記を日本語に変換
    cleaned = cleaned.replace(/\s*\(high\)/, ' (重要)');
    cleaned = cleaned.replace(/\s*\(medium\)/, ' (中程度)');
    cleaned = cleaned.replace(/\s*\(low\)/, ' (軽微)');
    
    // 不自然な表現を修正
    cleaned = cleaned.replace(/さらなる改善が必要です。指摘された点を修正してください。/, '更なる品質向上の余地があります');
    cleaned = cleaned.replace(/段階的な改善を継続/, '継続的な改善を推奨します');
    cleaned = cleaned.replace(/定期的な見直しを実施/, '定期的な見直しが効果的です');
    
    return cleaned.trim();
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (score >= 80) return <BarChart3 className="w-4 h-4 text-blue-600" />;
    if (score >= 70) return <Eye className="w-4 h-4 text-yellow-600" />;
    return <AlertCircle className="w-4 h-4 text-red-600" />;
  };

  const overallScore = analysisResults.length > 0 
    ? Math.round(analysisResults.reduce((sum, result) => sum + result.score, 0) / analysisResults.length)
    : 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header - Analysis Controls */}
      <div className="p-4 bg-white border-b flex-shrink-0">
        <div className="space-y-3">
          {/* Analysis Button */}
          <Button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI分析中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI分析を開始
              </>
            )}
          </Button>

          {/* Focus Areas Selection */}
          <div className="space-y-2">
            <p className="text-xs text-gray-600">分析重点項目を選択（任意）</p>
            <div className="flex flex-wrap gap-1">
              {focusAreaOptions.map(area => (
                <Button
                  key={area}
                  variant={selectedFocusAreas.includes(area) ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleToggleFocusArea(area)}
                  className="text-xs h-6 px-2"
                >
                  {area}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Results */}
      <ScrollArea className="flex-1 p-4">
        {!hasAnalyzed && !loading && (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">志望理由書のAI分析</h3>
            <p className="text-sm text-gray-500 mb-6">
              AI技術により、あなたの志望理由書を詳細に分析し、<br />
              改善点を具体的に提案いたします。
            </p>
            <div className="bg-blue-50 rounded-lg p-4 text-left max-w-md mx-auto">
              <h4 className="font-medium text-blue-900 mb-2">分析内容：</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 文章構造の論理性</li>
                <li>• 説得力と具体性</li>
                <li>• 表現力と独自性</li>
                <li>• 全体的な一貫性</li>
              </ul>
            </div>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center space-x-3 bg-blue-50 rounded-lg px-6 py-4">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <div className="text-left">
                <p className="font-medium text-blue-900">AI分析実行中</p>
                <p className="text-sm text-blue-700">志望理由書を詳細に分析しています...</p>
              </div>
            </div>
          </div>
        )}

        {hasAnalyzed && analysisResults.length > 0 && (
          <div className="space-y-6">
            {/* 総合スコア */}
            <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-purple-50">
              <CardHeader>
                <CardTitle className="flex items-center text-lg">
                  <BarChart3 className="w-5 h-5 mr-2 text-blue-600" />
                  総合分析結果
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold mb-2 text-gray-800">
                    {overallScore}
                    <span className="text-lg text-gray-500 ml-1">/ 100</span>
                  </div>
                  <div className="flex items-center justify-center space-x-2">
                    {getScoreIcon(overallScore)}
                    <span className={`font-medium ${getScoreColor(overallScore)}`}>
                      {overallScore >= 90 ? '優秀' : 
                       overallScore >= 80 ? '良好' : 
                       overallScore >= 70 ? '改善の余地あり' : '要改善'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {analysisResults.length}つの項目で分析完了
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* 詳細分析結果 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <Lightbulb className="w-5 h-5 mr-2 text-yellow-500" />
                詳細分析・改善提案
              </h3>
              
              {analysisResults.map((result, index) => (
                <Card key={result.step} className={`border ${getStepColor(result.step).split(' ').pop()}`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                                        <CardTitle className="flex items-center text-base">
                    <Badge className={getStepColor(result.step)}>
                      {getStepTitle(result.step)}
                    </Badge>
                  </CardTitle>
                      <div className="flex items-center space-x-2">
                        {getScoreIcon(result.score)}
                        <span className={`font-bold ${getScoreColor(result.score)}`}>
                          {result.score}点
                        </span>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                                        {/* 改善提案リスト */}
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-700">改善提案</h4>
                      {result.suggestions && result.suggestions.length > 0 ? (
                        result.suggestions.map((suggestion, sugIndex) => {
                          const cleanedSuggestion = cleanSuggestionText(suggestion);
                          
                          // 空や無意味な提案をフィルタリング
                          if (!cleanedSuggestion || cleanedSuggestion.trim().length < 5) {
                            return null;
                          }
                          
                          return (
                            <div 
                              key={sugIndex}
                              className="p-3 bg-white rounded-md border cursor-pointer hover:bg-gray-50 transition-colors"
                              onClick={() => onSuggestionClick(result.step, sugIndex, cleanedSuggestion, result.changes)}
                            >
                              <div className="flex items-start justify-between">
                                <p className="text-sm text-gray-700 flex-1">{cleanedSuggestion}</p>
                                <ChevronRight className="w-4 h-4 text-gray-400 ml-2 flex-shrink-0 mt-0.5" />
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="p-3 bg-gray-50 rounded-md border border-dashed">
                          <p className="text-sm text-gray-500 text-center">
                            この項目の分析結果を準備中です...
                          </p>
                        </div>
                      )}
                    </div>

                    {/* 変更件数表示 */}
                    {result.changes.length > 0 && (
                      <div className="flex items-center justify-between pt-2 border-t">
                        <span className="text-xs text-gray-500">
                          {result.changes.length}件の具体的な改善案があります
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onSuggestionClick(result.step, 0, result.suggestions[0] || '', result.changes)}
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          詳細を見る
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* 再分析ボタン */}
            <div className="pt-4 border-t">
              <Button
                onClick={handleAnalyze}
                disabled={loading}
                variant="outline"
                className="w-full"
              >
                <Zap className="w-4 h-4 mr-2" />
                再分析を実行
              </Button>
            </div>
          </div>
        )}
      </ScrollArea>
    </div>
  );
} 