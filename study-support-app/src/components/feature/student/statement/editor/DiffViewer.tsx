'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Check, 
  X, 
  Eye, 
  EyeOff, 
  Sparkles,
  RotateCcw,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { StatementImprovementResponse } from '@/services/statementService';

interface DiffViewerProps {
  improvementData: StatementImprovementResponse | null;
  isVisible: boolean;
  onClose: () => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  onAcceptChange: (changeId: string) => void;
  onRejectChange: (changeId: string) => void;
}

interface ChangeWithStatus {
  id: string;
  type: 'add' | 'delete' | 'modify';
  original: string;
  improved: string;
  line_number: number;
  status: 'pending' | 'accepted' | 'rejected';
}

const DiffViewer: React.FC<DiffViewerProps> = ({
  improvementData,
  isVisible,
  onClose,
  onAcceptAll,
  onRejectAll,
  onAcceptChange,
  onRejectChange
}) => {
  const [changesWithStatus, setChangesWithStatus] = useState<ChangeWithStatus[]>([]);
  const [showOriginal, setShowOriginal] = useState(true);
  const [showImproved, setShowImproved] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);

  // improvementDataが変わったときにchangesWithStatusを更新
  React.useEffect(() => {
    if (improvementData?.changes) {
      setChangesWithStatus(
        improvementData.changes.map(change => ({
          ...change,
          status: 'pending' as const
        }))
      );
    }
  }, [improvementData]);

  // 変更の承認・拒否処理
  const handleAcceptChange = (changeId: string) => {
    setChangesWithStatus(prev =>
      prev.map(change =>
        change.id === changeId ? { ...change, status: 'accepted' } : change
      )
    );
    onAcceptChange(changeId);
  };

  const handleRejectChange = (changeId: string) => {
    setChangesWithStatus(prev =>
      prev.map(change =>
        change.id === changeId ? { ...change, status: 'rejected' } : change
      )
    );
    onRejectChange(changeId);
  };

  // 全て承認
  const handleAcceptAll = () => {
    setChangesWithStatus(prev =>
      prev.map(change => ({ ...change, status: 'accepted' }))
    );
    onAcceptAll();
  };

  // 全て拒否
  const handleRejectAll = () => {
    setChangesWithStatus(prev =>
      prev.map(change => ({ ...change, status: 'rejected' }))
    );
    onRejectAll();
  };

  // リセット
  const handleReset = () => {
    setChangesWithStatus(prev =>
      prev.map(change => ({ ...change, status: 'pending' }))
    );
  };

  // 統計情報を計算
  const stats = React.useMemo(() => {
    const accepted = changesWithStatus.filter(c => c.status === 'accepted').length;
    const rejected = changesWithStatus.filter(c => c.status === 'rejected').length;
    const pending = changesWithStatus.filter(c => c.status === 'pending').length;
    return { accepted, rejected, pending, total: changesWithStatus.length };
  }, [changesWithStatus]);

  if (!isVisible || !improvementData) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-6xl h-[90vh] flex flex-col">
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Sparkles className="w-5 h-5 text-blue-600" />
              <CardTitle>AI改善提案</CardTitle>
              <Badge variant="outline">
                {stats.total}件の変更提案
              </Badge>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={() => setIsExpanded(!isExpanded)}>
                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                詳細
              </Button>
              <Button variant="outline" size="sm" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
          {/* 統計とアクション */}
          <div className="flex items-center justify-between pt-4">
            <div className="flex items-center space-x-4 text-sm">
              <span className="text-green-600">承認: {stats.accepted}</span>
              <span className="text-red-600">拒否: {stats.rejected}</span>
              <span className="text-gray-600">保留: {stats.pending}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={handleReset}>
                <RotateCcw className="w-4 h-4 mr-1" />
                リセット
              </Button>
              <Button variant="outline" size="sm" onClick={handleRejectAll}>
                <X className="w-4 h-4 mr-1" />
                全て拒否
              </Button>
              <Button size="sm" onClick={handleAcceptAll}>
                <Check className="w-4 h-4 mr-1" />
                全て承認
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-hidden p-0">
          <div className="h-full flex">
            {/* 変更リスト */}
            <div className="w-1/3 border-r">
              <div className="p-4 border-b bg-gray-50">
                <h3 className="font-medium text-sm">変更一覧</h3>
                <div className="flex items-center space-x-2 mt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => setShowOriginal(!showOriginal)}
                  >
                    {showOriginal ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                    元の文章
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => setShowImproved(!showImproved)}
                  >
                    {showImproved ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                    改善案
                  </Button>
                </div>
              </div>
              
              <ScrollArea className="h-[calc(100%-120px)]">
                <div className="p-4 space-y-3">
                  {changesWithStatus.map((change, index) => (
                    <div
                      key={change.id}
                      className={`border rounded-lg p-3 ${
                        change.status === 'accepted' ? 'border-green-200 bg-green-50' :
                        change.status === 'rejected' ? 'border-red-200 bg-red-50' :
                        'border-gray-200 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-gray-600">
                          変更 #{index + 1}
                        </span>
                        <Badge 
                          variant={
                            change.type === 'add' ? 'default' :
                            change.type === 'delete' ? 'destructive' :
                            'secondary'
                          }
                          className="text-xs"
                        >
                          {change.type === 'add' ? '追加' :
                           change.type === 'delete' ? '削除' :
                           '修正'}
                        </Badge>
                      </div>

                      {showOriginal && change.original && (
                        <div className="mb-2">
                          <p className="text-xs text-gray-500 mb-1">元の文章:</p>
                          <p className="text-sm bg-red-50 p-2 rounded text-red-800 line-through">
                            {change.original}
                          </p>
                        </div>
                      )}

                      {showImproved && change.improved && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">改善案:</p>
                          <p className="text-sm bg-green-50 p-2 rounded text-green-800">
                            {change.improved}
                          </p>
                        </div>
                      )}

                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant={change.status === 'accepted' ? 'default' : 'outline'}
                          className="flex-1 text-xs"
                          onClick={() => handleAcceptChange(change.id)}
                        >
                          <Check className="w-3 h-3 mr-1" />
                          承認
                        </Button>
                        <Button
                          size="sm"
                          variant={change.status === 'rejected' ? 'destructive' : 'outline'}
                          className="flex-1 text-xs"
                          onClick={() => handleRejectChange(change.id)}
                        >
                          <X className="w-3 h-3 mr-1" />
                          拒否
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>

            {/* プレビューエリア */}
            <div className="flex-1 flex flex-col">
              <div className="p-4 border-b bg-gray-50">
                <h3 className="font-medium text-sm">プレビュー</h3>
              </div>
              
              <div className="flex-1 flex">
                {/* 元の文章 */}
                {showOriginal && (
                  <div className="w-1/2 border-r">
                    <div className="p-3 bg-red-50 border-b">
                      <h4 className="text-sm font-medium text-red-800">元の文章</h4>
                    </div>
                    <ScrollArea className="h-[calc(100%-40px)]">
                      <div className="p-4">
                        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                          {improvementData.original_text}
                        </pre>
                      </div>
                    </ScrollArea>
                  </div>
                )}

                {/* 改善された文章 */}
                {showImproved && (
                  <div className={showOriginal ? "w-1/2" : "w-full"}>
                    <div className="p-3 bg-green-50 border-b">
                      <h4 className="text-sm font-medium text-green-800">改善案</h4>
                    </div>
                    <ScrollArea className="h-[calc(100%-40px)]">
                      <div className="p-4">
                        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                          {improvementData.improved_text}
                        </pre>
                      </div>
                    </ScrollArea>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>

        {/* 説明エリア（展開時のみ表示） */}
        {isExpanded && improvementData.explanation && (
          <div className="border-t p-4 bg-blue-50">
            <h4 className="text-sm font-medium text-blue-800 mb-2">AI からの説明</h4>
            <p className="text-sm text-blue-700">
              {improvementData.explanation}
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default DiffViewer; 