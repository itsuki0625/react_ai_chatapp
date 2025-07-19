"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { PersonalStatement, StatementStatus, ChatSession, DesiredUniversity, convertToPersonalStatement } from '@/types/statement';
import { getStatement, createStatement, updateStatement, improveStatementWithAI, StatementImprovementResponse } from '@/services/statementService';
import { getDesiredSchools, DesiredSchool } from '@/services/universityService';
import { useChat } from '@/store/chat/ChatContext';
import { ChatTypeEnum } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Save, 
  Settings, 
  MessageCircle, 
  FileText,
  Sparkles,
  History,
  ChevronDown,
  GripVertical,
  X,
  CheckCircle,
  Minus,
  MessageCircle as MessageCircleIcon
} from 'lucide-react';
import { toast } from 'sonner';
import AIAnalysisPanel from './AIAnalysisPanel';

interface Props {
  statementId?: string;
}

interface Change {
  original: string;
  improved: string;
  reason: string;
}

interface SelectedSuggestion {
  step: string;
  suggestionIndex: number;
  suggestionText: string;
  changes: Change[];
}

export default function StatementEditor({ statementId }: Props) {
  const router = useRouter();
  const { fetchSessions, sessions } = useChat();
  
  // Statement data
  const [statement, setStatement] = useState<PersonalStatement | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState<StatementStatus>(StatementStatus.DRAFT);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [submissionDeadline, setSubmissionDeadline] = useState('');
  const [selectedUniversity, setSelectedUniversity] = useState<DesiredSchool | null>(null);
  const [selectedSelfAnalysisChat, setSelectedSelfAnalysisChat] = useState<ChatSession | null>(null);
  const [desiredSchools, setDesiredSchools] = useState<DesiredSchool[]>([]);
  
  // Chat data
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'ai'>('ai');
  const [activeChatId, setActiveChatId] = useState<string>('default');
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [chatSessions, setChatSessions] = useState<any[]>([
    { id: 'default', title: 'デフォルトチャット', messageCount: 0 }
  ]);
  const [chatPanelWidth, setChatPanelWidth] = useState(384);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const debouncedSaveRef = useRef<NodeJS.Timeout | null>(null);
  
  // UI state
  const [showSettings, setShowSettings] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [isResizing, setIsResizing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // AI improvement state
  const [showDiffViewer, setShowDiffViewer] = useState(false);
  const [improvementData, setImprovementData] = useState<StatementImprovementResponse | null>(null);
  const [isGeneratingImprovement, setIsGeneratingImprovement] = useState(false);
  
  // Selected suggestion state
  const [selectedSuggestion, setSelectedSuggestion] = useState<SelectedSuggestion | null>(null);
  const [appliedChanges, setAppliedChanges] = useState<Set<string>>(new Set());

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize data
  useEffect(() => {
    const initializeData = async () => {
      console.log('=== Initialize Data Started ===');
      try {
        // 志望大学一覧を取得
        console.log('Fetching desired schools...');
        const desiredSchoolsData = await getDesiredSchools();
        console.log('Desired schools fetched:', desiredSchoolsData);
        setDesiredSchools(desiredSchoolsData);
        
        // 自己分析チャット一覧を取得
        console.log('Fetching self analysis sessions...');
        await fetchSessions(ChatTypeEnum.SELF_ANALYSIS);
        console.log('Self analysis sessions fetch completed');

        if (statementId) {
          const apiStatement = await getStatement(statementId);
          const foundStatement = convertToPersonalStatement(apiStatement);
          
          setStatement(foundStatement);
          setTitle(foundStatement.title || '');
          setContent(foundStatement.content || '');
          setStatus(foundStatement.status);
          setKeywords(foundStatement.keywords || []);
          setSubmissionDeadline(foundStatement.submissionDeadline || '');
          
          // Find university from desired schools
          const university = desiredSchoolsData.find((school: DesiredSchool) => 
            school.university?.name === foundStatement.universityName
          );
          setSelectedUniversity(university || null);
        }
      } catch (error) {
        console.error('Failed to load data:', error);
        toast.error('データの読み込みに失敗しました');
      }
    };
    
    initializeData();
  }, [statementId, fetchSessions]);

  // Handle self-analysis chat selection when sessions are loaded
  useEffect(() => {
    if (statement?.selfAnalysisChatId && sessions.length > 0) {
      const selfAnalysisChat = sessions.find(session => session.id === statement.selfAnalysisChatId);
      if (selfAnalysisChat && selfAnalysisChat.status !== 'ARCHIVED') {
        setSelectedSelfAnalysisChat({
          id: selfAnalysisChat.id,
          title: selfAnalysisChat.title || '無題のチャット',
          messageCount: 0,
          updatedAt: selfAnalysisChat.updated_at || selfAnalysisChat.created_at || new Date().toISOString(),
          createdAt: selfAnalysisChat.created_at || new Date().toISOString()
        });
      } else if (selfAnalysisChat && selfAnalysisChat.status === 'ARCHIVED') {
        setSelectedSelfAnalysisChat(null);
        console.log('Selected self-analysis chat has been archived and was deselected');
      }
    }
  }, [statement, sessions]);

  // Update word count
  useEffect(() => {
    setWordCount(content.length);
  }, [content]);

  // Handle panel resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newWidth = containerRect.right - e.clientX;
      
      // Set min/max constraints
      const minWidth = 300;
      const maxWidth = Math.min(800, containerRect.width * 0.6);
      
      const constrainedWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));
      setChatPanelWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const handleResizeStart = () => {
    setIsResizing(true);
  };

  const handleSave = async () => {
    if (!content.trim()) {
      toast.error('内容を入力してください');
      return;
    }

    const saveData = {
      title: title || '無題の志望理由書',
      content,
      status: statementId ? status : StatementStatus.DRAFT,
      desired_department_id: selectedUniversity?.desired_departments?.[0]?.id || undefined,
      self_analysis_chat_id: selectedSelfAnalysisChat?.id || undefined,
      submission_deadline: submissionDeadline || undefined,
      keywords: keywords.length > 0 ? keywords : undefined
    };

    try {
      if (statementId) {
        console.log('Updating statement...');
        const updatedStatement = await updateStatement(statementId, saveData);
        console.log('Statement updated:', updatedStatement);
        const convertedStatement = convertToPersonalStatement(updatedStatement);
        setStatement(convertedStatement);
        toast.success('志望理由書が更新されました');
      } else {
        console.log('Creating new statement...');
        const createdStatement = await createStatement(saveData);
        console.log('Statement created:', createdStatement);
        const convertedStatement = convertToPersonalStatement(createdStatement);
        setStatement(convertedStatement);
        toast.success('志望理由書が作成されました');
        
        // Redirect to edit page
        router.push(`/student/statement/${createdStatement.id}/edit`);
      }

      const convertedStatement = convertToPersonalStatement(savedStatement);
        setStatement(convertedStatement);
      
      if (!statementId) {
        router.push(`/student/statement/${savedStatement.id}/edit`);
      }
      
      toast.success('志望理由書を保存しました');
    } catch (error) {
      console.error('Error saving statement:', error);
      toast.error('保存中にエラーが発生しました');
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || isAiTyping) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sessionId: activeChatId,
      role: 'user',
      content: newMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsAiTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sessionId: activeChatId,
        role: 'assistant',
        content: generateMockResponse(newMessage),
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsAiTyping(false);
    }, 1500);
  };

  // Diff viewer handlers
  const handleAcceptAllChanges = () => {
    if (improvementData) {
      setContent(improvementData.improved_text);
      setShowDiffViewer(false);
      toast.success('すべての変更を適用しました');
    }
  };

  const handleRejectAllChanges = () => {
    setShowDiffViewer(false);
    toast.info('変更をキャンセルしました');
  };

  const handleAcceptChange = (changeId: string) => {
    // Individual change acceptance logic can be implemented here
    console.log('Accepting change:', changeId);
  };

  const handleRejectChange = (changeId: string) => {
    // Individual change rejection logic can be implemented here
    console.log('Rejecting change:', changeId);
  };

  const getStatusColor = (status: StatementStatus) => {
    switch (status) {
      case StatementStatus.DRAFT: return 'bg-gray-100 text-gray-800';
      case StatementStatus.REVIEW: return 'bg-blue-100 text-blue-800';
      case StatementStatus.REVIEWED: return 'bg-green-100 text-green-800';
      case StatementStatus.FINAL: return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleContentChange = (newContent: string) => {
    setContent(newContent);
  };

  const handleImprovementApplied = () => {
    toast.success('AI添削の改善案が適用されました');
    // 自動保存も実行
    handleSave();
  };

  const handleAutoSave = () => {
    toast.success('AI添削の改善案が適用されました');
    handleSave();
  };

  // Handle suggestion selection from AI panel
  const handleSuggestionClick = (step: string, index: number, suggestionText: string, changes: Change[]) => {
    setSelectedSuggestion({
      step,
      suggestionIndex: index,
      suggestionText,
      changes
    });
  };

  // Apply all changes from selected suggestion
  const handleApplyAllChanges = (changes: Change[]) => {
    let updatedContent = content;
    
    changes.forEach(change => {
      updatedContent = updatedContent.replace(change.original, change.improved);
    });
    
    setContent(updatedContent);
    setSelectedSuggestion(null);
    
    // Mark changes as applied
    const changeIds = changes.map(c => `${c.original}-${c.improved}`);
    setAppliedChanges(prev => new Set([...prev, ...changeIds]));
    
    toast.success(`${changes.length}件の変更を適用しました`);
  };

  // Close suggestion detail overlay
  const handleCloseSuggestionDetail = () => {
    setSelectedSuggestion(null);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white border-b flex-shrink-0">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            onClick={() => router.push('/student/statement')}
          >
            ← 一覧に戻る
          </Button>
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <h1 className="text-lg font-semibold">
              {statementId ? '志望理由書を編集' : '新しい志望理由書'}
            </h1>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <Badge className={getStatusColor(status)}>
            {status === StatementStatus.DRAFT && '下書き'}
            {status === StatementStatus.REVIEW && 'レビュー中'}
            {status === StatementStatus.REVIEWED && 'レビュー済み'}
            {status === StatementStatus.FINAL && '完成版'}
          </Badge>
          <span className="text-sm text-gray-500">{wordCount}文字</span>
          
          {/* AI Improvement Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleGenerateImprovement('general')}
            disabled={!statementId || isGeneratingImprovement || !content.trim()}
          >
            <Wand2 className="w-4 h-4 mr-1" />
            {isGeneratingImprovement ? '生成中...' : 'AI改善'}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="w-4 h-4" />
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            <Save className="w-4 h-4 mr-2" />
            {isLoading ? '保存中...' : '保存'}
          </Button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 bg-white border-b space-y-4 flex-shrink-0">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                志望大学
              </label>
              <Select 
                value={selectedUniversity?.id || ''} 
                onValueChange={(value) => {
                  const university = desiredSchools.find((school: DesiredSchool) => school.id === value);
                  setSelectedUniversity(university || null);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="志望大学を選択" />
                </SelectTrigger>
                <SelectContent>
                  {desiredSchools.map((school: DesiredSchool) => (
                    <SelectItem key={school.id} value={school.id}>
                      {school.preference_order}. {school.university?.name || '大学名不明'} - {school.desired_departments?.map(d => d.department?.name || '学部名不明').join(', ') || '学部情報なし'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                自己分析チャット
              </label>
              <Select 
                value={selectedSelfAnalysisChat?.id || 'none'} 
                onValueChange={(value) => {
                  if (value === 'none') {
                    setSelectedSelfAnalysisChat(null);
                  } else {
                    const chat = sessions.find(session => session.id === value);
                    if (chat && chat.status !== 'ARCHIVED') {
                      setSelectedSelfAnalysisChat({
                        id: chat.id,
                        title: chat.title || '無題のチャット',
                        messageCount: 0,
                        updatedAt: chat.updated_at || chat.created_at || new Date().toISOString(),
                        createdAt: chat.created_at || new Date().toISOString()
                      });
                    }
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="自己分析チャットを選択" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">選択しない</SelectItem>
                  {sessions
                    .filter(session => session.status !== 'ARCHIVED')
                    .map((session) => (
                      <SelectItem key={session.id} value={session.id}>
                        {session.title || '無題のチャット'}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                ステータス
              </label>
              <Select value={status} onValueChange={(value) => setStatus(value as StatementStatus)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={StatementStatus.DRAFT}>下書き</SelectItem>
                  <SelectItem value={StatementStatus.REVIEW}>レビュー中</SelectItem>
                  <SelectItem value={StatementStatus.REVIEWED}>レビュー済み</SelectItem>
                  <SelectItem value={StatementStatus.FINAL}>完成版</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                提出期限
              </label>
              <Input
                type="date"
                value={submissionDeadline || ''}
                onChange={(e) => setSubmissionDeadline(e.target.value)}
              />
            </div>
          </div>
          
          {/* Selected Self-Analysis Chat Info */}
          {selectedSelfAnalysisChat && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center space-x-2">
                <MessageCircle className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">
                  選択中の自己分析チャット: {selectedSelfAnalysisChat.title}
                </span>
              </div>
              <p className="text-xs text-blue-600 mt-1">
                {selectedSelfAnalysisChat.messageCount}件のメッセージ • 
                最終更新: {new Date(selectedSelfAnalysisChat.updatedAt).toLocaleDateString('ja-JP')}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Main Content - 2 Pane Layout */}
      <div className="flex-1 flex overflow-hidden min-h-0" ref={containerRef}>
        {/* Left Pane - Editor */}
        <div className="flex-1 flex flex-col bg-white min-h-0">
          <div className="p-4 border-b flex-shrink-0">
            <Input
              placeholder="志望理由書のタイトルを入力..."
              value={title || ''}
              onChange={(e) => setTitle(e.target.value)}
              className="text-lg font-medium border-none px-0 focus:ring-0"
            />
          </div>
          
          <div className="flex-1 p-4 overflow-hidden">
            <Textarea
              placeholder="志望理由を書き始めてください...&#10;&#10;右側のAIチャットで、文章の改善や質問ができます。"
              value={content || ''}
              onChange={(e) => setContent(e.target.value)}
              className="w-full h-full resize-none border-none focus:ring-0 text-base leading-relaxed overflow-y-auto"
            />
          </div>
        </div>

        {/* Resizer Handle */}
        <div
          className={`w-3 bg-gray-300 hover:bg-blue-400 cursor-col-resize flex-shrink-0 transition-all duration-150 relative group border-l border-r border-gray-200 ${
            isResizing ? 'bg-blue-500 w-4' : ''
          }`}
          onMouseDown={handleResizeStart}
          title="ドラッグしてパネルサイズを調整"
        >
          {/* Resize Icon */}
          <div className="absolute inset-0 flex items-center justify-center">
            <GripVertical className={`w-4 h-4 transition-opacity duration-150 ${
              isResizing ? 'text-white opacity-100' : 'text-gray-500 opacity-60 group-hover:opacity-100 group-hover:text-white'
            }`} />
          </div>
        </div>

        {/* 右側パネル */}
        <div 
          className="bg-gray-50 border-l flex-shrink-0"
          style={{ width: `${chatPanelWidth}px` }}
        >
          <div className="h-full flex flex-col">
            {/* タブヘッダー */}
            <div className="flex border-b bg-white">
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex-1 px-4 py-2 text-sm font-medium ${
                  activeTab === 'chat'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <MessageCircle className="w-4 h-4 mr-2 inline" />
                チャット
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`flex-1 px-4 py-2 text-sm font-medium ${
                  activeTab === 'ai'
                    ? 'border-b-2 border-purple-500 text-purple-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Sparkles className="w-4 h-4 mr-2 inline" />
                AI分析
              </button>
            </div>

            {/* タブコンテンツ */}
            <div className="flex-1 overflow-hidden">
              {activeTab === 'chat' && (
                <div className="h-full bg-white">
                  {/* 既存のチャット機能 */}
                  <div className="p-4 text-center text-gray-500">
                    <MessageCircle className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>チャット機能は開発中です</p>
                  </div>
                </div>
              )}
              
                             {activeTab === 'ai' && (
                 <div className="h-full">
                   {statementId ? (
                     <AIAnalysisPanel
                       statementId={statementId}
                       currentContent={content}
                       onContentChange={setContent}
                       onImprovementApplied={handleAutoSave}
                       onSuggestionClick={handleSuggestionClick}
                     />
                   ) : (
                     <div className="p-4 text-center text-gray-500">
                       <Sparkles className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                       <p>AI分析機能を使用するには、<br/>まず志望理由書を保存してください</p>
                     </div>
                   )}
                 </div>
               )}
            </div>
          </div>
        </div>
      </div>

      {/* Selected Suggestion Detail Overlay */}
      {selectedSuggestion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">変更内容の詳細</h3>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={handleCloseSuggestionDetail}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Selected Suggestion Info */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Badge className="bg-blue-100 text-blue-800">
                    {selectedSuggestion.step}
                  </Badge>
                  <span className="text-sm text-gray-600">
                    提案 #{selectedSuggestion.suggestionIndex + 1}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{selectedSuggestion.suggestionText}</p>
              </div>

              {/* Changes List */}
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
                        <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                        <span className="text-sm font-medium text-green-800">変更後</span>
                      </div>
                      <p className="text-gray-700 whitespace-pre-wrap">
                        {change.improved}
                      </p>
                    </div>
                    
                    {/* 変更理由（吹き出し） */}
                    <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                      <div className="flex items-start">
                        <MessageCircleIcon className="w-4 h-4 text-blue-600 mr-2 mt-0.5" />
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
              
              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 mt-6">
                <Button 
                  variant="outline" 
                  onClick={handleCloseSuggestionDetail}
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
        </div>
      )}
    </div>
  );
} 