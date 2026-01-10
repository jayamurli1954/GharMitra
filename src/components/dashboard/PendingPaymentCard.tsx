import React from 'react';
import {View, Text, StyleSheet, TouchableOpacity} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

interface PendingPaymentCardProps {
  flatNumber: string;
  memberName: string;
  amountDue: number;
  billMonth: string;
  daysOverdue: number;
  onPress?: () => void;
}

export const PendingPaymentCard: React.FC<PendingPaymentCardProps> = ({
  flatNumber,
  memberName,
  amountDue,
  billMonth,
  daysOverdue,
  onPress,
}) => {
  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.7}
      disabled={!onPress}>
      <View style={styles.header}>
        <View style={styles.flatInfo}>
          <View style={styles.flatBadge}>
            <Text style={styles.flatNumber}>{flatNumber}</Text>
          </View>
          <View style={styles.memberInfo}>
            <Text style={styles.memberName}>{memberName}</Text>
            <Text style={styles.billMonth}>{billMonth}</Text>
          </View>
        </View>
        {daysOverdue > 0 && (
          <View style={styles.overdueBadge}>
            <Icon name="time" size={12} color="#FFF" />
            <Text style={styles.overdueText}>{daysOverdue}d</Text>
          </View>
        )}
      </View>
      <View style={styles.footer}>
        <Text style={styles.amountLabel}>Amount Due:</Text>
        <Text style={styles.amountValue}>{formatCurrency(amountDue)}</Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  flatInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  flatBadge: {
    backgroundColor: '#E3F2FD',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    marginRight: 10,
  },
  flatNumber: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  memberInfo: {
    flex: 1,
  },
  memberName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 2,
  },
  billMonth: {
    fontSize: 12,
    color: '#8E8E93',
  },
  overdueBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F44336',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  overdueText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#FFF',
    marginLeft: 4,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  amountLabel: {
    fontSize: 13,
    color: '#8E8E93',
  },
  amountValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FF9800',
  },
});


