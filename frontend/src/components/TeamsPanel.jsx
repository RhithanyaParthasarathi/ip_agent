import React, { useState, useEffect, useRef } from 'react';
import { Phone, PhoneOff, Loader, Wifi, WifiOff, MessageSquare, Users, AlertCircle, Radio, User, Mic, MicOff, Volume2 } from 'lucide-react';
import './TeamsPanel.css';

const API_URL = import.meta.env.VITE_API_URL;

function TeamsPanel() {
    const [meetingUrl, setMeetingUrl] = useState('');
    const [botStatus, setBotStatus] = useState(null);
    const [activeCallId, setActiveCallId] = useState(null);
    const [callInfo, setCallInfo] = useState(null);
    const [isJoining, setIsJoining] = useState(false);
    const [isLeaving, setIsLeaving] = useState(false);
    const [joinMethod, setJoinMethod] = useState('selenium'); // Default to selenium since user prefers it
    const [seleniumSessionId, setSeleniumSessionId] = useState(null);
    const [isHeadless, setIsHeadless] = useState(false);
    const [error, setError] = useState(null);
    const [demoQuestion, setDemoQuestion] = useState('');
    const [demoLoading, setDemoLoading] = useState(false);
    const [demoTranscript, setDemoTranscript] = useState([]);
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const [isActionLoading, setIsActionLoading] = useState(null);
    const [manualMessage, setManualMessage] = useState('');
    const [isSendingManual, setIsSendingManual] = useState(false);
    const transcriptRef = useRef(null);

    // Poll bot status
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch(`${API_URL}/teams/status`);
                const data = await res.json();
                setBotStatus(data);
            } catch (e) {
                console.error('Failed to fetch Teams status:', e);
            }
        };
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    // Poll call info when active
    useEffect(() => {
        if (!activeCallId) return;
        const fetchCallInfo = async () => {
            try {
                const res = await fetch(`${API_URL}/teams/call/${activeCallId}`);
                if (res.ok) {
                    const data = await res.json();
                    setCallInfo(data);
                    if (data.status === 'disconnected') {
                        setActiveCallId(null);
                    }
                }
            } catch (e) {
                console.error('Failed to fetch call info:', e);
            }
        };
        fetchCallInfo();
        const interval = setInterval(fetchCallInfo, 3000);
        return () => clearInterval(interval);
    }, [activeCallId]);

    // Auto-scroll transcript
    useEffect(() => {
        if (transcriptRef.current) {
            transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
        }
    }, [demoTranscript, callInfo?.transcript]);

    const joinMeeting = async () => {
        if (!meetingUrl.trim()) return;
        setIsJoining(true);
        setError(null);
        try {
            const endpoint = joinMethod === 'selenium' 
                ? `/teams/selenium/join?headless=${isHeadless}` 
                : '/teams/join';
            
            const res = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meeting_url: meetingUrl }),
            });
            
            if (res.ok) {
                const data = await res.json();
                if (joinMethod === 'selenium') {
                    setSeleniumSessionId(data.session_id);
                    // For selenium, we don't have "activeCallId" in the same way yet
                    // but we can set a dummy one to trigger the "Active" UI
                    setActiveCallId(`sel_${data.session_id}`);
                } else {
                    setActiveCallId(data.call_connection_id);
                }
            } else {
                const err = await res.json();
                setError(err.detail || 'Failed to join meeting');
            }
        } catch (e) {
            setError('Network error: Could not reach backend');
        }
        setIsJoining(false);
    };

    const leaveMeeting = async () => {
        if (!activeCallId) return;
        setIsLeaving(true);
        try {
            if (joinMethod === 'selenium' && seleniumSessionId) {
                await fetch(`${API_URL}/teams/selenium/leave/${seleniumSessionId}`, { method: 'POST' });
                setSeleniumSessionId(null);
            } else {
                await fetch(`${API_URL}/teams/leave/${activeCallId}`, { method: 'POST' });
            }
            setActiveCallId(null);
            setCallInfo(null);
        } catch (e) {
            setError('Failed to leave meeting');
        }
        setIsLeaving(false);
    };

    const triggerAction = async (action) => {
        if (!seleniumSessionId) return;
        setIsActionLoading(action);
        try {
            const res = await fetch(`${API_URL}/teams/selenium/action/${seleniumSessionId}/${action}`, {
                method: 'POST'
            });
            if (!res.ok) throw new Error("Action failed");
        } catch (e) {
            console.error(`Failed to trigger action ${action}:`, e);
        }
        setIsActionLoading(null);
    };

    const handleManualChat = async () => {
        if (!seleniumSessionId || !manualMessage.trim() || isSendingManual) return;
        setIsSendingManual(true);
        try {
            const res = await fetch(`${API_URL}/teams/selenium/chat/${seleniumSessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: manualMessage }),
            });
            if (res.ok) {
                setManualMessage('');
            } else {
                throw new Error("Failed to send manual message");
            }
        } catch (e) {
            console.error("Send error:", e);
            setError("Failed to send manual message: " + e.message);
        }
        setIsSendingManual(false);
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                await sendVoiceQuery(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error("Error accessing microphone:", err);
            setError("Could not access microphone.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const sendVoiceQuery = async (audioBlob) => {
        setDemoLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', audioBlob, 'voice_query.wav');
            if (activeCallId) formData.append('conversation_id', activeCallId);

            const res = await fetch(`${API_URL}/ask-voice`, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) throw new Error("Failed to process voice");
            
            const data = await res.json();
            
            // Add transcription to UI
            setDemoTranscript(prev => [...prev, {
                speaker: 'You (Voice)',
                text: data.transcription,
                is_bot: false,
                timestamp: new Date().toISOString(),
            }]);

            // Add bot answer
            setDemoTranscript(prev => [...prev, {
                speaker: 'RAG Bot',
                text: data.answer,
                is_bot: true,
                mode: data.mode,
                timestamp: new Date().toISOString(),
            }]);

            // Play the audio response
            if (data.audio_base64) {
                playAudioResponse(data.audio_base64);
            }

        } catch (e) {
            setError("Voice Error: " + e.message);
        }
        setDemoLoading(false);
    };

    const playAudioResponse = (base64) => {
        try {
            const audio = new Audio(`data:audio/mpeg;base64,${base64}`);
            audio.play();
        } catch (e) {
            console.error("Error playing audio:", e);
        }
    };

    const sendDemoQuestion = async () => {
        if (!demoQuestion.trim() || demoLoading) return;
        const question = demoQuestion.trim();
        setDemoQuestion('');
        setDemoLoading(true);

        // Add user message to transcript
        setDemoTranscript(prev => [...prev, {
            speaker: 'You',
            text: question,
            is_bot: false,
            timestamp: new Date().toISOString(),
        }]);

        try {
            const res = await fetch(`${API_URL}/teams/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question }),
            });
            const data = await res.json();
            setDemoTranscript(prev => [...prev, {
                speaker: 'RAG Bot',
                text: data.answer,
                is_bot: true,
                mode: data.mode,
                timestamp: new Date().toISOString(),
            }]);
        } catch (e) {
            setDemoTranscript(prev => [...prev, {
                speaker: 'System',
                text: 'Failed to get response from RAG agent.',
                is_bot: true,
                timestamp: new Date().toISOString(),
            }]);
        }
        setDemoLoading(false);
    };

    const handleDemoKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendDemoQuestion();
        }
    };

    const isConnected = botStatus?.bot_status?.initialized;
    const transcript = activeCallId && callInfo?.transcript?.length > 0
        ? callInfo.transcript
        : demoTranscript;

    return (
        <div className="teams-panel">
            {/* Status Bar */}
            <div className="teams-status-bar">
                <div className="status-indicator-group">
                    <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
                    <span className="status-text">
                        {isConnected ? 'ACS Connected' : 'ACS Not Configured'}
                    </span>
                    <div className="status-divider" />
                    <div className={`status-dot ${seleniumSessionId ? 'connected' : 'idle'}`} />
                    <span className="status-text">
                        {seleniumSessionId ? 'Selenium Active' : 'Selenium Idle'}
                    </span>
                </div>
                {activeCallId && (
                    <div className="call-badge">
                        <Phone size={14} />
                        <span>In Call ({joinMethod})</span>
                    </div>
                )}
            </div>

            {/* Join Meeting Section */}
            <div className="teams-join-section">
                <h3 className="section-title">
                    <Users size={18} />
                    Teams Meeting
                </h3>

                {!activeCallId ? (
                    <div className="join-form-container">
                        <div className="join-method-picker">
                            <button 
                                className={`method-btn ${joinMethod === 'selenium' ? 'active' : ''}`}
                                onClick={() => setJoinMethod('selenium')}
                            >
                                Selenium
                            </button>
                            <button 
                                className={`method-btn ${joinMethod === 'acs' ? 'active' : ''}`}
                                onClick={() => setJoinMethod('acs')}
                            >
                                ACS (Standard)
                            </button>
                        </div>

                        {joinMethod === 'selenium' && (
                            <label className="headless-toggle">
                                <input 
                                    type="checkbox" 
                                    checked={isHeadless} 
                                    onChange={(e) => setIsHeadless(e.target.checked)} 
                                />
                                <span>Run in background (Headless)</span>
                            </label>
                        )}

                        <div className="join-form">
                            <input
                                type="text"
                                className="meeting-input"
                                placeholder="Paste Teams meeting URL..."
                                value={meetingUrl}
                                onChange={(e) => setMeetingUrl(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && joinMeeting()}
                                disabled={isJoining}
                            />
                            <button
                                className="join-btn"
                                onClick={joinMeeting}
                                disabled={!meetingUrl.trim() || isJoining || (joinMethod === 'acs' && !isConnected)}
                            >
                                {isJoining ? (
                                    <><Loader size={16} className="spinner" /> Joining...</>
                                ) : (
                                    <><Phone size={16} /> Join</>
                                )}
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="active-call-info">
                        <div className="call-status-row">
                            <div className="call-status-badge">
                                <div className="pulse-dot" />
                                <span>{callInfo?.status || 'connecting'}</span>
                            </div>
                            {callInfo?.participant_count > 0 && (
                                <span className="participant-count">
                                    <Users size={14} /> {callInfo.participant_count} participants
                                </span>
                            )}
                        </div>

                        {joinMethod === 'selenium' && seleniumSessionId && (
                            <div className="manual-controls">
                                <span className="controls-label">Bot Controls:</span>
                                <div className="control-buttons">
                                    <button 
                                        className="control-btn mute" 
                                        onClick={() => triggerAction('mute')}
                                        disabled={isActionLoading === 'mute'}
                                        title="Force Mute"
                                    >
                                        {isActionLoading === 'mute' ? <Loader size={12} className="spinner" /> : <MicOff size={12} />}
                                        Mute
                                    </button>
                                    <button 
                                        className="control-btn unmute" 
                                        onClick={() => triggerAction('unmute')}
                                        disabled={isActionLoading === 'unmute'}
                                        title="Force Unmute"
                                    >
                                        {isActionLoading === 'unmute' ? <Loader size={12} className="spinner" /> : <Mic size={12} />}
                                        Unmute
                                    </button>
                                    <button 
                                        className="control-btn" 
                                        onClick={() => triggerAction('chat')}
                                        disabled={isActionLoading === 'chat'}
                                    >
                                        {isActionLoading === 'chat' ? <Loader size={12} className="spinner" /> : <MessageSquare size={12} />}
                                        Chat
                                    </button>
                                    <button 
                                        className="control-btn" 
                                        onClick={() => triggerAction('more')}
                                        disabled={isActionLoading === 'more'}
                                    >
                                        {isActionLoading === 'more' ? <Loader size={12} className="spinner" /> : <Radio size={12} />}
                                        More
                                    </button>
                                    <button 
                                        className="control-btn" 
                                        onClick={() => triggerAction('captions')}
                                        disabled={isActionLoading === 'captions'}
                                    >
                                        {isActionLoading === 'captions' ? <Loader size={12} className="spinner" /> : <Volume2 size={12} />}
                                        Captions
                                    </button>
                                </div>
                                
                                <div className="manual-chat-input">
                                    <input 
                                        type="text" 
                                        className="control-input"
                                        placeholder="Send manual message to Teams..." 
                                        value={manualMessage}
                                        onChange={(e) => setManualMessage(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleManualChat()}
                                        disabled={isSendingManual}
                                    />
                                    <button 
                                        className="control-send-btn"
                                        onClick={handleManualChat}
                                        disabled={!manualMessage.trim() || isSendingManual}
                                    >
                                        {isSendingManual ? <Loader size={12} className="spinner" /> : <MessageSquare size={12} />}
                                    </button>
                                </div>
                            </div>
                        )}

                        <button
                            className="leave-btn"
                            onClick={leaveMeeting}
                            disabled={isLeaving}
                        >
                            {isLeaving ? (
                                <><Loader size={16} className="spinner" /> Leaving...</>
                            ) : (
                                <><PhoneOff size={16} /> Leave Meeting</>
                            )}
                        </button>
                    </div>
                )}

                {error && (
                    <div className="error-banner">
                        <AlertCircle size={16} />
                        <span>{error}</span>
                        <button onClick={() => setError(null)}>×</button>
                    </div>
                )}

                {!isConnected && (
                    <div className="info-banner">
                        <AlertCircle size={14} />
                        <span>ACS not configured. Set <code>ACS_CONNECTION_STRING</code> in <code>.env</code></span>
                    </div>
                )}
            </div>

            {/* Transcript / Demo Section */}
            <div className="teams-transcript-section">
                <h3 className="section-title">
                    <MessageSquare size={18} />
                    {activeCallId ? 'Live Transcript' : 'Demo Q&A (Teams Simulation)'}
                </h3>

                <div className="transcript-feed" ref={transcriptRef}>
                    {transcript.length === 0 ? (
                        <div className="transcript-empty">
                            <Radio size={32} className="empty-icon" />
                            <p>{activeCallId
                                ? 'Waiting for speech...'
                                : 'Ask a question to simulate Teams voice Q&A'
                            }</p>
                        </div>
                    ) : (
                        transcript.map((entry, idx) => (
                            <div key={idx} className={`transcript-entry ${entry.is_bot ? 'bot' : 'user'}`}>
                                <div className="transcript-avatar">
                                    {entry.is_bot ? <Radio size={16} /> : <User size={16} />}
                                </div>
                                <div className="transcript-bubble">
                                    <span className="transcript-speaker">{entry.speaker}</span>
                                    <p className="transcript-text">{entry.text}</p>
                                    {entry.mode && (
                                        <span className={`mode-badge ${entry.mode}`}>
                                            {entry.mode === 'rag' ? '📚 From Documents' : '🌐 General Knowledge'}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    {demoLoading && (
                        <div className="transcript-entry bot">
                            <div className="transcript-avatar"><Radio size={16} /></div>
                            <div className="transcript-bubble loading">
                                <Loader size={14} className="spinner" /> Thinking...
                            </div>
                        </div>
                    )}
                </div>

                {/* Demo input (always available for testing) */}
                <div className="demo-input-container">
                    <button
                        className={`mic-btn ${isRecording ? 'recording' : ''}`}
                        onClick={isRecording ? stopRecording : startRecording}
                        title={isRecording ? "Stop Recording" : "Ask via Voice"}
                    >
                        {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                    </button>
                    <textarea
                        className="demo-input"
                        placeholder={activeCallId
                            ? 'Type or use mic to ask something...'
                            : 'Ask a question (simulates Teams voice Q&A)...'
                        }
                        value={demoQuestion}
                        onChange={(e) => setDemoQuestion(e.target.value)}
                        onKeyDown={handleDemoKeyDown}
                        rows={1}
                        disabled={demoLoading || isRecording}
                    />
                    <button
                        className="demo-send-btn"
                        onClick={sendDemoQuestion}
                        disabled={!demoQuestion.trim() || demoLoading || isRecording}
                    >
                        {demoLoading ? <Loader size={18} className="spinner" /> : <MessageSquare size={18} />}
                    </button>
                </div>
            </div>

            {/* Events Log */}
            {activeCallId && callInfo?.recent_events?.length > 0 && (
                <div className="teams-events-section">
                    <h3 className="section-title">Events</h3>
                    <div className="events-log">
                        {callInfo.recent_events.map((evt, idx) => (
                            <div key={idx} className="event-entry">
                                <span className="event-time">
                                    {new Date(evt.timestamp).toLocaleTimeString()}
                                </span>
                                <span className="event-msg">{evt.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default TeamsPanel;
