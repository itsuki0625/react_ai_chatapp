"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { PersonalStatement, StatementStatus, ChatSession, ChatMessage, DesiredUniversity, convertToPersonalStatement } from '@/types/statement';
import { mockChatSessions, mockChatMessages } from '@/lib/mockData/statements';
import { getStatement, createStatement, updateStatement } from '@/services/statementService';
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
import { 
  Save, 
  Settings, 
  MessageCircle, 
  Send, 
  Plus,
  BookOpen,
  Target,
  Calendar,
  FileText,
  Sparkles,
  History,
  ChevronDown,
  GripVertical
} from 'lucide-react';
import { toast } from 'sonner';

interface Props {
  statementId?: string;
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
  const [chatSessions, setChatSessions] = useState<ChatSession[]>(mockChatSessions);
  const [activeChatId, setActiveChatId] = useState<string>('chat-1');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isAiTyping, setIsAiTyping] = useState(false);
  
  // UI state
  const [showSettings, setShowSettings] = useState(false);
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [chatPanelWidth, setChatPanelWidth] = useState(384); // 24rem = 384px
  const [isResizing, setIsResizing] = useState(false);
  
  // Refs
  const chatHistoryRef = useRef<HTMLDivElement>(null);
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
          
          // Find self-analysis chat (will be set by useEffect when sessions are loaded)
          // NOTE: 自己分析チャットの連携は、sessionsが読み込まれた後に別のuseEffectで処理します
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
      if (selfAnalysisChat && selfAnalysisChat.status !== 'ARCHIVED') { // アーカイブされたチャットは選択しない
        setSelectedSelfAnalysisChat({
          id: selfAnalysisChat.id,
          title: selfAnalysisChat.title || '無題のチャット',
          messageCount: 0,
          updatedAt: selfAnalysisChat.updated_at || selfAnalysisChat.created_at || new Date().toISOString(),
          createdAt: selfAnalysisChat.created_at || new Date().toISOString()
        });
      } else if (selfAnalysisChat && selfAnalysisChat.status === 'ARCHIVED') {
        // 既に選択されているチャットがアーカイブされた場合は選択を解除
        setSelectedSelfAnalysisChat(null);
        console.log('Selected self-analysis chat has been archived and was deselected');
      }
    }
  }, [statement, sessions]);

  // Load chat messages separately
  useEffect(() => {
    const chatMessages = mockChatMessages.filter(m => m.sessionId === activeChatId);
    setMessages(chatMessages);
  }, [activeChatId]);

  // Update word count
  useEffect(() => {
    setWordCount(content.length);
  }, [content]);

  // Close chat history dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (chatHistoryRef.current && !chatHistoryRef.current.contains(event.target as Node)) {
        setShowChatHistory(false);
      }
    };

    if (showChatHistory) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showChatHistory]);

  // Handle panel resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newWidth = containerRect.right - e.clientX;
      
      // Set min/max constraints
      const minWidth = 280;
      const maxWidth = containerRect.width * 0.7;
      
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
    console.log('=== Save Button Clicked ===');
    console.log('Title:', title);
    console.log('Content length:', content?.length || 0);
    console.log('Selected University:', selectedUniversity);
    console.log('Selected Self Analysis Chat:', selectedSelfAnalysisChat);
    console.log('Submission Deadline:', submissionDeadline);
    console.log('StatementId (for update):', statementId);
    
    if (!title || !title.trim()) {
      console.log('Validation failed: Title missing');
      toast.error('タイトルを入力してください。');
      return;
    }
    
    // desired_department_idの処理を安全に（志望大学が選択されていない場合はundefined）
    let desired_department_id;
    if (selectedUniversity) {
      if (selectedUniversity.desired_departments && selectedUniversity.desired_departments.length > 0) {
        desired_department_id = selectedUniversity.desired_departments[0].id;
      } else {
        // フォールバック: universitiyのIDを使用 (これは正しくない可能性があるので警告)
        console.warn('No desired_departments found, using university ID as fallback');
        desired_department_id = selectedUniversity.id;
      }
    } else {
      console.log('No university selected, desired_department_id will be undefined');
      desired_department_id = undefined;
    }
    
    const saveData: any = {
      title,
      content,
      status,
      keywords
    };
    
    // 値が存在する場合のみ追加
    if (desired_department_id) {
      saveData.desired_department_id = desired_department_id;
    }
    if (selectedSelfAnalysisChat?.id) {
      saveData.self_analysis_chat_id = selectedSelfAnalysisChat.id;
    }
    if (submissionDeadline && submissionDeadline.trim()) {
      saveData.submission_deadline = submissionDeadline;
    }
    
    console.log('Save data prepared:', saveData);
    
    try {
      if (statementId) {
        console.log('Attempting to update statement...');
        const updatedStatement = await updateStatement(statementId, saveData);
        console.log('Update successful:', updatedStatement);
        const convertedStatement = convertToPersonalStatement(updatedStatement);
        setStatement(convertedStatement);
        toast.success('志望理由書を更新しました。');
      } else {
        console.log('Attempting to create new statement...');
        const createdStatement = await createStatement(saveData);
        console.log('Create successful:', createdStatement);
        const convertedStatement = convertToPersonalStatement(createdStatement);
        setStatement(convertedStatement);
        toast.success('志望理由書を作成しました。');
        // 新規作成の場合、編集ページにリダイレクト
        router.push(`/student/statement/${createdStatement.id}/edit`);
      }
    } catch (error) {
      console.error('Save failed with error:', error);
      console.error('Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        status: (error as any)?.status,
        response: (error as any)?.response?.data
      });
      const errorMessage = error instanceof Error ? error.message : String(error);
      toast.error(`保存に失敗しました: ${errorMessage}`);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

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

    // Mock AI response
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

  const generateMockResponse = (userMessage: string): string => {
    const responses = [
      "この部分についてですが、もう少し具体的な例を挙げることで説得力が増すと思います。どのような体験やエピソードを追加できるでしょうか？",
      "文章の構成は良いですね。ただし、第○段落の論理的な繋がりを強化すると、より一貫性のある志望理由書になります。",
      "この表現は適切ですが、より学術的な言い回しに変更することも検討してみてください。例えば「〜と考えます」を「〜と思料します」など。",
      "志望動機の部分がとても良く書けています。さらに、将来の具体的なビジョンを追加すると、より印象的な志望理由書になるでしょう。"
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const createNewChatSession = () => {
    const newSession: ChatSession = {
      id: `chat-${Date.now()}`,
      title: '新規チャット',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messageCount: 0
    };
    
    setChatSessions(prev => [...prev, newSession]);
    setActiveChatId(newSession.id);
    setMessages([]);
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
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              console.log('=== Settings Button Clicked ===');
              console.log('Current desiredSchools:', desiredSchools);
              console.log('Current sessions:', sessions);
              console.log('Current showSettings:', showSettings);
              setShowSettings(!showSettings);
            }}
          >
            <Settings className="w-4 h-4" />
          </Button>
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            保存
          </Button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 bg-white border-b space-y-4 flex-shrink-0">
          {/* Debug info */}
          {process.env.NODE_ENV === 'development' && (
            <div className="p-2 bg-gray-100 text-xs">
              <div>Debug: desiredSchools length: {desiredSchools.length}</div>
              <div>Debug: sessions total: {sessions.length}, active: {sessions.filter(s => s.status !== 'ARCHIVED').length}</div>
              <div>Debug: selectedUniversity: {selectedUniversity?.id || 'none'}</div>
              <div>Debug: selectedSelfAnalysisChat: {selectedSelfAnalysisChat?.id || 'none'}</div>
            </div>
          )}
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
                    if (chat && chat.status !== 'ARCHIVED') { // アーカイブされたチャットは選択しない
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
                    .filter(session => session.status !== 'ARCHIVED') // アーカイブされたチャットを除外
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
          className={`w-2 bg-gray-200 hover:bg-blue-400 cursor-col-resize flex-shrink-0 transition-colors duration-150 relative group ${
            isResizing ? 'bg-blue-500' : ''
          }`}
          onMouseDown={handleResizeStart}
          title="ドラッグしてパネルサイズを調整"
        >
          {/* Resize Icon */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-150">
            <GripVertical className="w-4 h-4 text-white" />
          </div>
        </div>

        {/* Right Pane - AI Chat */}
        <div 
          className="flex flex-col bg-gray-50 min-h-0 flex-shrink-0" 
          style={{ width: `${chatPanelWidth}px` }}
        >
          {/* Chat Header */}
          <div className="p-4 bg-white border-b flex-shrink-0">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <h2 className="font-semibold">AIアシスタント</h2>
              </div>
              <div className="flex items-center space-x-2">
                <div className="relative" ref={chatHistoryRef}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowChatHistory(!showChatHistory)}
                  >
                    <History className="w-4 h-4 mr-1" />
                    <ChevronDown className={`w-3 h-3 transition-transform ${showChatHistory ? 'rotate-180' : ''}`} />
                  </Button>
                  
                  {/* Chat History Dropdown */}
                  {showChatHistory && (
                    <div className="absolute top-full left-0 mt-1 w-64 bg-white border rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
                      <div className="p-2 border-b bg-gray-50">
                        <div className="text-xs font-medium text-gray-700">チャット履歴</div>
                      </div>
                      <div className="p-1">
                        {chatSessions.map((session) => (
                          <div
                            key={session.id}
                            className={`p-2 rounded cursor-pointer text-sm hover:bg-gray-100 ${
                              activeChatId === session.id 
                                ? 'bg-blue-50 text-blue-800 border border-blue-200' 
                                : ''
                            }`}
                            onClick={() => {
                              setActiveChatId(session.id);
                              setShowChatHistory(false);
                            }}
                          >
                            <div className="font-medium truncate">{session.title}</div>
                            <div className="text-xs text-gray-500">
                              {session.messageCount}件のメッセージ
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={createNewChatSession}
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            {/* Current Chat Info */}
            <div className="text-sm text-gray-600">
              {chatSessions.find(s => s.id === activeChatId)?.title || '新規チャット'}
            </div>
          </div>

          {/* Chat Messages */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border'
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </div>
                    <div className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      {new Date(message.timestamp).toLocaleTimeString('ja-JP', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
              ))}
              
              {isAiTyping && (
                <div className="flex justify-start">
                  <div className="bg-white border p-3 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Chat Input */}
          <div className="p-4 bg-white border-t flex-shrink-0">
            <div className="flex space-x-2">
              <Textarea
                placeholder="AIに質問や改善依頼をしてください..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                className="flex-1 min-h-[60px] max-h-[120px]"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!newMessage.trim() || isAiTyping}
                className="self-end"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Shift+Enterで改行、Enterで送信
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 