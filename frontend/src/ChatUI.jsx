import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot } from 'lucide-react';

const ChatUI = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "สวัสดีครับ! ผมคือ IT Support Helpdesk Bot ยินดีช่วยเหลือครับ วันนี้มีอะไรให้ผมช่วยไหมครับ?",
      sender: "bot",
      source: "system"
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      sender: "user"
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userMessage.text })
      });

      const data = await response.json();

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: data.answer,
        sender: "bot",
        source: data.source,
        intent: data.intent,
        confidence: data.confidence
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: "ขออภัยครับ ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ในขณะนี้ โปรดตรวจสอบว่า Backend API เปิดใช้งานอยู่",
        sender: "bot",
        source: "error"
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="chat-wrapper">
      <div className="chat-header">
        <div className="header-icon">
          <Bot />
        </div>
        <div className="header-info">
          <h1>IT Support AI</h1>
          <p><span className="status-dot"></span> Online & Ready to help</p>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-group ${msg.sender}`}>
            <div className="message-bubble">
              {msg.text}
            </div>
            <div className="message-meta">
              {msg.sender === 'bot' && msg.source === 'local_intent' && (
                <span className="source-badge" title="Fast & Free (No LLM Tokens Used)">
                  ⚡ Local Match ({msg.intent}) • {msg.confidence ? (msg.confidence * 100).toFixed(1) : "100"}% Confidence
                </span>
              )}
              {msg.sender === 'bot' && msg.source.startsWith('LLM') && (
                <span className="source-badge" title="Generated via AI Domain Expert">🧠 {msg.source}</span>
              )}
              {msg.sender === 'bot' && msg.source === 'error' && (
                <span className="source-badge" style={{color: '#ef4444', background: 'rgba(239, 68, 68, 0.2)'}}>⚠️ Error</span>
              )}
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="message-group bot">
            <div className="message-bubble">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-form">
          <input
            type="text"
            className="chat-input"
            placeholder="พิมพ์ปัญหาของคุณที่นี่ (เช่น ลืมรหัสผ่าน, เน็ตหลุด)..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isTyping}
          />
          <button type="submit" className="send-button" disabled={!inputValue.trim() || isTyping}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatUI;
