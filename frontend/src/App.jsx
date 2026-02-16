import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [collectionInfo, setCollectionInfo] = useState(null);

  const fetchCollectionInfo = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/collection/info`);
      const data = await response.json();
      setCollectionInfo(data);
    } catch (error) {
      console.error('Error fetching collection info:', error);
    }
  };

  useEffect(() => {
    fetchCollectionInfo();
  }, []);

  return (
    <div className="app">
      <Header />
      <div className="app-container">
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          collectionInfo={collectionInfo}
          onUploadSuccess={fetchCollectionInfo}
        />
        <ChatInterface sidebarOpen={sidebarOpen} />
      </div>
    </div>
  );
}

export default App;
