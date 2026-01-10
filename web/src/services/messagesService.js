import api from './api';

const messagesService = {
    /**
     * List all chat rooms for the current society
     */
    listRooms: async () => {
        const response = await api.get('/messages/rooms');
        return response.data;
    },

    /**
     * Get messages in a specific room
     */
    getMessages: async (roomId, limit = 100) => {
        const response = await api.get(`/messages/rooms/${roomId}/messages?limit=${limit}`);
        return response.data;
    },

    /**
     * Send a message to a room
     */
    sendMessage: async (roomId, text) => {
        const response = await api.post(`/messages/rooms/${roomId}/messages`, { text });
        return response.data;
    },

    /**
     * Create a new chat room (Admin only)
     */
    createRoom: async (roomData) => {
        const response = await api.post('/messages/rooms', roomData);
        return response.data;
    }
};

export default messagesService;
