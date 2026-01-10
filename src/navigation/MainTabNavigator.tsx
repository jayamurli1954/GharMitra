import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {Text} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

import EnhancedDashboardScreen from '../screens/dashboard/EnhancedDashboardScreen';
import AccountingNavigator from './AccountingNavigator';
import MaintenanceNavigator from './MaintenanceNavigator';
import MessagesNavigator from './MessagesNavigator';
import ReportsNavigator from './ReportsNavigator';
import MembersNavigator from './MembersNavigator';
import MeetingsNavigator from './MeetingsNavigator';
import ProfileScreen from '../screens/profile/ProfileScreen';

const Tab = createBottomTabNavigator();

const MainTabNavigator = () => {
  // Define colors for each tab
  const getTabColor = (routeName: string): string => {
    const colorMap: Record<string, string> = {
      'Dashboard': '#007AFF', // Blue
      'Accounting': '#34C759', // Green
      'Maintenance': '#FF9500', // Orange
      'Messages': '#5856D6', // Purple
      'Reports': '#FF2D55', // Pink
      'Members': '#5AC8FA', // Light Blue
      'Meetings': '#FF3B30', // Red
      'Profile': '#AF52DE', // Purple
    };
    return colorMap[routeName] || '#007AFF';
  };

  return (
    <Tab.Navigator
      screenOptions={({route}) => {
        const activeColor = getTabColor(route.name);
        return {
          tabBarIcon: ({focused, size, color}) => {
            let iconName: string = 'home';

            if (route.name === 'Dashboard') {
              iconName = focused ? 'home' : 'home-outline';
            } else if (route.name === 'Accounting') {
              iconName = focused ? 'wallet' : 'wallet-outline';
            } else if (route.name === 'Maintenance') {
              iconName = focused ? 'receipt' : 'receipt-outline';
            } else if (route.name === 'Messages') {
              iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
            } else if (route.name === 'Reports') {
              iconName = focused ? 'bar-chart' : 'bar-chart-outline';
            } else if (route.name === 'Members') {
              iconName = focused ? 'people' : 'people-outline';
            } else if (route.name === 'Meetings') {
              iconName = focused ? 'calendar' : 'calendar-outline';
            } else if (route.name === 'Profile') {
              iconName = focused ? 'person' : 'person-outline';
            }

            // Use the activeColor for focused, gray for inactive
            const iconColor = focused ? activeColor : '#8E8E93';
            return <Icon name={iconName} size={size} color={iconColor} />;
          },
          tabBarActiveTintColor: activeColor,
          tabBarInactiveTintColor: '#8E8E93',
          headerShown: true,
          headerStyle: {
            backgroundColor: '#007AFF',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        };
      }}>
      <Tab.Screen
        name="Dashboard"
        component={EnhancedDashboardScreen}
        options={{
          title: 'Dashboard',
          tabBarActiveTintColor: '#007AFF',
        }}
      />
      <Tab.Screen
        name="Maintenance"
        component={MaintenanceNavigator}
        options={{
          title: 'Bills',
          headerShown: false,
          tabBarActiveTintColor: '#FF9500',
        }}
      />
      <Tab.Screen
        name="Accounting"
        component={AccountingNavigator}
        options={{
          title: 'Accounting',
          headerShown: false,
          tabBarActiveTintColor: '#34C759',
        }}
      />
      <Tab.Screen
        name="Messages"
        component={MessagesNavigator}
        options={{
          title: 'Messages',
          headerShown: false,
          tabBarActiveTintColor: '#5856D6',
        }}
      />
      <Tab.Screen
        name="Reports"
        component={ReportsNavigator}
        options={{
          title: 'Reports',
          headerShown: false,
          tabBarActiveTintColor: '#FF2D55',
        }}
      />
      <Tab.Screen
        name="Members"
        component={MembersNavigator}
        options={{
          title: 'Members',
          headerShown: false,
          tabBarActiveTintColor: '#5AC8FA',
        }}
      />
      <Tab.Screen
        name="Meetings"
        component={MeetingsNavigator}
        options={{
          title: 'Meetings',
          headerShown: false,
          tabBarActiveTintColor: '#FF3B30',
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: 'Profile',
          tabBarActiveTintColor: '#AF52DE',
        }}
      />
    </Tab.Navigator>
  );
};

export default MainTabNavigator;
