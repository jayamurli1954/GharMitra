import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {messagesService, ChatRoom, ChatRoomCreate} from '../../services/messagesService';
import {authService} from '../../services/authService';

const MessageListScreen = ({navigation}: any) => {
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newRoom, setNewRoom] = useState<ChatRoomCreate>({
    name: '',
    type: 'general',
    description: '',
  });

  useEffect(() => {
    loadChatRooms();
    checkAdminStatus();
  }, []);

  const checkAdminStatus = async () => {
    try {
      const user = await authService.getStoredUser();
      setIsAdmin(user?.role === 'admin' || user?.role === 'super_admin');
    } catch (error) {
      console.error('Error checking admin status:', error);
      setIsAdmin(false);
    }
  };

  const loadChatRooms = async () => {
    setLoading(true);
    setError(null);
    try {
      const rooms = await messagesService.getChatRooms();
      setChatRooms(rooms);
    } catch (error: any) {
      console.error('Error loading chat rooms:', error);
      setError('Failed to load chat rooms');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async () => {
    if (!newRoom.name.trim()) {
      Alert.alert('Error', 'Please enter a room name');
      return;
    }

    setCreating(true);
    try {
      const createdRoom = await messagesService.createChatRoom(newRoom);
      Alert.alert('Success', `Chat room "${createdRoom.name}" created successfully!`);
      setShowCreateModal(false);
      setNewRoom({name: '', type: 'general', description: ''});
      loadChatRooms();
    } catch (error: any) {
      console.error('Error creating chat room:', error);
      Alert.alert(
        'Error',
        error.message || 'Failed to create chat room. Please try again.',
      );
    } finally {
      setCreating(false);
    }
  };

  const formatTime = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return date.toLocaleDateString('en-IN', {weekday: 'short'});
    } else {
      return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
      });
    }
  };

  const getIconForRoomType = (type: string) => {
    switch (type) {
      case 'general':
        return 'chatbubbles';
      case 'maintenance':
        return 'construct';
      case 'announcements':
        return 'megaphone';
      default:
        return 'chatbubbles';
    }
  };

  const getRoomTypeColor = (type: string) => {
    switch (type) {
      case 'general':
        return '#007AFF';
      case 'maintenance':
        return '#FF9500';
      case 'announcements':
        return '#34C759';
      default:
        return '#007AFF';
    }
  };

  const renderChatRoom = ({item}: {item: ChatRoom}) => (
    <TouchableOpacity
      style={styles.chatRoomCard}
      onPress={() =>
        navigation.navigate('ChatRoom', {roomId: item.id, roomName: item.name})
      }
      activeOpacity={0.7}>
      <View
        style={[
          styles.chatRoomIcon,
          {backgroundColor: getRoomTypeColor(item.type) + '20'},
        ]}>
        <Icon
          name={getIconForRoomType(item.type)}
          size={28}
          color={getRoomTypeColor(item.type)}
        />
      </View>
      <View style={styles.chatRoomDetails}>
        <View style={styles.chatRoomHeader}>
          <Text style={styles.chatRoomName}>{item.name}</Text>
          {item.last_message_at && (
            <Text style={styles.chatRoomTime}>
              {formatTime(item.last_message_at)}
            </Text>
          )}
        </View>
        <View style={styles.chatRoomFooter}>
          <Text style={styles.lastMessage} numberOfLines={1}>
            {item.last_message || 'No messages yet'}
          </Text>
          {item.unread_count && item.unread_count > 0 && (
            <View style={styles.unreadBadge}>
              <Text style={styles.unreadText}>{item.unread_count}</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading && chatRooms.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading chat rooms...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Error Message */}
      {error && (
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={24} color="#FF3B30" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={loadChatRooms}
            activeOpacity={0.7}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Chat Rooms List */}
      <FlatList
        data={chatRooms}
        renderItem={renderChatRoom}
        keyExtractor={(item, index) => item.id?.toString() || `chatroom-${index}`}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={loadChatRooms} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Icon name="chatbubbles-outline" size={64} color="#C7C7CC" />
            <Text style={styles.emptyStateText}>No chat rooms available</Text>
            <Text style={styles.emptyStateSubtext}>
              {isAdmin
                ? 'Tap the + button to create your first chat room'
                : 'Chat rooms will appear here once they are created by an admin'}
            </Text>
          </View>
        }
      />

      {/* Create Chat Room Button (Admin Only) */}
      {isAdmin && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => setShowCreateModal(true)}
          activeOpacity={0.8}>
          <Icon name="add" size={28} color="#FFF" />
        </TouchableOpacity>
      )}

      {/* Create Chat Room Modal */}
      <Modal
        visible={showCreateModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowCreateModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create Chat Room</Text>
              <TouchableOpacity
                onPress={() => setShowCreateModal(false)}
                style={styles.closeButton}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <View style={styles.modalBody}>
              <Text style={styles.label}>Room Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., General Discussion"
                value={newRoom.name}
                onChangeText={text => setNewRoom({...newRoom, name: text})}
                autoCapitalize="words"
              />

              <Text style={styles.label}>Room Type *</Text>
              <View style={styles.typeContainer}>
                {(['general', 'maintenance', 'announcements'] as const).map(type => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.typeButton,
                      newRoom.type === type && styles.typeButtonActive,
                    ]}
                    onPress={() => setNewRoom({...newRoom, type})}>
                    <Icon
                      name={getIconForRoomType(type)}
                      size={20}
                      color={newRoom.type === type ? '#FFF' : getRoomTypeColor(type)}
                    />
                    <Text
                      style={[
                        styles.typeButtonText,
                        newRoom.type === type && styles.typeButtonTextActive,
                      ]}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.label}>Description (Optional)</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="What is this room for?"
                value={newRoom.description || ''}
                onChangeText={text => setNewRoom({...newRoom, description: text})}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />
            </View>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowCreateModal(false)}
                disabled={creating}>
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.createButton, creating && styles.buttonDisabled]}
                onPress={handleCreateRoom}
                disabled={creating}>
                {creating ? (
                  <ActivityIndicator color="#FFF" />
                ) : (
                  <Text style={styles.createButtonText}>Create Room</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFE5E5',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF3B30',
    gap: 12,
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#D32F2F',
    fontWeight: '500',
  },
  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#FF3B30',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  listContainer: {
    padding: 16,
  },
  chatRoomCard: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  chatRoomIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatRoomDetails: {
    flex: 1,
    marginLeft: 16,
  },
  chatRoomHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  chatRoomName: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1D1D1F',
    flex: 1,
  },
  chatRoomTime: {
    fontSize: 13,
    color: '#8E8E93',
    marginLeft: 8,
  },
  chatRoomFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lastMessage: {
    fontSize: 14,
    color: '#8E8E93',
    flex: 1,
  },
  unreadBadge: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    minWidth: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 8,
    marginLeft: 12,
  },
  unreadText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '700',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 60,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#8E8E93',
    marginTop: 20,
    fontWeight: '600',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#C7C7CC',
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 20,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    paddingBottom: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1D1D1F',
  },
  closeButton: {
    padding: 4,
  },
  modalBody: {
    padding: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 10,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#F9F9F9',
    color: '#333',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  typeContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#DDD',
    backgroundColor: '#F9F9F9',
    gap: 8,
  },
  typeButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  typeButtonTextActive: {
    color: '#FFF',
  },
  modalFooter: {
    flexDirection: 'row',
    gap: 12,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  modalButton: {
    flex: 1,
    padding: 16,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    backgroundColor: '#F0F0F0',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  createButton: {
    backgroundColor: '#007AFF',
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});

export default MessageListScreen;
