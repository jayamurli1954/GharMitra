import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

interface ActivityItemProps {
  type: string;
  title: string;
  description: string;
  amount?: number;
  timestamp: string;
  icon: string;
  color: string;
}

export const ActivityItem: React.FC<ActivityItemProps> = ({
  type,
  title,
  description,
  amount,
  timestamp,
  icon,
  color,
}) => {
  const formatCurrency = (value: number) => {
    return `₹${value.toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
    });
  };

  return (
    <View style={styles.container}>
      <View style={[styles.iconContainer, {backgroundColor: color + '20'}]}>
        <Icon name={icon} size={20} color={color} />
      </View>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
          <Text style={styles.timestamp}>{formatTime(timestamp)}</Text>
        </View>
        <Text style={styles.description} numberOfLines={2}>
          {description}
        </Text>
        {amount !== undefined && amount > 0 && (
          <Text style={[styles.amount, {color}]}>
            {type === 'payment' ? '+' : '-'}{formatCurrency(amount)}
          </Text>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D1D1F',
    flex: 1,
    marginRight: 8,
  },
  timestamp: {
    fontSize: 11,
    color: '#8E8E93',
  },
  description: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 4,
  },
  amount: {
    fontSize: 15,
    fontWeight: 'bold',
  },
});


