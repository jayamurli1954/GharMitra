/**
 * GharKhata - Main Tab Navigator with Material Community Icons
 * Complete working bottom navigation
 * 
 * File location: src/navigation/MainTabNavigator.tsx
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Platform } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Import your screens (adjust paths as needed)
import DashboardScreen from '../screens/dashboard/DashboardScreen';
// import BillsScreen from '../screens/bills/BillsScreen';
// import AccountingScreen from '../screens/accounting/AccountingScreen';
// import MessagesScreen from '../screens/messages/MessagesScreen';
// import MembersScreen from '../screens/members/MembersScreen';
// import ProfileScreen from '../screens/profile/ProfileScreen';

const Tab = createBottomTabNavigator();

// Tab configuration with icons
const TAB_CONFIG = {
  Dashboard: {
    icon: 'view-dashboard',
    label: 'Dashboard',
  },
  Bills: {
    icon: 'receipt',
    label: 'Bills',
  },
  Accounting: {
    icon: 'calculator',
    label: 'Accounting',
  },
  Messages: {
    icon: 'message-text',
    label: 'Messages',
  },
  Members: {
    icon: 'account-group',
    label: 'Members',
  },
  Profile: {
    icon: 'account-circle',
    label: 'Profile',
  },
};

const MainTabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          const config = TAB_CONFIG[route.name];
          const iconName = config?.icon || 'help-circle';
          
          return (
            <Icon 
              name={iconName} 
              size={size} 
              color={color}
            />
          );
        },
        tabBarActiveTintColor: '#2196F3',
        tabBarInactiveTintColor: '#9E9E9E',
        tabBarStyle: {
          height: Platform.OS === 'ios' ? 88 : 60,
          paddingBottom: Platform.OS === 'ios' ? 28 : 8,
          paddingTop: 8,
          borderTopWidth: 1,
          borderTopColor: '#E0E0E0',
          elevation: 8,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.1,
          shadowRadius: 4,
          backgroundColor: '#FFFFFF',
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
        tabBarItemStyle: {
          paddingVertical: 4,
        },
        headerShown: false,
        tabBarHideOnKeyboard: true,
      })}
    >
      <Tab.Screen 
        name="Dashboard" 
        component={DashboardScreen}
        options={{
          tabBarBadge: undefined,
        }}
      />
      
      {/* Uncomment as you add screens
      <Tab.Screen 
        name="Bills" 
        component={BillsScreen}
      />
      
      <Tab.Screen 
        name="Accounting" 
        component={AccountingScreen}
      />
      
      <Tab.Screen 
        name="Messages" 
        component={MessagesScreen}
        options={{
          tabBarBadge: 3,
        }}
      />
      
      <Tab.Screen 
        name="Members" 
        component={MembersScreen}
      />
      
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
      />
      */}
    </Tab.Navigator>
  );
};

export default MainTabNavigator;
