import React, { useState } from 'react';
import { Bot, User, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './Message.css';

function Message({ message }) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={`message ${message.type} ${message.error ? 'error' : ''}`}>
      <div className="message-avatar">
        {message.type === 'user' ? (
          <User size={20} />
        ) : (
          <Bot size={20} />
        )}
      </div>
      
      <div className="message-body">
        <div className="message-content">
          {message.type === 'bot' ? (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          ) : (
            message.content
          )}
        </div>
        
        {message.mode && (
          <div className="message-mode">
            <span className={`mode-badge ${message.mode}`}>
              {message.mode === 'rag' ? 'From Documents' : 'General Knowledge'}
            </span>
          </div>
        )}
        
        {message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <button 
              className="sources-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              <FileText size={16} />
              {message.sources.length} Source{message.sources.length > 1 ? 's' : ''}
              {showSources ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            
            {showSources && (
              <div className="sources-list">
                {message.sources.map((source, idx) => (
                  <div key={idx} className="source-item">
                    <div className="source-header">
                      <FileText size={14} />
                      <span>{source.metadata.source || 'Document'}</span>
                    </div>
                    <div className="source-content">
                      {source.content}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        <div className="message-timestamp">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

export default Message;
