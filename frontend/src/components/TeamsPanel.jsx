import React, { useState, useEffect, useRef } from 'react';
import { Phone, PhoneOff, Loader, Wifi, WifiOff, MessageSquare, Users, AlertCircle, Bot, User } from 'lucide-react';
import './TeamsPanel.css';

const API_URL = import.meta.env.VITE_API_URL;

function TeamsPanel() {
    const [meetingUrl, setMeetingUrl] = useState('');
    const [botStatus, setBotStatus] = useState(null);
    const [activeCallId, setActiveCallId] = useState(null);
    const [callInfo, setCallInfo] = useState(null);
    const [isJoining, setIsJoining] = useState(false);
    const [isLeaving, setIsLeaving] = useState(false);
    const [error, setError] = useState(null);
    const [demoQuestion, setDemoQuestion] = useState('');
    const [demoLoading, setDemoLoading] = useState(false);
    const [demoTranscript, setDemoTranscript] = useState([]);
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
            const res = await fetch(`${API_URL}/teams/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meeting_url: meetingUrl }),
            });
            if (res.ok) {
                const data = await res.json();
                setActiveCallId(data.call_connection_id);
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
            await fetch(`${API_URL}/teams/leave/${activeCallId}`, { method: 'POST' });
            setActiveCallId(null);
            setCallInfo(null);
        } catch (e) {
            setError('Failed to leave meeting');
        }
        setIsLeaving(false);
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
                </div>
                {activeCallId && (
                    <div className="call-badge">
                        <Phone size={14} />
                        <span>In Call</span>
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
                    <div className="join-form">
                        <input
                            type="text"
                            className="meeting-input"
                            placeholder="Paste Teams meeting URL..."
                            value={meetingUrl}
                            onChange={(e) => setMeetingUrl(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && joinMeeting()}
                            disabled={isJoining || !isConnected}
                        />
                        <button
                            className="join-btn"
                            onClick={joinMeeting}
                            disabled={!meetingUrl.trim() || isJoining || !isConnected}
                        >
                            {isJoining ? (
                                <><Loader size={16} className="spinner" /> Joining...</>
                            ) : (
                                <><Phone size={16} /> Join</>
                            )}
                        </button>
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
                            <Bot size={32} className="empty-icon" />
                            <p>{activeCallId
                                ? 'Waiting for speech...'
                                : 'Ask a question to simulate Teams voice Q&A'
                            }</p>
                        </div>
                    ) : (
                        transcript.map((entry, idx) => (
                            <div key={idx} className={`transcript-entry ${entry.is_bot ? 'bot' : 'user'}`}>
                                <div className="transcript-avatar">
                                    {entry.is_bot ? <Bot size={16} /> : <User size={16} />}
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
                            <div className="transcript-avatar"><Bot size={16} /></div>
                            <div className="transcript-bubble loading">
                                <Loader size={14} className="spinner" /> Thinking...
                            </div>
                        </div>
                    )}
                </div>

                {/* Demo input (always available for testing) */}
                <div className="demo-input-container">
                    <textarea
                        className="demo-input"
                        placeholder={activeCallId
                            ? 'Type to simulate a voice question...'
                            : 'Ask a question (simulates Teams voice Q&A)...'
                        }
                        value={demoQuestion}
                        onChange={(e) => setDemoQuestion(e.target.value)}
                        onKeyDown={handleDemoKeyDown}
                        rows={1}
                        disabled={demoLoading}
                    />
                    <button
                        className="demo-send-btn"
                        onClick={sendDemoQuestion}
                        disabled={!demoQuestion.trim() || demoLoading}
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
