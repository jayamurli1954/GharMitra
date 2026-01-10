import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface StatCardProps {
  label: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: string;
  color: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  change,
  trend,
  icon,
  color,
}) => {
  const getTrendIcon = () => {
    if (trend === 'up') return 'trending-up';
    if (trend === 'down') return 'trending-down';
    return 'minus';
  };

  const getTrendColor = () => {
    if (trend === 'up') return '#4CAF50';
    if (trend === 'down') return '#F44336';
    return '#8E8E93';
  };

  return (
    <View style={styles.card}>
      <View style={[styles.iconContainer, {backgroundColor: color + '20'}]}>
        <Icon name={icon} size={28} color={color} />
      </View>
      <View style={styles.content}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.value}>{value}</Text>
        {change && (
          <View style={styles.changeContainer}>
            <Icon name={getTrendIcon()} size={14} color={getTrendColor()} />
            <Text style={[styles.changeText, {color: getTrendColor()}]}>
              {change}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  content: {
    flex: 1,
  },
  label: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 4,
  },
  value: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  changeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  changeText: {
    fontSize: 12,
    marginLeft: 4,
    fontWeight: '600',
  },
});


