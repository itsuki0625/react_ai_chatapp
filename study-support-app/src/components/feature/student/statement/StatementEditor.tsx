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
import { 
  Save, 
  Settings, 
  MessageCircle, 
  FileText,
  Sparkles,
  GripVertical,
  Wand2,
  Eye
} from 'lucide-react';
import { toast } from 'sonner';
import ChatPane from './editor/ChatPane';
import DiffViewer from './editor/DiffViewer';

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
  
  // UI state
  const [showSettings, setShowSettings] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [chatPanelWidth, setChatPanelWidth] = useState(384); // 24rem = 384px
  const [isResizing, setIsResizing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // AI improvement state
  const [showDiffViewer, setShowDiffViewer] = useState(false);
  const [improvementData, setImprovementData] = useState<StatementImprovementResponse | null>(null);
  const [isGeneratingImprovement, setIsGeneratingImprovement] = useState(false);
  
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
    try {
      setIsLoading(true);
      
      const statementData = {
        title: title || '',
        content: content || '',
      status,
        desired_department_id: selectedUniversity?.id,
        self_analysis_chat_id: selectedSelfAnalysisChat?.id,
        submission_deadline: submissionDeadline || undefined,
      keywords
    };
    
      let savedStatement;
      if (statementId) {
        savedStatement = await updateStatement(statementId, statementData);
      } else {
        savedStatement = await createStatement(statementData);
      }

      const convertedStatement = convertToPersonalStatement(savedStatement);
        setStatement(convertedStatement);
      
      if (!statementId) {
        router.push(`/student/statement/${savedStatement.id}/edit`);
      }
      
      toast.success('志望理由書を保存しました');
    } catch (error) {
      console.error('Save error:', error);
      const errorMessage = error instanceof Error ? error.message : '保存に失敗しました';
      toast.error(`保存に失敗しました: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // AI improvement functions
  const handleGenerateImprovement = async (improvementType: 'general' | 'structure' | 'expression' | 'logic' = 'general') => {
    if (!statementId || !content.trim()) {
      toast.error('志望理由書を保存してから改善機能をお使いください');
      return;
    }

    try {
      setIsGeneratingImprovement(true);
      const improvement = await improveStatementWithAI(statementId, improvementType);
      setImprovementData(improvement);
      setShowDiffViewer(true);
      toast.success('AI改善提案を生成しました');
    } catch (error) {
      console.error('Improvement generation error:', error);
      toast.error('AI改善提案の生成に失敗しました');
    } finally {
      setIsGeneratingImprovement(false);
    }
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
          className={`w-2 bg-gray-200 hover:bg-blue-400 cursor-col-resize flex-shrink-0 transition-colors duration-150 relative group ${
            isResizing ? 'bg-blue-500' : ''
          }`}
          onMouseDown={handleResizeStart}
          title="ドラッグしてパネルサイズを調整"
        >
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-150">
            <GripVertical className="w-4 h-4 text-white" />
          </div>
        </div>

        {/* Right Pane - AI Chat */}
        <div 
          className="flex flex-col bg-gray-50 min-h-0 flex-shrink-0" 
          style={{ width: `${chatPanelWidth}px` }}
        >
          <ChatPane 
            statementId={statementId} 
            isVisible={true}
          />
        </div>
      </div>

      {/* Diff Viewer Modal */}
      <DiffViewer
        improvementData={improvementData}
        isVisible={showDiffViewer}
        onClose={() => setShowDiffViewer(false)}
        onAcceptAll={handleAcceptAllChanges}
        onRejectAll={handleRejectAllChanges}
        onAcceptChange={handleAcceptChange}
        onRejectChange={handleRejectChange}
      />
    </div>
  );
} 