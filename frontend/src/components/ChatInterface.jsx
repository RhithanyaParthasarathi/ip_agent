import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Trash2, Pencil, Check } from 'lucide-react';
import Message from './Message';
import './ChatInterface.css';

const API_URL = import.meta.env.VITE_API_URL;

function ChatInterface({
  sidebarOpen, messages, onMessagesChange,
  conversationTitle, onRenameConversation,
  conversationId, activeSources
}) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState('');
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

    onMessagesChange([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const body = { question: input };
      if (conversationId) body.conversation_id = String(conversationId);
      if (activeSources && activeSources.length > 0) body.selected_sources = activeSources;

      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer || data.detail || 'No response received.',
        sources: data.sources || [],
        mode: data.mode || 'general',
        timestamp: new Date()
      };

      onMessagesChange([...messages, userMessage, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error. Please make sure the backend is running.',
        error: true,
        timestamp: new Date()
      };
      onMessagesChange([...messages, userMessage, errorMessage]);
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
    onMessagesChange([]);
    try {
      await fetch(`${API_URL}/clear-memory`, { method: 'POST' });
    } catch (error) {
      console.error('Error clearing memory:', error);
    }
  };

  const startEditTitle = () => {
    setTitleDraft(conversationTitle);
    setEditingTitle(true);
  };

  const confirmTitle = () => {
    if (titleDraft.trim()) {
      onRenameConversation(titleDraft.trim());
    }
    setEditingTitle(false);
  };

  return (
    <div className={`chat-interface ${sidebarOpen ? '' : 'full-width'}`}>
      <div className="chat-header">
        <div className="chat-title-area">
          {editingTitle ? (
            <div className="title-edit-row">
              <input
                className="title-edit-input"
                value={titleDraft}
                onChange={(e) => setTitleDraft(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') confirmTitle(); if (e.key === 'Escape') setEditingTitle(false); }}
                autoFocus
              />
              <button className="title-edit-btn" onClick={confirmTitle}><Check size={16} /></button>
            </div>
          ) : (
            <div className="title-display-row">
              <h2>{conversationTitle}</h2>
              <button className="title-edit-trigger" onClick={startEditTitle}>
                <Pencil size={14} />
              </button>
            </div>
          )}
        </div>
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
            <h3>Hi!</h3>
            <p>Ask me anything</p>
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
