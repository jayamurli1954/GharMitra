import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import MembersScreen from '../screens/members/MembersScreen';
import PhysicalDocumentsScreen from '../screens/members/PhysicalDocumentsScreen';
import BulkImportScreen from '../screens/members/BulkImportScreen';
import AddMemberScreen from '../screens/members/AddMemberScreen';

const Stack = createStackNavigator();

const MembersNavigator = () => {
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
        name="MembersList"
        component={MembersScreen}
        options={{title: 'Members'}}
      />
      <Stack.Screen
        name="AddMember"
        component={AddMemberScreen}
        options={{title: 'Add Member'}}
      />
      <Stack.Screen
        name="BulkImport"
        component={BulkImportScreen}
        options={{title: 'Bulk Import Members'}}
      />
      <Stack.Screen
        name="PhysicalDocuments"
        component={PhysicalDocumentsScreen}
        options={{title: 'Physical Documents'}}
      />
    </Stack.Navigator>
  );
};

export default MembersNavigator;






