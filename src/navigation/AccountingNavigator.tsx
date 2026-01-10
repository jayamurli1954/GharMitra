import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import AccountingListScreen from '../screens/accounting/AccountingListScreen';
import AddTransactionScreen from '../screens/accounting/AddTransactionScreen';
import TransactionDetailScreen from '../screens/accounting/TransactionDetailScreen';
import OpeningBalanceScreen from '../screens/accounting/OpeningBalanceScreen';

const Stack = createStackNavigator();

const AccountingNavigator = () => {
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
        name="AccountingList"
        component={AccountingListScreen}
        options={{title: 'Accounting'}}
      />
      <Stack.Screen
        name="AddTransaction"
        component={AddTransactionScreen}
        options={{title: 'Add Transaction'}}
      />
      <Stack.Screen
        name="TransactionDetail"
        component={TransactionDetailScreen}
        options={{title: 'Transaction Details'}}
      />
      <Stack.Screen
        name="OpeningBalance"
        component={OpeningBalanceScreen}
        options={{title: 'Opening Balances'}}
      />
    </Stack.Navigator>
  );
};

export default AccountingNavigator;
