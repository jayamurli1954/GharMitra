import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/Ionicons';

import MeetingsListScreen from '../screens/meetings/MeetingsListScreen';
import MeetingDetailsScreen from '../screens/meetings/MeetingDetailsScreen';
import CreateMeetingScreen from '../screens/meetings/CreateMeetingScreen';
import MarkAttendanceScreen from '../screens/meetings/MarkAttendanceScreen';
import RecordMinutesScreen from '../screens/meetings/RecordMinutesScreen';

const Stack = createStackNavigator();

const MeetingsNavigator = () => {
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
        name="MeetingsList"
        component={MeetingsListScreen}
        options={{
          title: 'Meetings',
          headerRight: () => (
            <Icon name="calendar-outline" size={24} color="#fff" style={{marginRight: 16}} />
          ),
        }}
      />
      <Stack.Screen
        name="MeetingDetails"
        component={MeetingDetailsScreen}
        options={{
          title: 'Meeting Details',
        }}
      />
      <Stack.Screen
        name="CreateMeeting"
        component={CreateMeetingScreen}
        options={{
          title: 'Create Meeting',
        }}
      />
      <Stack.Screen
        name="MarkAttendance"
        component={MarkAttendanceScreen}
        options={{
          title: 'Mark Attendance',
        }}
      />
      <Stack.Screen
        name="RecordMinutes"
        component={RecordMinutesScreen}
        options={{
          title: 'Record Minutes',
        }}
      />
    </Stack.Navigator>
  );
};

export default MeetingsNavigator;





