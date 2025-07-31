"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { 
  CheckCircle, 
  XCircle, 
  Sparkles, 
  Send,
  Loader2,
  User,
  Bot,
  ArrowRight,
  Zap,
  ChevronRight
} from 'lucide-react';
import { 
  AISuggestion, 
  AIChatResponse, 
  chatWithAIForImprovement,
  AIImprovementRequest,
  AIImprovementResponse,
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

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  suggestions?: AISuggestion[];
}

interface PendingSuggestion extends AISuggestion {
  id: string;
  applied: boolean;
  rejected: boolean;
}

export default function AIImprovementPanel({ 
  statementId, 
  currentContent, 
  onContentChange, 
  onImprovementApplied,
  onSuggestionClick
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '志望理由書の改善をお手伝いします！「この部分を改善して」「もっと具体的に書きたい」など、どのような改善をご希望でしょうか？',
      timestamp: new Date().toISOString(),
      suggestions: []
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingSuggestions, setPendingSuggestions] = useState<PendingSuggestion[]>([]);
  
  // 全体添削用の状態
  const [fullImprovementLoading, setFullImprovementLoading] = useState(false);
  const [fullImprovementResults, setFullImprovementResults] = useState<StepImprovement[]>([]);
  const [selectedFocusAreas, setSelectedFocusAreas] = useState<string[]>([]);
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const focusAreaOptions = [
    '文章構造',
    '説得力',
    '具体性',
    '論理的一貫性',
    '表現力',
    '独自性'
  ];

  // 新しいメッセージが追加されたときに自動スクロール
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      // チャット履歴を準備
      const chatHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp
      }));

      // AI チャットを実行
      const response = await chatWithAIForImprovement(statementId, {
        message: inputMessage,
        chat_history: chatHistory,
        current_content: currentContent
      });

      // AI応答メッセージを追加
      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: response.ai_message,
        timestamp: new Date().toISOString(),
        suggestions: response.suggestions
      };

      setMessages(prev => [...prev, aiMessage]);

      // 改善提案があれば保留中の提案として追加
      if (response.suggestions && response.suggestions.length > 0) {
        const newPendingSuggestions = response.suggestions.map(suggestion => ({
          ...suggestion,
          id: `suggestion-${Date.now()}-${Math.random()}`,
          applied: false,
          rejected: false
        }));
        setPendingSuggestions(prev => [...prev, ...newPendingSuggestions]);
      }

    } catch (error) {
      console.error('AI chat failed:', error);
      toast.error('AI との対話中にエラーが発生しました');
      
      // エラーメッセージを追加
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '申し訳ございません。エラーが発生しました。もう一度お試しください。',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // 全体添削の実行
  const handleFullImprovement = async () => {
    try {
      setFullImprovementLoading(true);
      
      // 全体添削開始メッセージを追加
      const startMessage: ChatMessage = {
        id: `full-improvement-start-${Date.now()}`,
        role: 'assistant',
        content: `全体添削を開始します...${selectedFocusAreas.length > 0 ? `\n重点分野: ${selectedFocusAreas.join(', ')}` : ''}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, startMessage]);
      
      const response = await improveStatementWithAI(statementId, {
        personal_statement_id: statementId,
        focus_areas: selectedFocusAreas.length > 0 ? selectedFocusAreas : undefined
      });

      const parsedImprovements = parseAIImprovements(response);
      setFullImprovementResults(parsedImprovements);

      // 全体添削完了メッセージを追加
      const completionMessage: ChatMessage = {
        id: `full-improvement-complete-${Date.now()}`,
        role: 'assistant',
        content: `全体添削が完了しました！${parsedImprovements.length}つのステップで改善案をご提案します。下記の詳細をご確認ください。`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, completionMessage]);

      // 改善提案を抽出してpendingSuggestionsに追加
      const allSuggestions: PendingSuggestion[] = [];
      parsedImprovements.forEach(improvement => {
        improvement.changes.forEach(change => {
          allSuggestions.push({
            id: `full-${Date.now()}-${Math.random()}`,
            type: 'replacement',
            original: change.original,
            improved: change.improved,
            reason: change.reason,
            step: improvement.step,
            applied: false,
            rejected: false
          });
        });
      });

      setPendingSuggestions(prev => [...prev, ...allSuggestions]);
      toast.success('全体添削が完了しました');

    } catch (error) {
      console.error('Full improvement failed:', error);
      toast.error('全体添削中にエラーが発生しました');
      
      // エラーメッセージを追加
      const errorMessage: ChatMessage = {
        id: `full-improvement-error-${Date.now()}`,
        role: 'assistant',
        content: '申し訳ございません。全体添削中にエラーが発生しました。もう一度お試しください。',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setFullImprovementLoading(false);
    }
  };

  const handleApplySuggestion = (suggestionId: string) => {
    const suggestion = pendingSuggestions.find(s => s.id === suggestionId);
    if (!suggestion || suggestion.applied) return;

    let newContent = currentContent;

    if (suggestion.type === 'replacement' && suggestion.original && suggestion.improved) {
      // 置換提案を適用
      newContent = newContent.replace(suggestion.original, suggestion.improved);
    } else if (suggestion.type === 'improvement' && suggestion.content) {
      // 改善提案を適用（文末に追加）
      newContent = newContent + '\n\n' + suggestion.content;
    }

    onContentChange(newContent);
    
    // 提案を適用済みとしてマーク
    setPendingSuggestions(prev => 
      prev.map(s => 
        s.id === suggestionId 
          ? { ...s, applied: true, rejected: false }
          : s
      )
    );

    onImprovementApplied();
    toast.success('改善案が適用されました');
  };

  const handleRejectSuggestion = (suggestionId: string) => {
    setPendingSuggestions(prev => 
      prev.map(s => 
        s.id === suggestionId 
          ? { ...s, applied: false, rejected: true }
          : s
      )
    );
    toast.info('改善案を拒否しました');
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
      'analysis': 'bg-blue-100 text-blue-800',
      'structure': 'bg-green-100 text-green-800',
      'content': 'bg-purple-100 text-purple-800',
      'expression': 'bg-yellow-100 text-yellow-800',
      'coherence': 'bg-pink-100 text-pink-800',
      'polish': 'bg-gray-100 text-gray-800'
    };
    return colors[step as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header - Full Improvement Controls */}
      <div className="p-4 bg-white border-b flex-shrink-0">
        <div className="space-y-3">
          {/* Full Improvement Button */}
          <Button
            onClick={handleFullImprovement}
            disabled={fullImprovementLoading || loading}
            className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800"
          >
            {fullImprovementLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                全体添削中...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                全体添削を実行
              </>
            )}
          </Button>

          {/* Focus Areas Selection */}
          <div className="space-y-2">
            <p className="text-xs text-gray-600">重点分野を選択（任意）</p>
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

      {/* Chat Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="space-y-2">
              {/* Message */}
              <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className="flex items-center space-x-2 mb-1">
                    {message.role === 'user' ? (
                      <User className="w-4 h-4 text-blue-600" />
                    ) : (
                      <Bot className="w-4 h-4 text-purple-600" />
                    )}
                    <span className="text-xs text-gray-500">
                      {message.role === 'user' ? 'あなた' : 'AI アシスタント'}
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <div className={`p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border shadow-sm'
                  }`}>
                    <div className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Suggestions */}
              {message.role === 'assistant' && message.suggestions && message.suggestions.length > 0 && (
                <div className="ml-6 space-y-2">
                  {message.suggestions.map((suggestion, index) => {
                    const pendingSuggestion = pendingSuggestions.find(ps => 
                      ps.original === suggestion.original && 
                      ps.improved === suggestion.improved &&
                      ps.content === suggestion.content
                    );
                    
                    return (
                      <Card key={index} className="bg-gray-50 border-l-4 border-l-purple-400">
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between mb-2">
                            <Badge className={getStepColor(suggestion.step)}>
                              {suggestion.step}
                            </Badge>
                            <span className="text-xs text-gray-500 capitalize">
                              {suggestion.type}
                            </span>
                          </div>

                          {suggestion.type === 'replacement' && suggestion.original && suggestion.improved && (
                            <div className="space-y-2">
                              <div className="grid grid-cols-1 gap-2">
                                <div>
                                  <p className="text-xs text-red-600 font-medium">変更前:</p>
                                  <p className="text-sm bg-red-50 p-2 rounded border-l-2 border-red-300">
                                    {suggestion.original}
                                  </p>
                                </div>
                                <div className="flex items-center justify-center">
                                  <ArrowRight className="w-4 h-4 text-gray-400" />
                                </div>
                                <div>
                                  <p className="text-xs text-green-600 font-medium">変更後:</p>
                                  <p className="text-sm bg-green-50 p-2 rounded border-l-2 border-green-300">
                                    {suggestion.improved}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}

                          {suggestion.type === 'improvement' && suggestion.content && (
                            <div>
                              <p className="text-xs text-blue-600 font-medium mb-1">改善提案:</p>
                              <p className="text-sm bg-blue-50 p-2 rounded border-l-2 border-blue-300">
                                {suggestion.content}
                              </p>
                            </div>
                          )}

                          {suggestion.type === 'general' && suggestion.content && (
                            <div>
                              <p className="text-sm text-gray-700">
                                {suggestion.content}
                              </p>
                            </div>
                          )}

                          <div className="mt-2">
                            <p className="text-xs text-gray-600 mb-2">
                              <span className="font-medium">理由:</span> {suggestion.reason}
                            </p>
                            
                            {pendingSuggestion && !pendingSuggestion.applied && !pendingSuggestion.rejected && (
                              <div className="flex space-x-2">
                                <Button
                                  size="sm"
                                  onClick={() => handleApplySuggestion(pendingSuggestion.id)}
                                  className="bg-green-600 hover:bg-green-700"
                                >
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  適用
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleRejectSuggestion(pendingSuggestion.id)}
                                >
                                  <XCircle className="w-3 h-3 mr-1" />
                                  拒否
                                </Button>
                              </div>
                            )}

                            {pendingSuggestion?.applied && (
                              <Badge variant="default" className="bg-green-100 text-green-800">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                適用済み
                              </Badge>
                            )}

                            {pendingSuggestion?.rejected && (
                              <Badge variant="outline" className="text-gray-500">
                                <XCircle className="w-3 h-3 mr-1" />
                                拒否済み
                              </Badge>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          ))}

          {/* Full Improvement Results - Suggestions Only */}
          {fullImprovementResults.length > 0 && (
            <div className="ml-6 space-y-3">
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                  <Sparkles className="w-4 h-4 mr-2 text-purple-600" />
                  全体添削結果
                </h3>
                <div className="space-y-4">
                  {fullImprovementResults.map((improvement) => (
                    <div key={improvement.step} className="bg-white p-4 rounded-lg border">
                      <div className="flex items-center mb-3">
                        <Badge className={getStepColor(improvement.step)}>
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
                            onClick={() => onSuggestionClick(improvement.step, index, suggestion, improvement.changes)}
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
              </div>
            </div>
          )}

          {/* Loading Message */}
          {(loading || fullImprovementLoading) && (
            <div className="flex justify-start">
              <div className="max-w-[85%]">
                <div className="flex items-center space-x-2 mb-1">
                  <Bot className="w-4 h-4 text-purple-600" />
                  <span className="text-xs text-gray-500">AI アシスタント</span>
                </div>
                <div className="bg-white border shadow-sm p-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                    <span className="text-sm text-gray-600">
                      {fullImprovementLoading ? '全体添削中...' : '考え中...'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 bg-white border-t">
        <div className="flex space-x-2">
          <Textarea
            ref={textareaRef}
            placeholder="「この部分をもっと具体的に」「表現を改善して」など..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 min-h-[60px] max-h-[120px] resize-none"
            disabled={loading || fullImprovementLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || loading || fullImprovementLoading}
            className="self-end"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Shift+Enterで改行、Enterで送信
        </div>
      </div>
    </div>
  );
} 