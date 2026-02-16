import React, { useState } from 'react';
import { Upload, FileText, X, ChevronLeft, Database, Loader2 } from 'lucide-react';
import './Sidebar.css';

function Sidebar({ isOpen, onToggle, collectionInfo, onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus('Uploading...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload/document', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setUploadStatus(`✓ ${data.filename} processed (${data.chunks} chunks)`);
        onUploadSuccess();
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        setUploadStatus(`✗ Error: ${data.detail}`);
      }
    } catch (error) {
      setUploadStatus(`✗ Error: ${error.message}`);
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

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
          {/* Collection Info */}
          <div className="info-card">
            <div className="info-header">
              <Database size={18} />
              <span>Vector Store</span>
            </div>
            {collectionInfo && (
              <div className="info-details">
                <div className="info-row">
                  <span className="label">Documents:</span>
                  <span className="value">{collectionInfo.points_count || 0}</span>
                </div>
                <div className="info-row">
                  <span className="label">Vectors:</span>
                  <span className="value">{collectionInfo.vectors_count || 0}</span>
                </div>
              </div>
            )}
          </div>

          {/* Upload Section */}
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
              <div className={`upload-status ${uploadStatus.startsWith('✓') ? 'success' : 'error'}`}>
                {uploadStatus}
              </div>
            )}
          </div>

          {/* Instructions */}
          <div className="instructions">
            <h3>How to Use</h3>
            <ol>
              <li>Upload company documents</li>
              <li>Ask questions in the chat</li>
              <li>Get answers from your docs or general knowledge</li>
            </ol>
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
