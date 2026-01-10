import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import messagesService from '../services/messagesService';
import { authService } from '../services/authService';

const MessagesScreen = () => {
    const navigate = useNavigate();
    const [rooms, setRooms] = useState([]);
    const [selectedRoom, setSelectedRoom] = useState(null);
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [user, setUser] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newRoomData, setNewRoomData] = useState({ name: '', type: 'general', description: '' });
    const messagesEndRef = useRef(null);

    useEffect(() => {
        const init = async () => {
            const currentUser = await authService.getCurrentUser();
            setUser(currentUser);
            loadRooms();
        };
        init();
    }, []);

    useEffect(() => {
        if (selectedRoom) {
            loadMessages(selectedRoom.id);
        }
    }, [selectedRoom]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const loadRooms = async (autoSelectId = null) => {
        setLoading(true);
        try {
            const roomsList = await messagesService.listRooms();
            setRooms(roomsList);
            if (autoSelectId) {
                const newRoom = roomsList.find(r => r.id === autoSelectId);
                if (newRoom) setSelectedRoom(newRoom);
            } else if (!selectedRoom && roomsList.length > 0) {
                setSelectedRoom(roomsList[0]);
            }
        } catch (error) {
            console.error('Error loading rooms:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadMessages = async (roomId) => {
        setLoadingMessages(true);
        try {
            const messagesList = await messagesService.getMessages(roomId);
            setMessages(messagesList);
        } catch (error) {
            console.error('Error loading messages:', error);
        } finally {
            setLoadingMessages(false);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim() || !selectedRoom) return;

        try {
            const sent = await messagesService.sendMessage(selectedRoom.id, newMessage);
            setMessages([...messages, sent]);
            setNewMessage('');
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        }
    };

    const handleCreateRoom = async (e) => {
        e.preventDefault();
        try {
            const created = await messagesService.createRoom(newRoomData);
            setShowCreateModal(false);
            setNewRoomData({ name: '', type: 'general', description: '' });
            loadRooms(created.id);
        } catch (error) {
            console.error('Error creating room:', error);
            alert('Failed to create room. Admin access required.');
        }
    };

    if (loading && rooms.length === 0) {
        return (
            <div className="loading-container">
                <div className="loading-text">Loading chat rooms...</div>
            </div>
        );
    }

    return (
        <div className="dashboard-container" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <div className="dashboard-header" style={{ flexShrink: 0 }}>
                <div className="dashboard-header-left">
                    <h1 className="dashboard-header-title">💬 Messages</h1>
                </div>
                <div className="dashboard-header-right">
                    <button onClick={() => navigate('/dashboard')} className="dashboard-logout-button">
                        ← Back to Dashboard
                    </button>
                </div>
            </div>

            <div style={{ display: 'flex', flex: 1, overflow: 'hidden', padding: '20px', gap: '20px' }}>
                {/* Sidebar - Rooms List */}
                <div style={{
                    width: '300px',
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden'
                }}>
                    <div style={{
                        padding: '20px',
                        borderBottom: '1px solid #eee',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                    }}>
                        <span style={{ fontWeight: 'bold', color: '#1D1D1F' }}>Chat Rooms</span>
                        {user?.role === 'admin' && (
                            <button
                                onClick={() => setShowCreateModal(true)}
                                style={{
                                    padding: '4px 8px',
                                    borderRadius: '6px',
                                    backgroundColor: '#007AFF',
                                    color: 'white',
                                    border: 'none',
                                    fontSize: '12px',
                                    cursor: 'pointer',
                                    fontWeight: 'bold'
                                }}
                            >
                                + Add Room
                            </button>
                        )}
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        {rooms.map(room => (
                            <div
                                key={room.id}
                                onClick={() => setSelectedRoom(room)}
                                style={{
                                    padding: '15px 20px',
                                    cursor: 'pointer',
                                    borderLeft: selectedRoom?.id === room.id ? '4px solid #007AFF' : '4px solid transparent',
                                    backgroundColor: selectedRoom?.id === room.id ? '#F2F2F7' : 'transparent',
                                    transition: '0.2s'
                                }}
                            >
                                <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>{room.name}</div>
                                <div style={{ fontSize: '12px', color: '#8E8E93', textTransform: 'uppercase' }}>{room.type}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main Chat Area */}
                <div style={{
                    flex: 1,
                    backgroundColor: 'white',
                    borderRadius: '12px',
                    boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden'
                }}>
                    {selectedRoom ? (
                        <>
                            <div style={{ padding: '15px 20px', borderBottom: '1px solid #eee', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <div>
                                    <div style={{ fontWeight: 'bold', color: '#1D1D1F' }}>{selectedRoom.name}</div>
                                    <div style={{ fontSize: '12px', color: '#8E8E93' }}>{selectedRoom.description || 'Public channel for society communication'}</div>
                                </div>
                            </div>

                            <div style={{ flex: 1, overflowY: 'auto', padding: '20px', backgroundColor: '#F9F9FB' }}>
                                {loadingMessages ? (
                                    <div style={{ textAlign: 'center', color: '#8E8E93', marginTop: '20px' }}>Loading messages...</div>
                                ) : messages.length === 0 ? (
                                    <div style={{ textAlign: 'center', color: '#8E8E93', marginTop: '40px' }}>No messages yet. Start the conversation!</div>
                                ) : (
                                    messages.map(msg => (
                                        <div
                                            key={msg.id}
                                            style={{
                                                display: 'flex',
                                                flexDirection: 'column',
                                                alignItems: msg.sender_id === user?.id ? 'flex-end' : 'flex-start',
                                                marginBottom: '15px'
                                            }}
                                        >
                                            <div style={{ fontSize: '11px', color: '#8E8E93', marginBottom: '4px', marginLeft: '4px', marginRight: '4px' }}>
                                                {msg.sender_name} • {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </div>
                                            <div style={{
                                                maxWidth: '70%',
                                                padding: '10px 15px',
                                                borderRadius: '16px',
                                                fontSize: '14px',
                                                backgroundColor: msg.sender_id === user?.id ? '#007AFF' : '#E5E5EA',
                                                color: msg.sender_id === user?.id ? 'white' : '#1D1D1F',
                                                borderBottomRightRadius: msg.sender_id === user?.id ? '4px' : '16px',
                                                borderBottomLeftRadius: msg.sender_id === user?.id ? '16px' : '4px'
                                            }}>
                                                {msg.content}
                                            </div>
                                        </div>
                                    ))
                                )}
                                <div ref={messagesEndRef} />
                            </div>

                            <div style={{ padding: '20px', borderTop: '1px solid #eee' }}>
                                <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '10px' }}>
                                    <input
                                        type="text"
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        placeholder={`Message ${selectedRoom.name}...`}
                                        style={{
                                            flex: 1,
                                            padding: '12px 18px',
                                            borderRadius: '24px',
                                            border: '1px solid #E5E5EA',
                                            fontSize: '14px',
                                            outline: 'none'
                                        }}
                                    />
                                    <button
                                        type="submit"
                                        style={{
                                            padding: '10px 20px',
                                            borderRadius: '24px',
                                            border: 'none',
                                            backgroundColor: '#007AFF',
                                            color: 'white',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        Send
                                    </button>
                                </form>
                            </div>
                        </>
                    ) : (
                        <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', color: '#8E8E93' }}>
                            Select a chat room to start messaging
                        </div>
                    )}
                </div>
            </div>

            {/* Create Room Modal */}
            {showCreateModal && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 2000
                }}>
                    <div style={{
                        backgroundColor: 'white',
                        padding: '30px',
                        borderRadius: '16px',
                        width: '400px',
                        boxShadow: '0 4px 24px rgba(0,0,0,0.2)'
                    }}>
                        <h2 style={{ marginBottom: '20px', color: '#1D1D1F' }}>Create New Room</h2>
                        <form onSubmit={handleCreateRoom}>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', fontSize: '14px', marginBottom: '5px', color: '#8E8E93' }}>Room Name</label>
                                <input
                                    type="text"
                                    required
                                    value={newRoomData.name}
                                    onChange={(e) => setNewRoomData({ ...newRoomData, name: e.target.value })}
                                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #E5E5EA', outline: 'none' }}
                                />
                            </div>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', fontSize: '14px', marginBottom: '5px', color: '#8E8E93' }}>Type</label>
                                <select
                                    value={newRoomData.type}
                                    onChange={(e) => setNewRoomData({ ...newRoomData, type: e.target.value })}
                                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #E5E5EA', outline: 'none' }}
                                >
                                    <option value="general">General</option>
                                    <option value="announcements">Announcements</option>
                                    <option value="maintenance">Maintenance</option>
                                </select>
                            </div>
                            <div style={{ marginBottom: '20px' }}>
                                <label style={{ display: 'block', fontSize: '14px', marginBottom: '5px', color: '#8E8E93' }}>Description</label>
                                <textarea
                                    value={newRoomData.description}
                                    onChange={(e) => setNewRoomData({ ...newRoomData, description: e.target.value })}
                                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #E5E5EA', outline: 'none', height: '80px', resize: 'none' }}
                                />
                            </div>
                            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: '#F2F2F7', cursor: 'pointer' }}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: '#007AFF', color: 'white', fontWeight: 'bold', cursor: 'pointer' }}
                                >
                                    Create Room
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MessagesScreen;
