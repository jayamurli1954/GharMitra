import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import ReportsDashboardScreen from '../screens/reports/ReportsDashboardScreen';
import TrialBalanceReportScreen from '../screens/reports/TrialBalanceReportScreen';
import GeneralLedgerReportScreen from '../screens/reports/GeneralLedgerReportScreen';
import OpeningBalanceScreen from '../screens/accounting/OpeningBalanceScreen';
import CashBookLedgerScreen from '../screens/reports/CashBookLedgerScreen';
import BankLedgerScreen from '../screens/reports/BankLedgerScreen';
import MemberTransactionLedgerScreen from '../screens/reports/MemberTransactionLedgerScreen';
import JournalEntryScreen from '../screens/accounting/JournalEntryScreen';
import JournalEntryReportScreen from '../screens/reports/JournalEntryReportScreen';
// Import other report screens as they are created

const Stack = createStackNavigator();

const ReportsNavigator = () => {
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
        name="ReportsDashboard"
        component={ReportsDashboardScreen}
        options={{title: 'Financial Reports'}}
      />
      <Stack.Screen
        name="TrialBalanceReport"
        component={TrialBalanceReportScreen}
        options={{title: 'Trial Balance'}}
      />
      <Stack.Screen
        name="GeneralLedgerReport"
        component={GeneralLedgerReportScreen}
        options={{title: 'General Ledger Report'}}
      />
      <Stack.Screen
        name="OpeningBalance"
        component={OpeningBalanceScreen}
        options={{title: 'Opening Balances'}}
      />
      <Stack.Screen
        name="CashBookLedger"
        component={CashBookLedgerScreen}
        options={{title: 'Cash Book Ledger'}}
      />
      <Stack.Screen
        name="BankLedger"
        component={BankLedgerScreen}
        options={{title: 'Bank Ledger'}}
      />
      <Stack.Screen
        name="MemberLedger"
        component={MemberTransactionLedgerScreen}
        options={{title: 'Member Transaction Ledger'}}
      />
      <Stack.Screen
        name="JournalEntry"
        component={JournalEntryScreen}
        options={{title: 'Create Journal Entry'}}
      />
      <Stack.Screen
        name="JournalEntryReport"
        component={JournalEntryReportScreen}
        options={{title: 'Journal Entries'}}
      />
      {/* Add other report screens here as they are created */}
    </Stack.Navigator>
  );
};

export default ReportsNavigator;
