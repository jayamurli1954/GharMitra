import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {legalService} from '../../services/legalService';
import Markdown from 'react-native-markdown-display';

const TermsScreen = ({navigation}: any) => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState<string>('');
  const [lastUpdated, setLastUpdated] = useState<string>('');

  useEffect(() => {
    loadTerms();
  }, []);

  const loadTerms = async () => {
    try {
      setLoading(true);
      const document = await legalService.getTermsOfService();
      setContent(document.content);
      setVersion(document.version);
      setLastUpdated(document.last_updated);
    } catch (error: any) {
      console.error('Error loading Terms of Service:', error);
      Alert.alert(
        'Error',
        'Failed to load Terms of Service. Please try again later.',
        [{text: 'OK', onPress: () => navigation.goBack()}],
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading Terms of Service...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color="#FFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Terms of Service</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Version Info */}
      <View style={styles.versionContainer}>
        <Text style={styles.versionText}>Version {version}</Text>
        {lastUpdated && (
          <Text style={styles.updatedText}>
            Last Updated: {new Date(lastUpdated).toLocaleDateString()}
          </Text>
        )}
      </View>

      {/* Content */}
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.contentContainer}>
        <Markdown style={markdownStyles}>{content}</Markdown>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingTop: 50,
    paddingBottom: 15,
    paddingHorizontal: 15,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  placeholder: {
    width: 40,
  },
  versionContainer: {
    backgroundColor: '#F5F5F7',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  versionText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  updatedText: {
    fontSize: 11,
    color: '#999',
    marginTop: 4,
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
  },
});

const markdownStyles = {
  body: {
    fontSize: 16,
    lineHeight: 24,
    color: '#1D1D1F',
  },
  heading1: {
    fontSize: 28,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 10,
    color: '#1D1D1F',
  },
  heading2: {
    fontSize: 22,
    fontWeight: 'bold',
    marginTop: 18,
    marginBottom: 8,
    color: '#1D1D1F',
  },
  heading3: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
    marginBottom: 6,
    color: '#1D1D1F',
  },
  paragraph: {
    marginBottom: 12,
    fontSize: 16,
    lineHeight: 24,
  },
  listItem: {
    marginBottom: 8,
    paddingLeft: 8,
  },
  strong: {
    fontWeight: 'bold',
  },
  link: {
    color: '#007AFF',
    textDecorationLine: 'underline',
  },
};

export default TermsScreen;






