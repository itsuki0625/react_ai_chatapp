'use client'; // このコンポーネントはクライアントサイドで動作

import React, { useEffect, useRef, useCallback } from 'react';
import MessageList from './MessageList';
import ChatMessageItemDisplay from './ChatMessage';
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
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const userScrolledUpRef = useRef<boolean>(false);
  const prevMessagesLengthRef = useRef<number>(0);

  const scrollToBottomOrPrevious = useCallback(() => {
    if (userScrolledUpRef.current) {
      // ユーザーがスクロールアップしている場合、何もしない
      return;
    }

    if (chatContainerRef.current) {
      const { scrollHeight, clientHeight } = chatContainerRef.current;
      // 常に最下部にスクロール
      chatContainerRef.current.scrollTop = scrollHeight - clientHeight;
    }
  }, []);

  // メッセージリストが変更されたときにスクロール処理を呼び出す
  // isLoading ストリーミングの開始と終了時など、ロード状態の変化でもスクロール
  useEffect(() => {
    // 初期ロード時やメッセージ更新時に最下部にスクロール
    scrollToBottomOrPrevious();
  }, [messages, isLoading, scrollToBottomOrPrevious]);

  // 新しいメッセージが追加された時だけ、強制的に最下部にスクロールするロジック
  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      // 新しいメッセージが追加されたと判断
      // console.log('[DEBUG ChatWindow] New message detected, forcing scroll to bottom.');
      userScrolledUpRef.current = false; // 自動スクロールを有効化
      scrollToBottomOrPrevious(); 
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages, scrollToBottomOrPrevious]);

  // ユーザーのスクロール操作を検出
  useEffect(() => {
    const container = chatContainerRef.current;
    const handleScroll = () => {
      if (container) {
        const { scrollTop, scrollHeight, clientHeight } = container;
        // ユーザーが手動でスクロールアップしたかどうかを判断
        // 閾値（例: 10px）を設けて、わずかな変動は無視する
        if (scrollHeight - scrollTop - clientHeight > 10) { 
          userScrolledUpRef.current = true;
          // console.log('[DEBUG ChatWindow] User scrolled up.');
        } else {
          userScrolledUpRef.current = false;
          // console.log('[DEBUG ChatWindow] User scrolled to bottom.');
        }
      }
    };

    if (container) {
      container.addEventListener('scroll', handleScroll);
    }
    return () => {
      if (container) {
        container.removeEventListener('scroll', handleScroll);
      }
    };
  }, []);

  // 履歴読み込みロジック (セッションIDが設定され、メッセージがまだない場合)
  // ChatProvider側でセッションID変更時に履歴を読み込むのが理想だが、
  // ここで明示的にトリガーすることも一時的な手段としてあり得る。
  // ただし、無限ループを避けるための条件やフラグ管理が重要。
  useEffect(() => {
    if (sessionId && messages.length === 0 && authStatus === 'authenticated' && !isLoading) {
      console.log(`ChatWindow: sessionId ${sessionId} detected with no messages. Attempting to load history via fetchMessages.`);
      fetchMessages(sessionId); // ★★★ fetchMessages を呼び出す ★★★
    }
  }, [sessionId, messages.length, authStatus, isLoading, fetchMessages]);

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
    // SELF_ANALYSIS用の初期AIメッセージを表示
    if (currentChatType === (ChatTypeEnum.SELF_ANALYSIS as any)) {
      return (
        <div className="flex flex-col flex-1 overflow-hidden h-full w-full">
          <div className="flex-1 overflow-y-auto h-full space-y-6 bg-white pb-40 p-4 pt-6">
            <ChatMessageItemDisplay message={{
              id: 'initial-self-analysis',
              sender: 'AI',
              content: 'こんにちは、今日から自己分析を始めましょう！　まずは将来やってみたいことを 1〜2 行で教えていただけますか？',
              timestamp: new Date().toISOString(),
            }} />
          </div>
        </div>
      );
    }
    
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