import React, {useEffect, useState, useRef} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  RefreshControl,
  Keyboard,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {messagesService, Message} from '../../services/messagesService';
import {authService} from '../../services/authService';

const ChatRoomScreen = ({route}: any) => {
  const {roomId, roomName} = route.params;
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const isTypingRef = useRef(false);

  // Keep ref in sync with state
  useEffect(() => {
    isTypingRef.current = isTyping;
  }, [isTyping]);

  useEffect(() => {
    loadUser();
    loadMessages();
    // Poll for new messages every 5 seconds (reduced frequency)
    // Only poll when user is not typing
    const interval = setInterval(() => {
      if (!isTypingRef.current) {
        loadMessages(true);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [roomId]);

  const loadUser = async () => {
    try {
      const user = await authService.getStoredUser();
      setCurrentUserId(user?.id || null);
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const loadMessages = async (silent = false) => {
    try {
      if (!silent && !refreshing) {
        setLoading(true);
      }
      const messagesList = await messagesService.getMessages(roomId);
      // Map API messages to component format
      const mappedMessages = messagesList.map(msg => ({
        id: msg.id,
        roomId: msg.room_id,
        senderId: msg.sender_id,
        senderName: msg.sender_name,
        text: msg.content || msg.text || '',
        timestamp: new Date(msg.created_at),
        read: true, // Backend doesn't track read status yet
      }));
      setMessages(mappedMessages);
    } catch (error: any) {
      console.error('Error loading messages:', error);
      // Don't show error alert for polling - only for initial load or refresh
      if (!silent && !refreshing) {
        // Error will be handled silently - empty state will show
      }
    } finally {
      if (!silent) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  };

  const handleSend = async () => {
    if (!newMessage.trim()) return;

    setSending(true);
    setIsTyping(false);
    try {
      await messagesService.sendMessage(roomId, {text: newMessage.trim()});
      setNewMessage('');
      // Reload messages to show the new one
      await loadMessages(true);
      // Keep keyboard open after sending
      inputRef.current?.focus();
    } catch (error: any) {
      console.error('Error sending message:', error);
      const errorMessage = error?.response?.data?.detail || 
                          error?.message || 
                          error?.data?.message ||
                          'Failed to send message. Please try again.';
      alert(`Error: ${errorMessage}`);
    } finally {
      setSending(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderMessage = ({item}: {item: any}) => {
    const isOwnMessage = item.senderId === currentUserId;

    return (
      <View
        style={[
          styles.messageContainer,
          isOwnMessage ? styles.ownMessage : styles.otherMessage,
        ]}>
        {!isOwnMessage && (
          <Text style={styles.senderName}>{item.senderName}</Text>
        )}
        <View
          style={[
            styles.messageBubble,
            isOwnMessage ? styles.ownBubble : styles.otherBubble,
          ]}>
          <Text
            style={[
              styles.messageText,
              isOwnMessage ? styles.ownMessageText : styles.otherMessageText,
            ]}>
            {item.text}
          </Text>
          <Text
            style={[
              styles.messageTime,
              isOwnMessage ? styles.ownMessageTime : styles.otherMessageTime,
            ]}>
            {formatTime(item.timestamp)}
          </Text>
        </View>
      </View>
    );
  };

  if (loading && messages.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading messages...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      enabled>
      <FlatList
        ref={flatListRef}
        data={messages.length > 0 ? [...messages].reverse() : []} // Reverse to show newest at bottom
        renderItem={renderMessage}
        keyExtractor={(item, index) => item.id?.toString() || `message-${index}`}
        contentContainerStyle={[
          styles.messagesContainer,
          messages.length === 0 && styles.emptyContainer,
        ]}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="none"
        onScrollBeginDrag={() => {
          // Dismiss keyboard when scrolling
          Keyboard.dismiss();
          setIsTyping(false);
        }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => {
            setRefreshing(true);
            loadMessages();
          }} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Icon name="chatbubbles-outline" size={60} color="#CCC" />
            <Text style={styles.emptyStateText}>No messages yet</Text>
            <Text style={styles.emptyStateSubtext}>
              Start a conversation with your community
            </Text>
          </View>
        }
      />

      <View style={styles.inputContainer}>
        <TextInput
          ref={inputRef}
          style={styles.input}
          placeholder="Type a message..."
          value={newMessage}
          onChangeText={(text) => {
            setNewMessage(text);
            setIsTyping(true);
          }}
          onFocus={() => setIsTyping(true)}
          onBlur={() => {
            // Small delay to allow send button to work
            setTimeout(() => setIsTyping(false), 200);
          }}
          multiline
          maxLength={500}
          blurOnSubmit={false}
          returnKeyType="send"
          onSubmitEditing={handleSend}
          textAlignVertical="center"
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!newMessage.trim() || sending) && styles.sendButtonDisabled,
          ]}
          onPress={handleSend}
          disabled={!newMessage.trim() || sending}>
          <Icon
            name="send"
            size={24}
            color={!newMessage.trim() || sending ? '#CCC' : '#007AFF'}
          />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  messagesContainer: {
    padding: 15,
    flexGrow: 1,
  },
  emptyContainer: {
    justifyContent: 'center',
    flex: 1,
  },
  messageContainer: {
    marginBottom: 15,
    maxWidth: '75%',
  },
  ownMessage: {
    alignSelf: 'flex-end',
  },
  otherMessage: {
    alignSelf: 'flex-start',
  },
  senderName: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
    marginLeft: 12,
  },
  messageBubble: {
    borderRadius: 18,
    padding: 12,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  ownBubble: {
    backgroundColor: '#007AFF',
    borderBottomRightRadius: 4,
  },
  otherBubble: {
    backgroundColor: '#FFF',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 20,
  },
  ownMessageText: {
    color: '#FFF',
  },
  otherMessageText: {
    color: '#333',
  },
  messageTime: {
    fontSize: 11,
    marginTop: 4,
  },
  ownMessageTime: {
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'right',
  },
  otherMessageTime: {
    color: '#999',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 60,
    minHeight: 300,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#999',
    marginTop: 15,
    fontWeight: '600',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#BBB',
    marginTop: 8,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 10,
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  input: {
    flex: 1,
    backgroundColor: '#F5F5F5',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    paddingTop: 10,
    fontSize: 15,
    maxHeight: 100,
    marginRight: 10,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
});

export default ChatRoomScreen;
