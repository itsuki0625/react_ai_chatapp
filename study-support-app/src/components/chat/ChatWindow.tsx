'use client'; // このコンポーネントはクライアントサイドで動作

import React, { useEffect, useRef } from 'react';
import MessageList from './MessageList';
import { useChat } from '@/store/chat/ChatContext';
import { useSession } from 'next-auth/react';
import { ChatTypeEnum } from '@/types/chat'; // ChatTypeEnumをインポート
import { Loader2, AlertCircle, UserX, MessageSquare } from 'lucide-react';

// ChatWindowProps はほぼ不要になるか、表示に関するオプションのみになる
// interface ChatWindowProps {
//   // chatType?: ChatTypeValue; // Contextから取得
//   // sessionId?: string;    // Contextから取得
// }

const ChatWindow: React.FC = () => {
  const {
    messages,
    isLoading, 
    error,
    sessionId,
    currentChatType,
    fetchMessages, // fetchMessages を useChat から取得
  } = useChat();

  const { data: authSession, status: authStatus } = useSession();
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    // MessageListコンポーネントの末尾にスクロール要素を配置する想定
    const scrollTarget = document.getElementById('messages-end-sentinel');
    if (scrollTarget) {
        scrollTarget.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 履歴読み込みロジック (セッションIDが設定され、メッセージがまだない場合)
  // ChatProvider側でセッションID変更時に履歴を読み込むのが理想だが、
  // ここで明示的にトリガーすることも一時的な手段としてあり得る。
  // ただし、無限ループを避けるための条件やフラグ管理が重要。
  useEffect(() => {
    if (sessionId && messages.length === 0 && authStatus === 'authenticated' && !isLoading) {
      console.log(`ChatWindow: sessionId ${sessionId} detected with no messages. Attempting to load history via fetchMessages.`);
      fetchMessages(sessionId); // ★★★ fetchMessages を呼び出す ★★★
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, messages.length, authStatus, isLoading, fetchMessages]); // fetchMessages を依存配列に追加

  // 認証ローディング状態
  if (authStatus === 'loading') {
    return (
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-white">
        <div className="flex flex-col items-center justify-center">
          <div className="w-16 h-16 relative mb-4">
            <div className="absolute inset-0 rounded-full border-t-4 border-blue-500 animate-spin"></div>
            <div className="absolute inset-3 rounded-full bg-white shadow-md flex items-center justify-center">
              <Loader2 className="w-6 h-6 text-blue-500" />
            </div>
          </div>
          <h3 className="text-lg font-medium text-slate-800">認証情報を確認中</h3>
          <p className="mt-2 text-slate-500 text-center max-w-xs">ログイン情報を検証しています...</p>
        </div>
      </div>
    );
  }

  // 未認証状態
  if (authStatus === 'unauthenticated') {
    return (
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-white">
        <div className="flex flex-col items-center justify-center text-center max-w-md">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mb-4">
            <UserX className="h-8 w-8 text-red-500" />
          </div>
          <h3 className="text-xl font-semibold text-slate-800 mb-3">ログインが必要です</h3>
          <p className="text-slate-600 mb-6">
            チャット機能を利用するには、ログインが必要です。アカウントをお持ちでない場合は、新規登録してください。
          </p>
          <div className="flex space-x-4">
            <a href="/auth/login" className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-150 font-medium">
              ログイン
            </a>
            <a href="/auth/register" className="px-5 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors duration-150 font-medium">
              新規登録
            </a>
          </div>
        </div>
      </div>
    );
  }

  // 履歴読み込み中
  if (isLoading && messages.length === 0 && sessionId) {
    return (
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-white">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-4">
            <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
          </div>
          <h3 className="text-lg font-medium text-slate-800">会話履歴を読み込み中</h3>
          <p className="mt-2 text-slate-500">少々お待ちください...</p>
        </div>
      </div>
    );
  }
  
  // セッションが開始されていない、またはメッセージが空の場合の表示
  if (!sessionId && messages.length === 0) {
    let welcomeMessage = "AIチャットへようこそ";
    let welcomeDescription = "下の入力欄からメッセージを送信して会話を始めましょう";
    
    switch(currentChatType) {
      case ChatTypeEnum.SELF_ANALYSIS:
        welcomeMessage = "自己分析チャットへようこそ";
        welcomeDescription = "あなた自身についての質問をして、自己理解を深めましょう";
        break;
      case ChatTypeEnum.ADMISSION:
        welcomeMessage = "総合型選抜チャットへようこそ";
        welcomeDescription = "入試に関する質問や相談に答えます";
        break;
      case ChatTypeEnum.STUDY_SUPPORT:
        welcomeMessage = "学習支援チャットへようこそ";
        welcomeDescription = "学習に関するサポートや質問に答えます";
        break;
      case ChatTypeEnum.FAQ:
        welcomeMessage = "FAQチャットへようこそ";
        welcomeDescription = "よくある質問に答えます";
        break;
    }
    
    return (
      <div className="flex flex-col flex-1 items-center justify-center h-full p-8 bg-white">
        <div className="max-w-md text-center">
          <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <MessageSquare className="h-10 w-10 text-blue-500" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-3">{welcomeMessage}</h2>
          <p className="text-slate-600 mb-8">
            {welcomeDescription}
          </p>
          
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-medium text-slate-900 mb-3">チャットの始め方</h3>
            <ul className="text-left text-sm text-slate-600 space-y-2">
              <li className="flex items-start">
                <span className="flex-shrink-0 h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center mr-2 mt-0.5">
                  <span className="text-xs font-bold text-blue-600">1</span>
                </span>
                下の入力欄にメッセージを入力
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center mr-2 mt-0.5">
                  <span className="text-xs font-bold text-blue-600">2</span>
                </span>
                送信ボタンをクリックまたはEnterキーを押す
              </li>
              <li className="flex items-start">
                <span className="flex-shrink-0 h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center mr-2 mt-0.5">
                  <span className="text-xs font-bold text-blue-600">3</span>
                </span>
                AIからの応答を待つ
              </li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden h-full w-full"> 
      {error && (
        <div className="p-3 bg-red-50 border-b border-red-200 text-red-700 text-sm flex items-center justify-center shadow-sm">
          <AlertCircle className="h-4 w-4 mr-2" />
          <span>エラー: {typeof error === 'string' ? error : error.message}</span>
        </div>
      )}
      <MessageList />
    </div>
  );
};

export default ChatWindow; 