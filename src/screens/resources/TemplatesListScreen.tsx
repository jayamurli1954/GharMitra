import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {templateService, Template} from '../../services/resourceService';
import {useNavigation, useRoute} from '@react-navigation/native';

const TemplatesListScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();
  // @ts-ignore
  const {category, categoryName} = route.params || {};

  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [category]);

  const loadTemplates = async () => {
    try {
      const templatesList = await templateService.getTemplates({category});
      setTemplates(templatesList);
    } catch (error: any) {
      console.error('Error loading templates:', error);
      Alert.alert('Error', 'Failed to load templates');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadTemplates();
  };

  const handleTemplatePress = async (template: Template) => {
    if (template.template_type === 'blank_download') {
      // Direct download of blank template
      await downloadBlankTemplate(template);
    } else {
      // Navigate to fill form
      // @ts-ignore
      navigation.navigate('GenerateDocument', {template});
    }
  };

  const downloadBlankTemplate = async (template: Template) => {
    try {
      setDownloadingId(template.id);
      const blob = await templateService.downloadBlankTemplate(template.id);

      // For React Native, we'll show a success message
      // The PDF blob is available but needs to be saved using react-native-fs
      // For now, we'll just confirm the download
      Alert.alert(
        'Template Ready',
        'The template PDF has been generated successfully. In production, this will be saved to your device.',
        [
          {
            text: 'OK',
            onPress: () => {
              // TODO: In production, use react-native-fs to save the file:
              // import RNFS from 'react-native-fs';
              // const path = `${RNFS.DocumentDirectoryPath}/${template.template_code}_blank.pdf`;
              // await RNFS.writeFile(path, blob, 'base64');
            },
          },
        ]
      );
      setDownloadingId(null);
    } catch (error: any) {
      console.error('Error downloading template:', error);
      Alert.alert('Error', 'Failed to download template');
      setDownloadingId(null);
    }
  };

  const renderTemplate = ({item}: {item: Template}) => {
    const isDownloading = downloadingId === item.id;

    return (
      <TouchableOpacity
        style={styles.templateCard}
        onPress={() => handleTemplatePress(item)}
        disabled={isDownloading}
        activeOpacity={0.7}>
        <View style={styles.templateIcon}>
          <Icon
            name={
              item.template_type === 'blank_download'
                ? 'document-outline'
                : 'create-outline'
            }
            size={32}
            color="#007AFF"
          />
        </View>
        <View style={styles.templateInfo}>
          <Text style={styles.templateName}>{item.template_name}</Text>
          {item.description && (
            <Text style={styles.templateDescription} numberOfLines={2}>
              {item.description}
            </Text>
          )}
          <View style={styles.templateMeta}>
            {item.can_autofill && (
              <View style={styles.metaBadge}>
                <Icon name="checkmark-circle" size={14} color="#4CAF50" />
                <Text style={styles.metaBadgeText}>Auto-fill</Text>
              </View>
            )}
            <View
              style={[
                styles.metaBadge,
                item.template_type === 'blank_download'
                  ? styles.typeBadgeBlank
                  : styles.typeBadgeGenerate,
              ]}>
              <Text
                style={[
                  styles.typeBadgeText,
                  item.template_type === 'blank_download'
                    ? styles.typeBadgeTextBlank
                    : styles.typeBadgeTextGenerate,
                ]}>
                {item.template_type === 'blank_download' ? 'Blank' : 'Generate'}
              </Text>
            </View>
          </View>
        </View>
        {isDownloading ? (
          <ActivityIndicator size="small" color="#007AFF" />
        ) : (
          <Icon
            name={
              item.template_type === 'blank_download'
                ? 'download-outline'
                : 'chevron-forward'
            }
            size={24}
            color="#007AFF"
          />
        )}
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading templates...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={templates}
        renderItem={renderTemplate}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        ListEmptyComponent={() => (
          <View style={styles.emptyContainer}>
            <Icon name="document-outline" size={60} color="#C7C7CC" />
            <Text style={styles.emptyText}>No templates in this category</Text>
            <Text style={styles.emptySubtext}>
              Templates will appear here when available
            </Text>
          </View>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  list: {
    padding: 16,
  },
  templateCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  templateIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  templateInfo: {
    flex: 1,
  },
  templateName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  templateDescription: {
    fontSize: 13,
    color: '#666',
    marginBottom: 8,
  },
  templateMeta: {
    flexDirection: 'row',
    gap: 8,
  },
  metaBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    gap: 4,
  },
  metaBadgeText: {
    fontSize: 11,
    color: '#4CAF50',
    fontWeight: '500',
  },
  typeBadge: {
    backgroundColor: '#E3F2FD',
  },
  typeBadgeBlank: {
    backgroundColor: '#FFF3E0',
  },
  typeBadgeGenerate: {
    backgroundColor: '#E3F2FD',
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: '500',
  },
  typeBadgeTextBlank: {
    color: '#FF9800',
  },
  typeBadgeTextGenerate: {
    color: '#007AFF',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
});

export default TemplatesListScreen;

