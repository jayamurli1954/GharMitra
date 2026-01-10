import React, {useEffect, useState, useCallback} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import {useFocusEffect} from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import {flatsService, Flat} from '../../services/flatsService';

const FlatsListScreen = ({navigation}: any) => {
  const [flats, setFlats] = useState<Flat[]>([]);
  const [loading, setLoading] = useState(false);

  const loadFlats = useCallback(async () => {
    setLoading(true);
    try {
      const flatsList = await flatsService.getFlats();
      
      // Validate that all flats have IDs
      const flatsWithIds = flatsList.map(flat => {
        if (!flat.id) {
          console.error('⚠️ Flat missing ID:', {
            flatNumber: flat.flat_number,
            flat: flat,
            hasId: !!flat.id,
          });
        }
        return flat;
      });
      
      // Log first flat to verify structure
      if (flatsWithIds.length > 0) {
        console.log('📋 Loaded flats - First flat structure:', {
          id: flatsWithIds[0].id,
          idType: typeof flatsWithIds[0].id,
          flatNumber: flatsWithIds[0].flat_number,
          allKeys: Object.keys(flatsWithIds[0]),
        });
      }
      
      setFlats(flatsWithIds);
    } catch (error: any) {
      console.error('Error loading flats:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to load flats. Please try again.';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Reload flats when screen comes into focus (e.g., after adding/editing a flat)
  useFocusEffect(
    useCallback(() => {
      // Reload immediately when screen comes into focus
      loadFlats();
    }, [loadFlats])
  );

  // Also listen for navigation focus event as backup
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      // Reload when screen receives focus
      loadFlats();
    });
    return unsubscribe;
  }, [navigation, loadFlats]);

  // Listen for navigation state changes to catch when returning from AddEditFlat
  useEffect(() => {
    const unsubscribe = navigation.addListener('state', () => {
      // Reload when navigation state changes (e.g., returning from another screen)
      loadFlats();
    });
    return unsubscribe;
  }, [navigation, loadFlats]);

  const handleDelete = (flat: Flat) => {
    // Validate flat has an ID before proceeding
    if (!flat.id) {
      console.error('❌ Cannot delete: Flat ID is missing', {
        flat: flat,
        flatNumber: flat.flat_number,
        hasId: !!flat.id,
        idValue: flat.id,
        idType: typeof flat.id,
      });
      Alert.alert(
        'Error',
        `Cannot delete flat ${flat.flat_number}: ID is missing. Please refresh the list and try again.`,
      );
      return;
    }

    const flatIdStr = String(flat.id).trim();
    
    // Validate ID is not empty or invalid
    if (!flatIdStr || flatIdStr === 'undefined' || flatIdStr === 'null' || flatIdStr === '') {
      console.error('❌ Cannot delete: Invalid flat ID', {
        flat: flat,
        flatNumber: flat.flat_number,
        idValue: flat.id,
        idString: flatIdStr,
      });
      Alert.alert(
        'Error',
        `Cannot delete flat ${flat.flat_number}: Invalid ID. Please refresh the list and try again.`,
      );
      return;
    }

    Alert.alert(
      'Delete Flat',
      `Are you sure you want to delete flat ${flat.flat_number}?`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              console.log('🗑️ Deleting flat:', {
                id: flatIdStr,
                idType: typeof flatIdStr,
                flatNumber: flat.flat_number,
                fullFlat: flat,
              });
              await flatsService.deleteFlat(flatIdStr);
              console.log('✅ Flat deleted successfully');
              loadFlats();
              Alert.alert('Success', 'Flat deleted successfully');
            } catch (error: any) {
              console.error('❌ Error deleting flat:', error);
              console.error('Error details:', {
                message: error.message,
                code: error.code,
                status: error.status || error.response?.status,
                response: error.response?.data,
                flatId: flat.id,
              });
              
              let errorMessage = 'Failed to delete flat. Please try again.';
              
              // Handle specific error types
              if (error.code === 'FORBIDDEN' || error.status === 403) {
                errorMessage = 'Admin access required. You must be logged in as an administrator to delete flats.';
              } else if (error.code === 'NOT_FOUND' || error.status === 404) {
                errorMessage = 'Flat not found. It may have already been deleted.';
              } else if (error.code === 'CONNECTION_ERROR') {
                errorMessage = error.message || 'Cannot connect to server. Please check your connection.';
              } else if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
              } else if (error.message) {
                errorMessage = error.message;
              }
              
              Alert.alert('Error', errorMessage);
            }
          },
        },
      ],
    );
  };

  const renderFlat = ({item}: {item: Flat}) => {
    const handleEdit = () => {
      // Ensure we're passing a complete flat object with ID
      if (!item.id) {
        Alert.alert(
          'Error',
          `Flat ${item.flat_number} is missing an ID. Please refresh the list and try again.`,
        );
        return;
      }
      
      console.log('Navigating to edit flat:', {
        id: item.id,
        flatNumber: item.flat_number,
        hasAllFields: !!(item.id && item.flat_number && item.owner_name),
      });
      
      navigation.navigate('AddEditFlat', {
        flat: {
          ...item, // Spread to ensure all fields are included
          id: item.id, // Explicitly include ID
        },
      });
    };

    return (
      <View style={styles.flatCard}>
        <View style={styles.flatHeader}>
          <View style={styles.flatNumberBadge}>
            <Text style={styles.flatNumberText}>{item.flat_number}</Text>
          </View>
          <View style={styles.flatActions}>
            <TouchableOpacity
              onPress={handleEdit}
              style={styles.actionButton}
              activeOpacity={0.7}>
              <Icon name="pencil" size={24} color="#007AFF" />
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => handleDelete(item)}
              style={styles.actionButton}
              activeOpacity={0.7}>
              <Icon name="trash" size={24} color="#F44336" />
            </TouchableOpacity>
          </View>
      </View>

      <View style={styles.flatDetails}>
        <View style={styles.detailRow}>
          <Icon name="person-outline" size={18} color="#007AFF" />
          <Text style={styles.detailLabel}>Owner:</Text>
          <Text style={styles.detailValue}>{item.owner_name}</Text>
        </View>

        <View style={styles.detailRow}>
          <Icon name="expand-outline" size={18} color="#007AFF" />
          <Text style={styles.detailLabel}>Area:</Text>
          <Text style={styles.detailValue}>{item.area_sqft} sq ft</Text>
        </View>

        <View style={styles.detailRow}>
          <Icon name="people-outline" size={18} color="#007AFF" />
          <Text style={styles.detailLabel}>Occupants:</Text>
          <Text style={styles.detailValue}>{item.occupants}</Text>
        </View>

        {item.owner_email && (
          <View style={styles.detailRow}>
            <Icon name="mail-outline" size={18} color="#007AFF" />
            <Text style={styles.detailLabel}>Email:</Text>
            <Text style={styles.detailValue}>{item.owner_email}</Text>
          </View>
        )}

        {item.owner_phone && (
          <View style={styles.detailRow}>
            <Icon name="call-outline" size={18} color="#007AFF" />
            <Text style={styles.detailLabel}>Phone:</Text>
            <Text style={styles.detailValue}>{item.owner_phone}</Text>
          </View>
        )}
      </View>
    </View>
    );
  };

  const totalArea = flats.reduce((sum, f) => sum + f.area_sqft, 0);
  const totalOccupants = flats.reduce((sum, f) => sum + f.occupants, 0);

  return (
    <View style={styles.container}>
      <View style={styles.summaryCard}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryNumber}>{flats.length}</Text>
          <Text style={styles.summaryLabel}>Total Flats</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryNumber}>{totalArea.toFixed(0)}</Text>
          <Text style={styles.summaryLabel}>Total Area (sq ft)</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryNumber}>{totalOccupants}</Text>
          <Text style={styles.summaryLabel}>Total Occupants</Text>
        </View>
      </View>

      {loading && flats.length === 0 ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading flats...</Text>
        </View>
      ) : (
        <FlatList
          data={flats}
          renderItem={renderFlat}
          keyExtractor={item => item.id || item.flat_number || String(item._id)}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl refreshing={loading} onRefresh={loadFlats} />
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Icon name="home-outline" size={60} color="#CCC" />
              <Text style={styles.emptyStateText}>No flats added yet</Text>
              <Text style={styles.emptyStateSubtext}>
                Add flats to start generating bills
              </Text>
            </View>
          }
        />
      )}

      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('AddEditFlat')}
        activeOpacity={0.8}>
        <Icon name="add" size={32} color="#FFF" />
      </TouchableOpacity>
    </View>
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
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  summaryCard: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    margin: 15,
    padding: 15,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    textAlign: 'center',
  },
  listContainer: {
    padding: 15,
  },
  flatCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 15,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  flatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  flatNumberBadge: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  flatNumberText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  flatActions: {
    flexDirection: 'row',
  },
  actionButton: {
    padding: 10,
    marginLeft: 12,
    borderRadius: 8,
    backgroundColor: '#F5F5F5',
  },
  flatDetails: {
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
    minWidth: 80,
  },
  detailValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
    flex: 1,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 60,
  },
  emptyStateText: {
    fontSize: 18,
    color: '#999',
    marginTop: 15,
    fontWeight: '600',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#BBB',
    marginTop: 8,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.3,
    shadowRadius: 5,
  },
});

export default FlatsListScreen;
