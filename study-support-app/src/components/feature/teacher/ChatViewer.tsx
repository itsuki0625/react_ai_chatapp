'use client';

import { useEffect, useState } from 'react';
import { 
  ArrowLeft,
  MessageSquare,
  User,
  Bot,
  Clock,
  FileText,
  Download,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useRouter } from 'next/navigation';
import { MockTenantAPI } from '@/lib/mock/tenant-api';
import { ChatMessage } from '@/lib/mock/student-data';
import { StudentChatSession } from '@/types/tenant';

interface ChatViewerProps {
  studentId: string;
  sessionId: string;
}

interface ChatData {
  session: StudentChatSession;
  messages: ChatMessage[];
  studentName: string;
}

export default function ChatViewer({ studentId, sessionId }: ChatViewerProps) {
  const router = useRouter();
  const [chatData, setChatData] = useState<ChatData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChatData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // セッション情報と学生詳細を取得
        const [studentDetails, messages] = await Promise.all([
          MockTenantAPI.getStudentDetails(studentId),
          MockTenantAPI.getChatMessages(sessionId)
        ]);

        const session = studentDetails.chatSessions.find(s => s.id === sessionId);
        if (!session) {
          throw new Error('チャットセッションが見つかりません');
        }

        setChatData({
          session,
          messages,
          studentName: studentDetails.student.fullName
        });
      } catch (err) {
        console.error('Failed to fetch chat data:', err);
        setError('チャットデータの取得に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchChatData();
  }, [studentId, sessionId]);

  const handleExport = () => {
    if (!chatData) return;
    
    // チャット履歴をテキスト形式でエクスポート
    const chatText = chatData.messages.map(msg => {
      const timestamp = new Date(msg.timestamp).toLocaleString('ja-JP');
      const sender = msg.sender === 'user' ? chatData.studentName : 'AI';
      return `[${timestamp}] ${sender}: ${msg.content}`;
    }).join('\n\n');

    const blob = new Blob([chatText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_${chatData.studentName}_${chatData.session.id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return <ChatViewerSkeleton />;
  }

  if (error || !chatData) {
    return (
      <ChatViewerError 
        error={error || 'データが見つかりません'} 
        onRetry={() => window.location.reload()}
        onBack={() => router.back()}
      />
    );
  }

  const { session, messages, studentName } = chatData;

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            戻る
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">チャット履歴</h1>
            <p className="text-gray-600">
              {studentName}さん - {session.title}
            </p>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            エクスポート
          </Button>
        </div>
      </div>

      {/* セッション情報 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <MessageSquare className="h-5 w-5 mr-2" />
                {session.title}
              </CardTitle>
              <CardDescription>
                {getSessionTypeDisplayName(session.type)} - {session.messageCount}件のメッセージ
              </CardDescription>
            </div>
            <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
              {getStatusDisplayName(session.status)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-600">作成日時</p>
              <p className="font-medium">
                {new Date(session.createdAt).toLocaleString('ja-JP')}
              </p>
            </div>
            <div>
              <p className="text-gray-600">最終メッセージ</p>
              <p className="font-medium">
                {new Date(session.lastMessageAt).toLocaleString('ja-JP')}
              </p>
            </div>
            <div>
              <p className="text-gray-600">セッション種別</p>
              <p className="font-medium">{getSessionTypeDisplayName(session.type)}</p>
            </div>
            <div>
              <p className="text-gray-600">ステータス</p>
              <p className="font-medium">{getStatusDisplayName(session.status)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* チャットメッセージ */}
      <Card>
        <CardHeader>
          <CardTitle>メッセージ履歴</CardTitle>
          <CardDescription>
            時系列順でメッセージを表示しています
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>メッセージがありません</p>
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble 
                  key={message.id} 
                  message={message} 
                  studentName={studentName}
                />
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* 分析サマリー */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="h-5 w-5 mr-2" />
            チャット分析
          </CardTitle>
          <CardDescription>
            このチャットセッションの分析情報
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {messages.filter(m => m.sender === 'user').length}
              </p>
              <p className="text-sm text-gray-600">学生のメッセージ</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {messages.filter(m => m.sender === 'ai').length}
              </p>
              <p className="text-sm text-gray-600">AIの応答</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-600">
                {Math.round(messages.reduce((sum, m) => sum + m.content.length, 0) / messages.length) || 0}
              </p>
              <p className="text-sm text-gray-600">平均文字数</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-600">
                {Math.round(
                  (new Date(session.lastMessageAt).getTime() - new Date(session.createdAt).getTime()) 
                  / (1000 * 60)
                ) || 0}
              </p>
              <p className="text-sm text-gray-600">継続時間（分）</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MessageBubble({ message, studentName }: { message: ChatMessage; studentName: string }) {
  const isUser = message.sender === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback>
            {isUser ? (
              <User className="h-4 w-4" />
            ) : (
              <Bot className="h-4 w-4" />
            )}
          </AvatarFallback>
        </Avatar>
        <div className={`${isUser ? 'mr-2' : 'ml-2'}`}>
          <div className={`
            px-4 py-2 rounded-lg
            ${isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-900'
            }
          `}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
          <div className={`flex items-center mt-1 text-xs text-gray-500 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <Clock className="h-3 w-3 mr-1" />
            <span>
              {isUser ? studentName : 'AI'} - {' '}
              {new Date(message.timestamp).toLocaleString('ja-JP', {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function getSessionTypeDisplayName(type: string): string {
  const typeNames = {
    self_analysis: '自己分析',
    statement_support: '志望理由書作成支援',
    general: '一般相談'
  };
  return typeNames[type as keyof typeof typeNames] || type;
}

function getStatusDisplayName(status: string): string {
  const statusNames = {
    active: 'アクティブ',
    completed: '完了',
    archived: 'アーカイブ'
  };
  return statusNames[status as keyof typeof statusNames] || status;
}

function ChatViewerSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
      <div className="h-32 bg-gray-200 rounded animate-pulse"></div>
      <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
      <div className="h-48 bg-gray-200 rounded animate-pulse"></div>
    </div>
  );
}

function ChatViewerError({ 
  error, 
  onRetry, 
  onBack 
}: { 
  error: string; 
  onRetry: () => void;
  onBack: () => void;
}) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          エラーが発生しました
        </h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <div className="flex space-x-2 justify-center">
          <Button variant="outline" onClick={onBack}>
            戻る
          </Button>
          <Button onClick={onRetry}>
            再試行
          </Button>
        </div>
      </div>
    </div>
  );
}