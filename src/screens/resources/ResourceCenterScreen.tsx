import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {templateService, TemplateCategory} from '../../services/resourceService';
import {useNavigation} from '@react-navigation/native';

const ResourceCenterScreen = () => {
  const navigation = useNavigation();
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const categoriesList = await templateService.getCategories();
      setCategories(categoriesList);
    } catch (error: any) {
      console.error('Error loading categories:', error);
      Alert.alert('Error', 'Failed to load template categories');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadCategories();
  };

  const getCategoryIcon = (iconName?: string): string => {
    // Map MaterialCommunityIcons to Ionicons
    const iconMap: Record<string, string> = {
      'home-export-outline': 'home-outline',
      'wrench-outline': 'construct-outline',
      'alert-circle-outline': 'alert-circle-outline',
      'check-circle-outline': 'checkmark-circle-outline',
      'gavel': 'hammer-outline',
      'scale-balance': 'scale-outline',
      'email-outline': 'mail-outline',
      'folder-outline': 'folder-outline',
      'currency-inr': 'cash-outline',
      'alert-outline': 'warning-outline',
    };
    return iconMap[iconName || ''] || 'document-text-outline';
  };

  const handleCategoryPress = (category: TemplateCategory) => {
    // @ts-ignore - navigation type will be updated
    navigation.navigate('TemplatesList', {
      category: category.category_code,
      categoryName: category.category_name,
    });
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading resource centre...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }>
      {/* Header */}
      <View style={styles.header}>
        <Icon name="document-text" size={50} color="#007AFF" />
        <Text style={styles.headerTitle}>Resource Centre</Text>
        <Text style={styles.headerSubtitle}>
          Download templates & generate forms
        </Text>
      </View>

      {/* Categories List */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Template Categories</Text>
        <Text style={styles.sectionSubtitle}>
          {categories.length} categories available
        </Text>

        {categories.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Icon name="document-outline" size={60} color="#C7C7CC" />
            <Text style={styles.emptyText}>No categories found</Text>
            <Text style={styles.emptySubtext}>
              Template categories will appear here
            </Text>
          </View>
        ) : (
          categories.map(category => (
            <TouchableOpacity
              key={category.category_code}
              style={styles.categoryCard}
              onPress={() => handleCategoryPress(category)}
              activeOpacity={0.7}>
              <View style={styles.categoryIcon}>
                <Icon
                  name={getCategoryIcon(category.icon_name)}
                  size={32}
                  color="#007AFF"
                />
              </View>
              <View style={styles.categoryInfo}>
                <Text style={styles.categoryName}>
                  {category.category_name}
                </Text>
                {category.category_description && (
                  <Text style={styles.categoryDescription} numberOfLines={2}>
                    {category.category_description}
                  </Text>
                )}
                <Text style={styles.templateCount}>
                  {category.template_count} template
                  {category.template_count !== 1 ? 's' : ''} available
                </Text>
              </View>
              <Icon name="chevron-forward" size={24} color="#C7C7CC" />
            </TouchableOpacity>
          ))
        )}
      </View>

      {/* Info Box */}
      <View style={styles.infoBox}>
        <Icon name="information-circle" size={24} color="#007AFF" />
        <View style={styles.infoContent}>
          <Text style={styles.infoTitle}>About Resource Centre</Text>
          <Text style={styles.infoText}>
            Access downloadable templates and generate forms with auto-fill.
            Generated documents are saved to your device only - we do not store
            filled forms online.
          </Text>
        </View>
      </View>
    </ScrollView>
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
  header: {
    backgroundColor: '#FFF',
    padding: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1D1D1F',
    marginTop: 12,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
    textAlign: 'center',
  },
  section: {
    backgroundColor: '#FFF',
    padding: 20,
    marginTop: 1,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
  categoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAFAFA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  categoryIcon: {
    width: 56,
    height: 56,
    borderRadius: 12,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  categoryDescription: {
    fontSize: 13,
    color: '#666',
    marginBottom: 6,
  },
  templateCount: {
    fontSize: 12,
    color: '#007AFF',
    fontWeight: '500',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 40,
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
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    margin: 20,
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});

export default ResourceCenterScreen;
