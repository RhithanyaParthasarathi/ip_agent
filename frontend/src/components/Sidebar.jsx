import React, { useState } from 'react';
import { Upload, FileText, ChevronLeft, Database, Loader2, Plus, MessageSquare, Trash2, Pin, PinOff, Pencil, Check, X, FileX2, Search, Radio, Phone, Library, Bot } from 'lucide-react';
import './Sidebar.css';

const API_URL = import.meta.env.VITE_API_URL || '/api';

function Sidebar({ 
  isOpen, onToggle, collectionInfo, onUploadSuccess,
  conversations, activeConversationId, onNewChat, onSelectConversation, onDeleteConversation,
  onRenameConversation, onTogglePinConversation,
  sources, onToggleSource, onDeleteSource,
  activeTab, setActiveTab
}) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const [showLibrary, setShowLibrary] = useState(true);

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


  const renderConvItem = (conv) => (
    <div
      key={conv.id}
      className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
      onClick={() => onSelectConversation(conv.id)}
    >
      <MessageSquare size={14} />
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
        <span className="conversation-title">{conv.title || 'Untitled Chat'}</span>
      )}
      <div className="conv-actions">
        {renamingId === conv.id ? (
          <>
            <button className="conv-action-btn confirm" onClick={confirmRename}><Check size={12} /></button>
            <button className="conv-action-btn cancel" onClick={cancelRename}><X size={12} /></button>
          </>
        ) : (
          <>
            <button className="conv-action-btn" onClick={(e) => startRename(conv, e)} title="Rename">
              <Pencil size={12} />
            </button>
            <button className="conv-action-btn" onClick={(e) => { e.stopPropagation(); onTogglePinConversation(conv.id); }} title={conv.pinned ? 'Unpin' : 'Pin'}>
              {conv.pinned ? <PinOff size={12} /> : <Pin size={12} />}
            </button>
            <button className="conv-action-btn delete-btn-side" onClick={(e) => { e.stopPropagation(); onDeleteConversation(conv.id); }}>
              <Trash2 size={12} />
            </button>
          </>
        )}
      </div>
    </div>
  );

  const filteredConversations = conversations.filter(c => 
    c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  const pinnedConvs = filteredConversations.filter(c => c.pinned);
  const unpinnedConvs = filteredConversations.filter(c => !c.pinned);

  return (
    <>
      <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-brand">
          <div className="logo-box">
            <Radio size={20} color="#fff" />
          </div>
          <span className="brand-name">Red AI</span>
          <button className="toggle-sidebar-btn" onClick={onToggle}>
            <ChevronLeft size={18} />
          </button>
        </div>

        <div className="sidebar-search">
          <div className="search-box">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search chats..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="sidebar-content">
          <div className="nav-group">
            <button 
              className={`nav-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => { setActiveTab('chat'); onNewChat(); setShowLibrary(false); }}
            >
              <div className="nav-icon-box purple"><Plus size={16} /></div>
              <span>New Chat</span>
            </button>
            <button 
              className={`nav-btn ${showLibrary ? 'active-lib' : ''}`}
              onClick={() => setShowLibrary(!showLibrary)}
            >
              <div className="nav-icon-box blue"><Library size={16} /></div>
              <span>Library</span>
            </button>
            <button 
              className={`nav-btn ${activeTab === 'teams' ? 'active' : ''}`}
              onClick={() => { setActiveTab('teams'); setShowLibrary(false); }}
            >
              <div className="nav-icon-box green"><Phone size={16} /></div>
              <span>Teams Meeting</span>
            </button>
          </div>

          <div className="section-divider" />

          {showLibrary && (
            <div className="conversations-section">
              <div className="section-header">
                <h3>Chat History</h3>
              </div>
              <div className="conversations-list">
                {pinnedConvs.map(renderConvItem)}
                {unpinnedConvs.map(renderConvItem)}
                {filteredConversations.length === 0 && (
                  <p className="no-convs">No chats found</p>
                )}
              </div>
            </div>
          )}

          {sources && sources.length > 0 && (
            <div className="sources-section-sidebar">
              <div className="section-header">
                <h3>Sources</h3>
              </div>
              <div className="sources-list-sidebar">
                {sources.map((source, idx) => (
                  <div key={idx} className="source-item-sidebar">
                    <FileText size={14} />
                    <span className="source-name-sidebar">{source.name || source}</span>
                    <button className="source-del-btn" onClick={() => onDeleteSource(source.name || source)}>
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="sidebar-footer">
            <div className="upload-mini-section">
              <label className="upload-link">
                <Upload size={14} />
                <span>{uploading ? 'Uploading...' : 'Upload Document'}</span>
                <input type="file" onChange={handleFileUpload} accept=".pdf,.docx,.txt" style={{ display: 'none' }} />
              </label>
            </div>
            
            <div className="vector-store-mini">
              <div className="mini-row">
                <Database size={13} />
                <span>{collectionInfo?.points_count || 0} {collectionInfo?.points_count === 1 ? 'Chunk' : 'Chunks'} in Vector Store</span>
              </div>
              <button 
                className="clear-vstore-btn"
                onClick={async () => {
                  if (window.confirm('Wipe the knowledge base? This clears ALL uploaded documents.')) {
                    const baseCandidates = [
                      API_URL,
                      '/api',
                      'http://localhost:8000'
                    ].filter((value, index, array) => Boolean(value) && array.indexOf(value) === index);

                    const requests = [];
                    for (const base of baseCandidates) {
                      requests.push({ url: `${base}/collection/clear`, method: 'POST' });
                      requests.push({ url: `${base}/collection`, method: 'DELETE' });
                    }

                    let lastResponseText = '';
                    let lastStatus = 0;

                    try {
                      for (const request of requests) {
                        const res = await fetch(request.url, { method: request.method });
                        if (res.ok) {
                          window.location.reload();
                          return;
                        }
                        lastStatus = res.status;
                        lastResponseText = await res.text();
                      }

                      alert(`Backend Error (${lastStatus}): ${lastResponseText || 'Not Found'}`);
                    } catch (e) { 
                      console.error('Failed to clear store', e);
                      alert(`Network Error: ${e.message}`);
                    }
                  }
                }}
              >
                Clear Knowledge
              </button>
            </div>
          </div>
        </div>
      </div>

      {!isOpen && (
        <button className="sidebar-floating-toggle" onClick={onToggle}>
          <Radio size={22} className="sidebar-glow-icon" />
        </button>
      )}
    </>
  );
}

export default Sidebar;
