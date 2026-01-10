import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import ResourceCenterScreen from '../screens/resources/ResourceCenterScreen';
import TemplatesListScreen from '../screens/resources/TemplatesListScreen';
import GenerateDocumentScreen from '../screens/resources/GenerateDocumentScreen';

const Stack = createStackNavigator();

const ResourceNavigator = () => {
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
        name="ResourceCenterHome"
        component={ResourceCenterScreen}
        options={{title: 'Resource Center'}}
      />
      <Stack.Screen
        name="TemplatesList"
        component={TemplatesListScreen}
        options={({route}: any) => ({
          title: route.params?.categoryName || 'Templates',
        })}
      />
      <Stack.Screen
        name="GenerateDocument"
        component={GenerateDocumentScreen}
        options={({route}: any) => ({
          title: route.params?.template?.template_name || 'Generate Document',
        })}
      />
    </Stack.Navigator>
  );
};

export default ResourceNavigator;



