/**
 * Under Development Component
 * Displays a friendly message for features that are coming soon
 */
import React from 'react';
import {View, Text, StyleSheet} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

interface UnderDevelopmentProps {
  featureName?: string;
  estimatedTime?: string;
  message?: string;
}

const UnderDevelopment: React.FC<UnderDevelopmentProps> = ({
  featureName,
  estimatedTime,
  message,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.iconContainer}>
        <Icon name="construct" size={64} color="#FF9800" />
      </View>
      <Text style={styles.title}>Under Development</Text>
      {featureName && (
        <Text style={styles.featureName}>{featureName}</Text>
      )}
      <Text style={styles.message}>
        {message || 'This feature is currently being developed and will be available shortly.'}
      </Text>
      {estimatedTime && (
        <View style={styles.timeContainer}>
          <Icon name="time-outline" size={16} color="#666" />
          <Text style={styles.estimatedTime}>Estimated: {estimatedTime}</Text>
        </View>
      )}
      <View style={styles.infoBox}>
        <Icon name="information-circle-outline" size={20} color="#007AFF" />
        <Text style={styles.infoText}>
          We're working hard to bring you this feature. Check back soon!
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
    backgroundColor: '#F5F5F7',
  },
  iconContainer: {
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1D1D1F',
    marginBottom: 8,
    textAlign: 'center',
  },
  featureName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
    marginBottom: 16,
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 20,
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    gap: 6,
  },
  estimatedTime: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    padding: 16,
    borderRadius: 12,
    alignItems: 'flex-start',
    gap: 12,
    maxWidth: '90%',
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#1976D2',
    lineHeight: 20,
  },
});

export default UnderDevelopment;








