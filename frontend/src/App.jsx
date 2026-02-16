import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [collectionInfo, setCollectionInfo] = useState(null);

  // Multi-conversation state
  const [conversations, setConversations] = useState([
    { id: String(Date.now()), title: 'New Chat', messages: [], createdAt: new Date(), pinned: false, sources: [] }
  ]);
  const [activeConversationId, setActiveConversationId] = useState(null);

  useEffect(() => {
    if (!activeConversationId && conversations.length > 0) {
      setActiveConversationId(conversations[0].id);
    }
  }, []);

  const fetchCollectionInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/collection/info`);
      const data = await response.json();
      setCollectionInfo(data);
    } catch (error) {
      console.error('Error fetching collection info:', error);
    }
  };

  // Fetch sources for the active conversation
  const fetchSources = useCallback(async (convId) => {
    if (!convId) return;
    try {
      const response = await fetch(`${API_URL}/sources/${convId}`);
      const data = await response.json();
      setConversations(prev => prev.map(c => {
        if (c.id !== convId) return c;
        // Preserve active state for existing sources, default new ones to active
        const existingMap = {};
        c.sources.forEach(s => { existingMap[s.name] = s.active; });
        const updatedSources = (data.sources || []).map(s => ({
          ...s,
          active: existingMap[s.name] !== undefined ? existingMap[s.name] : true
        }));
        return { ...c, sources: updatedSources };
      }));
    } catch (e) {}
  }, []);

  useEffect(() => {
    fetchCollectionInfo();
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      fetchSources(activeConversationId);
    }
  }, [activeConversationId, fetchSources]);

  const activeConversation = conversations.find(c => c.id === activeConversationId);

  const updateConversationMessages = (conversationId, messages) => {
    setConversations(prev => prev.map(c => {
      if (c.id !== conversationId) return c;
      // Auto-title from first user message if still default
      const firstUserMsg = messages.find(m => m.type === 'user');
      const title = (c.title === 'New Chat' && firstUserMsg)
        ? firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '')
        : c.title;
      return { ...c, messages, title };
    }));
  };

  const createNewConversation = async () => {
    const newConv = {
      id: String(Date.now()),
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      pinned: false,
      sources: []
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
    try {
      await fetch(`${API_URL}/clear-memory`, { method: 'POST' });
    } catch (e) {}
  };

  const deleteConversation = (id) => {
    setConversations(prev => {
      const updated = prev.filter(c => c.id !== id);
      if (updated.length === 0) {
        const fresh = { id: String(Date.now()), title: 'New Chat', messages: [], createdAt: new Date(), pinned: false, sources: [] };
        setActiveConversationId(fresh.id);
        return [fresh];
      }
      if (activeConversationId === id) {
        setActiveConversationId(updated[0].id);
      }
      return updated;
    });
  };

  const switchConversation = async (id) => {
    setActiveConversationId(id);
    try {
      await fetch(`${API_URL}/clear-memory`, { method: 'POST' });
    } catch (e) {}
  };

  const renameConversation = (id, newTitle) => {
    setConversations(prev => prev.map(c =>
      c.id === id ? { ...c, title: newTitle } : c
    ));
  };

  const togglePinConversation = (id) => {
    setConversations(prev => prev.map(c =>
      c.id === id ? { ...c, pinned: !c.pinned } : c
    ));
  };

  const toggleSourceActive = (sourceName) => {
    setConversations(prev => prev.map(c => {
      if (c.id !== activeConversationId) return c;
      return {
        ...c,
        sources: c.sources.map(s =>
          s.name === sourceName ? { ...s, active: !s.active } : s
        )
      };
    }));
  };

  const deleteSource = async (sourceName) => {
    try {
      await fetch(`${API_URL}/sources/${activeConversationId}/${encodeURIComponent(sourceName)}`, {
        method: 'DELETE'
      });
      fetchSources(activeConversationId);
      fetchCollectionInfo();
    } catch (e) {}
  };

  const handleUploadSuccess = () => {
    fetchCollectionInfo();
    fetchSources(activeConversationId);
  };

  // Sort: pinned first, then by creation date
  const sortedConversations = [...conversations].sort((a, b) => {
    if (a.pinned && !b.pinned) return -1;
    if (!a.pinned && b.pinned) return 1;
    return 0;
  });

  return (
    <div className="app">
      <Header />
      <div className="main-content">
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          collectionInfo={collectionInfo}
          onUploadSuccess={handleUploadSuccess}
          conversations={sortedConversations}
          activeConversationId={activeConversationId}
          onNewChat={createNewConversation}
          onSelectConversation={switchConversation}
          onDeleteConversation={deleteConversation}
          onRenameConversation={renameConversation}
          onTogglePinConversation={togglePinConversation}
          sources={activeConversation?.sources || []}
          onToggleSource={toggleSourceActive}
          onDeleteSource={deleteSource}
        />
        <ChatInterface
          sidebarOpen={sidebarOpen}
          messages={activeConversation?.messages || []}
          onMessagesChange={(msgs) => updateConversationMessages(activeConversationId, msgs)}
          conversationTitle={activeConversation?.title || 'New Chat'}
          onRenameConversation={(title) => renameConversation(activeConversationId, title)}
          conversationId={activeConversationId}
          activeSources={(activeConversation?.sources || []).filter(s => s.active).map(s => s.name)}
        />
      </div>
    </div>
  );
}

export default App;
