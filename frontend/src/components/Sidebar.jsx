import React, { useState } from 'react';
import { Upload, FileText, ChevronLeft, Database, Loader2, Plus, MessageSquare, Trash2, Pin, PinOff, Pencil, Check, X, FileX2 } from 'lucide-react';
import './Sidebar.css';

const API_URL = import.meta.env.VITE_API_URL;

function Sidebar({ 
  isOpen, onToggle, collectionInfo, onUploadSuccess,
  conversations, activeConversationId, onNewChat, onSelectConversation, onDeleteConversation,
  onRenameConversation, onTogglePinConversation,
  sources, onToggleSource, onDeleteSource
}) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus('Uploading...');

    const formData = new FormData();
    formData.append('file', file);
    if (activeConversationId) {
      formData.append('conversation_id', activeConversationId);
    }

    try {
      const response = await fetch(`${API_URL}/upload/document`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setUploadStatus(`${data.filename} (${data.chunks} chunks)`);
        onUploadSuccess();
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        setUploadStatus(`Error: ${data.detail}`);
      }
    } catch (error) {
      setUploadStatus(`Error: ${error.message}`);
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const startRename = (conv, e) => {
    e.stopPropagation();
    setRenamingId(conv.id);
    setRenameValue(conv.title);
  };

  const confirmRename = (e) => {
    e.stopPropagation();
    if (renameValue.trim()) {
      onRenameConversation(renamingId, renameValue.trim());
    }
    setRenamingId(null);
  };

  const cancelRename = (e) => {
    e.stopPropagation();
    setRenamingId(null);
  };

  const pinnedConvs = conversations.filter(c => c.pinned);
  const unpinnedConvs = conversations.filter(c => !c.pinned);

  const renderConvItem = (conv) => (
    <div
      key={conv.id}
      className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
      onClick={() => onSelectConversation(conv.id)}
    >
      <MessageSquare size={16} />
      {renamingId === conv.id ? (
        <input
          className="rename-input"
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => {
            if (e.key === 'Enter') confirmRename(e);
            if (e.key === 'Escape') cancelRename(e);
          }}
          autoFocus
        />
      ) : (
        <span className="conversation-title">{conv.title}</span>
      )}
      <div className="conv-actions">
        {renamingId === conv.id ? (
          <>
            <button className="conv-action-btn confirm" onClick={confirmRename}><Check size={13} /></button>
            <button className="conv-action-btn cancel" onClick={cancelRename}><X size={13} /></button>
          </>
        ) : (
          <>
            <button className="conv-action-btn" onClick={(e) => startRename(conv, e)} title="Rename">
              <Pencil size={13} />
            </button>
            <button className="conv-action-btn" onClick={(e) => { e.stopPropagation(); onTogglePinConversation(conv.id); }} title={conv.pinned ? 'Unpin' : 'Pin'}>
              {conv.pinned ? <PinOff size={13} /> : <Pin size={13} />}
            </button>
            <button className="conv-action-btn delete" onClick={(e) => { e.stopPropagation(); onDeleteConversation(conv.id); }}>
              <Trash2 size={13} />
            </button>
          </>
        )}
      </div>
    </div>
  );

  return (
    <>
      <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>Knowledge Base</h2>
          <button className="close-btn" onClick={onToggle}>
            <ChevronLeft size={20} />
          </button>
        </div>

        <div className="sidebar-content">
          {/* Conversations */}
          <div className="conversations-section">
            <button className="new-chat-btn" onClick={onNewChat}>
              <Plus size={18} />
              <span>New Chat</span>
            </button>
            <div className="conversations-list">
              {pinnedConvs.length > 0 && (
                <>
                  <div className="conv-group-label">Pinned</div>
                  {pinnedConvs.map(renderConvItem)}
                </>
              )}
              {unpinnedConvs.length > 0 && (
                <>
                  {pinnedConvs.length > 0 && <div className="conv-group-label">Recent</div>}
                  {unpinnedConvs.map(renderConvItem)}
                </>
              )}
            </div>
          </div>

          <div className="sidebar-divider" />

          {/* Sources for active conversation */}
          <div className="sources-section">
            <h3>Sources</h3>
            {sources.length === 0 ? (
              <p className="no-sources">No sources uploaded for this chat</p>
            ) : (
              <div className="sources-list">
                {sources.map(source => (
                  <div key={source.name} className={`source-item ${source.active ? 'active' : 'inactive'}`}>
                    <label className="source-toggle" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={source.active}
                        onChange={() => onToggleSource(source.name)}
                      />
                      <span className="source-name" title={source.name}>
                        {source.name}
                      </span>
                      <span className="source-chunks">{source.chunks}</span>
                    </label>
                    <button
                      className="source-delete-btn"
                      onClick={() => onDeleteSource(source.name)}
                      title="Remove source"
                    >
                      <FileX2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="sidebar-divider" />

          <div className="upload-section">
            <h3>Upload Documents</h3>
            <label className="upload-btn">
              {uploading ? (
                <>
                  <Loader2 size={20} className="spinner" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload size={20} />
                  <span>Choose File</span>
                </>
              )}
              <input 
                type="file" 
                onChange={handleFileUpload}
                accept=".pdf,.docx,.txt,.html"
                disabled={uploading}
                style={{ display: 'none' }}
              />
            </label>
            <p className="upload-hint">
              Supported: PDF, DOCX, TXT, HTML
            </p>
            {uploadStatus && (
              <div className={`upload-status ${uploadStatus.startsWith('Error') ? 'error' : 'success'}`}>
                {uploadStatus}
              </div>
            )}
          </div>

          <div className="sidebar-divider" />

          <div className="info-card">
            <div className="info-header">
              <Database size={18} />
              <span>Vector Store</span>
            </div>
            {collectionInfo && (
              <div className="info-details">
                <div className="info-row">
                  <span className="label">Chunks:</span>
                  <span className="value">{collectionInfo.points_count || 0}</span>
                </div>
                <div className="info-row">
                  <span className="label">Vectors:</span>
                  <span className="value">{collectionInfo.vectors_count || 0}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {!isOpen && (
        <button className="sidebar-toggle" onClick={onToggle}>
          <FileText size={20} />
        </button>
      )}
    </>
  );
}

export default Sidebar;
