import React, { useState, useRef, useEffect } from 'react';
import { Textarea } from "@/components/ui/textarea"; // Shadcn/ui の Textarea
import { Button } from "@/components/ui/button"; // Shadcn/ui の Button
import { SendHorizonal } from 'lucide-react'; // 送信アイコン

interface MessageInputProps {
  onSendMessage: (content: string) => void; // メッセージ送信時のコールバック関数
  isLoading: boolean; // ローディング状態（送信ボタンを無効化するため）
}

const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSendMessage = () => {
    const content = message.trim();
    if (content && !isLoading) {
      onSendMessage(content);
      setMessage(''); // 送信後にテキストエリアをクリア
      // 送信後に高さをリセット
      if (textareaRef.current) {
          textareaRef.current.style.height = 'auto'; 
      }
      // 送信後にフォーカスを戻す（モバイルでは挙動が異なる場合あり）
      // textareaRef.current?.focus(); 
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Shift + Enter で改行、Enterのみで送信
    if (event.key === 'Enter' && !event.shiftKey && !isLoading) {
      event.preventDefault(); // デフォルトの改行動作をキャンセル
      handleSendMessage();
    }
  };

  // Textareaの高さを自動調整する
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // 一旦高さをリセット
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 150; // 最大高さをピクセルで指定
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, [message]);

  return (
    <div className="p-2 sm:p-4 border-t bg-background flex items-end space-x-2"> {/* items-end に変更 */} 
      <Textarea
        ref={textareaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="メッセージを入力 (Shift+Enterで改行)..."
        className="flex-1 resize-none overflow-y-auto bg-muted border-0 rounded-lg focus-visible:ring-1 focus-visible:ring-ring min-h-[40px] max-h-[150px] text-sm p-2 leading-tight" // スタイル調整
        rows={1} // 初期表示は1行
        disabled={isLoading}
      />
      <Button
        onClick={handleSendMessage}
        disabled={isLoading || message.trim().length === 0}
        size="icon"
        className="flex-shrink-0 self-end" // ボタンを下に揃える
      >
        <SendHorizonal className="h-4 w-4" />
        <span className="sr-only">送信</span>
      </Button>
    </div>
  );
};

export default MessageInput; 