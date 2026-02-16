import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Trash2 } from 'lucide-react';
import Message from './Message';
import './ChatInterface.css';

function ChatInterface({ sidebarOpen }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: input }),
      });

      const data = await response.json();

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer,
        sources: data.sources,
        mode: data.mode,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error. Please make sure the backend is running.',
        error: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = async () => {
    setMessages([]);
    try {
      await fetch('http://localhost:8000/clear-memory', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error clearing memory:', error);
    }
  };

  return (
    <div className={`chat-interface ${sidebarOpen ? '' : 'full-width'}`}>
      <div className="chat-header">
        <h2>Chat</h2>
        {messages.length > 0 && (
          <button className="clear-btn" onClick={clearChat}>
            <Trash2 size={18} />
            Clear
          </button>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h3>👋 Welcome to the Company RAG Agent!</h3>
            <p>Ask me anything about your company documents or general questions.</p>
            <div className="example-questions">
              <span className="example-label">Try asking:</span>
              <button onClick={() => setInput("What can you help me with?")}>
                What can you help me with?
              </button>
              <button onClick={() => setInput("Explain how the RAG system works")}>
                Explain how the RAG system works
              </button>
            </div>
          </div>
        ) : (
          messages.map(message => (
            <Message key={message.id} message={message} />
          ))
        )}
        {loading && (
          <div className="message bot loading">
            <div className="message-content">
              <Loader2 size={20} className="spinner" />
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question..."
          rows={1}
          disabled={loading}
        />
        <button 
          onClick={handleSend} 
          disabled={!input.trim() || loading}
          className="send-btn"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
