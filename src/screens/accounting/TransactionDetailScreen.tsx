import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import firestore from '@react-native-firebase/firestore';
import Icon from 'react-native-vector-icons/Ionicons';
import {Transaction} from '../../types/models';

const TransactionDetailScreen = ({route, navigation}: any) => {
  const {transactionId} = route.params;
  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTransaction();
  }, []);

  const loadTransaction = async () => {
    try {
      const doc = await firestore()
        .collection('transactions')
        .doc(transactionId)
        .get();

      if (doc.exists) {
        const data = doc.data();
        setTransaction({
          id: doc.id,
          type: data!.type,
          category: data!.category,
          amount: data!.amount,
          description: data!.description,
          date: data!.date.toDate(),
          addedBy: data!.addedBy,
          createdAt: data!.createdAt.toDate(),
        });
      }
    } catch (error) {
      console.error('Error loading transaction:', error);
      Alert.alert('Error', 'Failed to load transaction details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Transaction',
      'Are you sure you want to delete this transaction?',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await firestore()
                .collection('transactions')
                .doc(transactionId)
                .delete();
              Alert.alert('Success', 'Transaction deleted successfully', [
                {text: 'OK', onPress: () => navigation.goBack()},
              ]);
            } catch (error) {
              console.error('Error deleting transaction:', error);
              Alert.alert('Error', 'Failed to delete transaction');
            }
          },
        },
      ],
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (!transaction) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="alert-circle-outline" size={60} color="#F44336" />
        <Text style={styles.errorText}>Transaction not found</Text>
      </View>
    );
  }

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };

  return (
    <ScrollView style={styles.container}>
      <View
        style={[
          styles.header,
          transaction.type === 'income' ? styles.headerIncome : styles.headerExpense,
        ]}>
        <Icon
          name={transaction.type === 'income' ? 'arrow-down-circle' : 'arrow-up-circle'}
          size={60}
          color={transaction.type === 'income' ? '#4CAF50' : '#F44336'}
        />
        <Text style={styles.amountText}>
          {transaction.type === 'income' ? '+' : '-'}
          {formatCurrency(transaction.amount)}
        </Text>
        <Text style={styles.typeText}>
          {transaction.type === 'income' ? 'Income' : 'Expense'}
        </Text>
      </View>

      <View style={styles.detailsContainer}>
        <View style={styles.detailRow}>
          <View style={styles.detailLabel}>
            <Icon name="pricetag-outline" size={20} color="#666" />
            <Text style={styles.detailLabelText}>Category</Text>
          </View>
          <Text style={styles.detailValue}>{transaction.category}</Text>
        </View>

        <View style={styles.detailRow}>
          <View style={styles.detailLabel}>
            <Icon name="document-text-outline" size={20} color="#666" />
            <Text style={styles.detailLabelText}>Description</Text>
          </View>
          <Text style={styles.detailValue}>{transaction.description}</Text>
        </View>

        <View style={styles.detailRow}>
          <View style={styles.detailLabel}>
            <Icon name="calendar-outline" size={20} color="#666" />
            <Text style={styles.detailLabelText}>Date</Text>
          </View>
          <Text style={styles.detailValue}>{formatDate(transaction.date)}</Text>
        </View>

        <View style={styles.detailRow}>
          <View style={styles.detailLabel}>
            <Icon name="time-outline" size={20} color="#666" />
            <Text style={styles.detailLabelText}>Created At</Text>
          </View>
          <Text style={styles.detailValue}>
            {formatDate(transaction.createdAt)}
          </Text>
        </View>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.deleteButton} onPress={handleDelete}>
          <Icon name="trash" size={24} color="#FFF" />
          <Text style={styles.deleteButtonText}>Delete Transaction</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    padding: 40,
  },
  errorText: {
    fontSize: 18,
    color: '#999',
    marginTop: 20,
  },
  header: {
    alignItems: 'center',
    padding: 40,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  headerIncome: {
    backgroundColor: '#E8F5E9',
  },
  headerExpense: {
    backgroundColor: '#FFEBEE',
  },
  amountText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 15,
  },
  typeText: {
    fontSize: 18,
    color: '#666',
    marginTop: 5,
  },
  detailsContainer: {
    margin: 20,
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 20,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  detailRow: {
    marginBottom: 20,
  },
  detailLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  detailLabelText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
    fontWeight: '600',
  },
  detailValue: {
    fontSize: 16,
    color: '#333',
    marginLeft: 28,
  },
  actions: {
    padding: 20,
  },
  deleteButton: {
    flexDirection: 'row',
    backgroundColor: '#F44336',
    borderRadius: 12,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  deleteButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});

export default TransactionDetailScreen;
