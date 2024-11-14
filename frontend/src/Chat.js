import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Chat() {
  const [messages, setMessages] = useState(() => {
    const savedMessages = localStorage.getItem('chatHistory');
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [input, setInput] = useState('');
  const [debug, setDebug] = useState('');

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = input;
    
    setMessages(prevMessages => [...prevMessages, { 
      sender: 'ユーザー', 
      text: userMessage,
      timestamp: new Date().toLocaleString()
    }]);
    setInput('');

    try {
      const response = await axios.post('http://localhost:5000/chat', { 
        message: userMessage,
        history: messages
      });
      
      const aiResponse = typeof response.data === 'string' 
        ? response.data 
        : response.data.replay || 'レスポンスの取得に失敗しました';
      
      setMessages(prevMessages => [...prevMessages, { 
        sender: 'AI', 
        text: aiResponse,
        timestamp: new Date().toLocaleString()
      }]);
    } catch (error) {
      console.error('エラー詳細:', error);
      setMessages(prevMessages => [...prevMessages, { 
        sender: 'AI', 
        text: 'エラーが発生しました。',
        timestamp: new Date().toLocaleString()
      }]);
    }
  };

  React.useEffect(() => {
    console.log('更新後のメッセージ一覧:', messages);
  }, [messages]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  const clearHistory = () => {
    if (window.confirm('会話履歴を削除してもよろしいですか？')) {
      setMessages([]);
      localStorage.removeItem('chatHistory');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '10px'
      }}>
        <h2 style={{ margin: 0 }}>チャット</h2>
        <button 
          onClick={clearHistory}
          style={{ 
            padding: '8px 16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          履歴を削除
        </button>
      </div>

      <div style={{ 
        height: '400px', 
        overflowY: 'auto', 
        border: '1px solid #ccc', 
        padding: '10px',
        marginBottom: '10px',
        borderRadius: '5px'
      }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#666', marginTop: '20px' }}>
            メッセージはまだありません
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} style={{
              margin: '10px 0',
              padding: '8px',
              backgroundColor: msg.sender === 'AI' ? '#f0f0f0' : '#e3f2fd',
              borderRadius: '5px',
              maxWidth: '80%',
              marginLeft: msg.sender === 'AI' ? '0' : 'auto',
              marginRight: msg.sender === 'AI' ? 'auto' : '0'
            }}>
              <div style={{ fontSize: '0.8em', color: '#666' }}>
                {msg.sender} - {msg.timestamp}
              </div>
              <div style={{ marginTop: '4px' }}>{msg.text}</div>
            </div>
          ))
        )}
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <input 
          value={input} 
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && sendMessage()}
          style={{ 
            flex: 1, 
            padding: '8px',
            borderRadius: '5px',
            border: '1px solid #ccc'
          }}
          placeholder="メッセージを入力..."
        />
        <button 
          onClick={sendMessage}
          style={{ 
            padding: '8px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          送信
        </button>
      </div>
    </div>
  );
}

export default Chat;
