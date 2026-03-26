import React, { useState, useRef, useEffect } from 'react';
import {
  Send, Loader2, Trash2, Pencil, Check, Mic, MicOff,
  FileText, Gift, Building2, Radio, X, Bot, Plus, Share2, Settings
} from 'lucide-react';
import RecordRTC from 'recordrtc';
import Message from './Message';
import './ChatInterface.css';

const API_URL = import.meta.env.VITE_API_URL;

function VoiceOverlay({ isRecording, interimText, onStop }) {
  return (
    <div className="voice-overlay">
      <div className="voice-modal">
        <button className="voice-close-btn" onClick={onStop}>
          <X size={20} />
        </button>

        <div className="voice-icon-area">
          <div className={`voice-orb ${isRecording ? 'listening' : 'processing'}`}>
            {isRecording ? <Mic size={32} /> : <Loader2 size={32} className="spinner" />}
          </div>
        </div>

        {/* Animated waveform bars */}
        <div className={`voice-waveform ${isRecording ? 'active' : ''}`}>
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="wave-bar" style={{ animationDelay: `${i * 0.07}s` }} />
          ))}
        </div>

        <div className="voice-transcript">
          {interimText
            ? <span className="interim-text">{interimText}</span>
            : <span className="voice-hint-text">
                {isRecording ? 'Listening...' : 'Processing...'}
              </span>
          }
        </div>

        {isRecording && (
          <button className="voice-stop-btn" onClick={onStop}>
            <MicOff size={18} />
            Stop Recording
          </button>
        )}
      </div>
    </div>
  );
}

function ChatInterface({
  sidebarOpen, messages, onMessagesChange,
  conversationTitle, onRenameConversation,
  conversationId, activeSources
}) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showVoiceOverlay, setShowVoiceOverlay] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const messagesEndRef = useRef(null);
  const speechRecognitionRef = useRef(null);
  const recordingRef = useRef(false);

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

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new RecordRTC(stream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: RecordRTC.StereoAudioRecorder,
        desiredSampRate: 16000,
        numberOfAudioChannels: 1
      });

      recorder.startRecording();
      recorder.stream = stream;
      setMediaRecorder(recorder);
      setIsRecording(true);
      recordingRef.current = true;
      setShowVoiceOverlay(true);
      setInterimText('Listening...');

      // Start Web Speech API for live interim transcript
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-IN';
        recognition.onresult = (event) => {
          let transcript = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
          }
          if (transcript.trim()) {
            setInterimText(transcript.trim());
          }
        };
        recognition.onerror = () => {
          setInterimText('Live transcription unavailable. Recording still in progress...');
        };
        recognition.onend = () => {
          if (recordingRef.current) {
            try {
              recognition.start();
            } catch {
              setInterimText('Live transcription unavailable. Recording still in progress...');
            }
          }
        };

        try {
          recognition.start();
        } catch {
          setInterimText('Live transcription unavailable. Recording still in progress...');
        }

        speechRecognitionRef.current = recognition;
      } else {
        setInterimText('Live transcription not supported in this browser.');
      }
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Could not access microphone.');
    }
  };

  const stopRecording = () => {
    recordingRef.current = false;
    // Stop Web Speech API interim transcript
    if (speechRecognitionRef.current) {
      speechRecognitionRef.current.stop();
      speechRecognitionRef.current = null;
    }

    if (mediaRecorder && isRecording) {
      setIsRecording(false); // Switch overlay to "Processing..." state
      mediaRecorder.stopRecording(async () => {
        try {
          const audioBlob = mediaRecorder.getBlob();
          if (mediaRecorder.stream) {
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
          }
          mediaRecorder.destroy();
          setMediaRecorder(null);
          setShowVoiceOverlay(false); // Close overlay immediately
          setInterimText('');
          await sendAudio(audioBlob);
        } catch (err) {
          console.error('Error finishing recording:', err);
          setShowVoiceOverlay(false);
        }
      });
    }
  };

  const sendAudio = async (audioBlob) => {
    if (loading) return;
    setLoading(true);

    const tempMessage = {
      id: Date.now(),
      type: 'user',
      content: '[Voice message transcribing...]',
      isVoice: true,
      timestamp: new Date()
    };
    onMessagesChange([...messages, tempMessage]);

    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');
      if (conversationId) formData.append('conversation_id', String(conversationId));

      const response = await fetch(`${API_URL}/ask-voice`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      const userMessage = {
        ...tempMessage,
        content: data.transcription || 'Voice message',
        isVoice: true,
      };

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer || data.detail || 'No response received.',
        sources: data.sources || [],
        mode: data.mode || 'general',
        timestamp: new Date()
      };

      onMessagesChange([...messages, userMessage, botMessage]);

      if (data.audio_base64) {
        const audio = new Audio('data:audio/wav;base64,' + data.audio_base64);
        audio.play().catch(e => console.error('Failed to play audio response', e));
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error processing your voice command.',
        error: true,
        timestamp: new Date()
      };
      onMessagesChange([...messages, tempMessage, errorMessage]);
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
    if (titleDraft.trim()) onRenameConversation(titleDraft.trim());
    setEditingTitle(false);
  };

  return (
    <div className={`chat-interface ${sidebarOpen ? '' : 'full-width'}`}>
      {/* Animated voice recording overlay */}
      {showVoiceOverlay && (
        <VoiceOverlay
          isRecording={isRecording}
          interimText={interimText}
          onStop={stopRecording}
        />
      )}

      <div className="chat-header">
        <div className="chat-header-left">
          <div className="header-brand-pill">
            <Radio size={14} />
            <span>Red AI</span>
          </div>
        </div>
        <div className="chat-header-actions">
          <button className="header-icon-btn" title="Share"><Share2 size={18} /></button>
          <button className="header-icon-btn" title="Settings"><Settings size={18} /></button>
        </div>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="mascot-container">
              <div className="welcome-icon-glow">
                <Radio size={80} />
              </div>
            </div>
            <h2 className="welcome-headline">How can I help you today?</h2>
            <p className="welcome-subtext">I am your agent - ask anything about company policies or onboarding.</p>
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

      <div className="input-outer-container">

        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Chat here..."
            rows={1}
            disabled={loading || isRecording}
          />
          
          <div className="input-buttons">
            <button
              onClick={startRecording}
              disabled={loading || showVoiceOverlay}
              className="mic-btn-minimal"
              title="Record Voice Message"
            >
              <Mic size={18} />
            </button>
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading || isRecording}
              className="send-btn-minimal"
              title="Send Message"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
