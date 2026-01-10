import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';

// Import screens
import ApartmentSettingsScreen from '../screens/settings/ApartmentSettingsScreen';
import SelectFixedExpensesScreen from '../screens/settings/SelectFixedExpensesScreen';
import FlatsListScreen from '../screens/flats/FlatsListScreen';
import AddEditFlatScreen from '../screens/flats/AddEditFlatScreen';
import GenerateBillsScreen from '../screens/maintenance/GenerateBillsScreen';
import AddWaterExpenseScreen from '../screens/maintenance/AddWaterExpenseScreen';
import BillHistoryScreen from '../screens/maintenance/BillHistoryScreen';

const Stack = createStackNavigator();

const MaintenanceNavigator = () => {
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
        name="GenerateBills"
        component={GenerateBillsScreen}
        options={{title: 'Generate Bills'}}
      />
      <Stack.Screen
        name="ApartmentSettings"
        component={ApartmentSettingsScreen}
        options={{title: 'Apartment Settings'}}
      />
      <Stack.Screen
        name="SelectFixedExpenses"
        component={SelectFixedExpensesScreen}
        options={{title: 'Select Fixed Expenses'}}
      />
      <Stack.Screen
        name="FlatsList"
        component={FlatsListScreen}
        options={{title: 'Manage Flats'}}
      />
      <Stack.Screen
        name="AddEditFlat"
        component={AddEditFlatScreen}
        options={{title: 'Flat Details'}}
      />
      <Stack.Screen
        name="AddWaterExpense"
        component={AddWaterExpenseScreen}
        options={{title: 'Water Expense'}}
      />
      <Stack.Screen
        name="BillHistory"
        component={BillHistoryScreen}
        options={{title: 'Bill History'}}
      />
    </Stack.Navigator>
  );
};

export default MaintenanceNavigator;
