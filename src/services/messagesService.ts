/**
 * Messages Service
 * Handles chat rooms and messages
 */
import api from './api';

export interface ChatRoom {
  id: string;
  name: string;
  type: 'general' | 'maintenance' | 'announcements';
  description?: string;
  created_at: string;
  last_message_at?: string;
  last_message?: string; // Last message content (if available)
  unread_count?: number; // Unread message count (if available)
}

export interface Message {
  id: string;
  room_id: string;
  sender_id: string;
  sender_name: string;
  content: string; // Backend uses 'content'
  text?: string; // Alias for content for compatibility
  created_at: string;
}

export interface ChatRoomCreate {
  name: string;
  type: 'general' | 'maintenance' | 'announcements';
  description?: string;
}

export interface MessageCreate {
  text: string; // Frontend uses 'text'
  content?: string; // Backend uses 'content'
}

export const messagesService = {
  /**
   * Get all chat rooms
   */
  async getChatRooms(): Promise<ChatRoom[]> {
    const response = await api.get<ChatRoom[]>('/messages/rooms');
    return response.data;
  },

  /**
   * Create a new chat room (admin only)
   */
  async createChatRoom(data: ChatRoomCreate): Promise<ChatRoom> {
    const response = await api.post<ChatRoom>('/messages/rooms', data);
    return response.data;
  },

  /**
   * Get messages for a chat room
   */
  async getMessages(roomId: string): Promise<Message[]> {
    const response = await api.get<Message[]>(`/messages/rooms/${roomId}/messages`);
    return response.data;
  },

  /**
   * Send a message to a chat room
   */
  async sendMessage(roomId: string, data: MessageCreate): Promise<Message> {
    // Backend accepts either 'text' or 'content' field
    const response = await api.post<Message>(`/messages/rooms/${roomId}/messages`, {
      text: data.text,
      content: data.content || data.text,
    });
    return response.data;
  },
};

