import React, { KeyboardEvent, useRef, useEffect } from 'react';
import useChat from '../../hooks/useChat';
import Button from '../common/Button';

const Chat: React.FC = () => {
  const {
    messages,
    input,
    setInput,
    sendMessage,
    clearHistory,
    isStreaming,
    sessionId,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="p-5 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-xl font-bold">AO塾チャット</h2>
        <div className="flex gap-2 items-center">
          {sessionId && (
            <span className="text-sm text-gray-500">
              Session: {sessionId.slice(0, 8)}
            </span>
          )}
          <Button
            label="履歴を削除"
            onClick={clearHistory}
            disabled={isStreaming}
          />
        </div>
      </div>

      <div className="h-[500px] overflow-y-auto border border-gray-200 rounded-lg p-4 mb-4 bg-white">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-5">
            メッセージはまだありません
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`my-2 p-3 rounded-lg max-w-[80%] ${
                msg.sender === 'AI'
                  ? 'bg-blue-50 mr-auto'
                  : 'bg-green-50 ml-auto'
              }`}
            >
              <div className="text-xs text-gray-500">
                {msg.sender} - {msg.timestamp}
              </div>
              <div className="mt-1 whitespace-pre-wrap">
                {msg.text}
                {msg.isStreaming && (
                  <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          className="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="メッセージを入力..."
        />
        <Button
          label={isStreaming ? "送信中..." : "送信"}
          onClick={sendMessage}
          disabled={isStreaming || !input.trim()}
        />
      </div>
    </div>
  );
};

export default Chat;

