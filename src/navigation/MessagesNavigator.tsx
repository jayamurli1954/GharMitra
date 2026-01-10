import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import MessageListScreen from '../screens/messages/MessageListScreen';
import ChatRoomScreen from '../screens/messages/ChatRoomScreen';

const Stack = createStackNavigator();

const MessagesNavigator = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: '#007AFF',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}>
      <Stack.Screen
        name="MessageList"
        component={MessageListScreen}
        options={{title: 'Messages'}}
      />
      <Stack.Screen
        name="ChatRoom"
        component={ChatRoomScreen}
        options={({route}: any) => ({title: route.params?.roomName || 'Chat'})}
      />
    </Stack.Navigator>
  );
};

export default MessagesNavigator;
