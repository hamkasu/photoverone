import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
  RefreshControl,
  Image,
} from 'react-native';
import { apiService } from '../services/api';

const { width } = Dimensions.get('window');
const PHOTO_SIZE = (width - 30) / 3; // 3 photos per row with margins

export default function GalleryScreen({ navigation }) {
  const [photos, setPhotos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadPhotos();
  }, []);

  const loadPhotos = async (pageNumber = 1, refresh = false) => {
    try {
      if (refresh) {
        setIsRefreshing(true);
      } else if (pageNumber === 1) {
        setIsLoading(true);
      }

      const response = await apiService.getPhotos(pageNumber, 20);
      
      if (refresh || pageNumber === 1) {
        setPhotos(response.photos || []);
      } else {
        setPhotos(prev => [...prev, ...(response.photos || [])]);
      }

      setHasMore(response.has_more || false);
      setPage(pageNumber);

    } catch (error) {
      console.error('Error loading photos:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const onRefresh = useCallback(() => {
    loadPhotos(1, true);
  }, []);

  const loadMore = () => {
    if (hasMore && !isLoading) {
      loadPhotos(page + 1);
    }
  };

  const openPhoto = (photo) => {
    navigation.navigate('PhotoView', { photo });
  };

  const openCamera = () => {
    navigation.navigate('Camera');
  };

  const renderPhoto = ({ item }) => (
    <TouchableOpacity
      style={styles.photoContainer}
      onPress={() => openPhoto(item)}
    >
      <Image
        source={{ uri: item.thumbnail_url || item.url }}
        style={styles.photo}
        resizeMode="cover"
      />
    </TouchableOpacity>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyTitle}>No Photos Yet</Text>
      <Text style={styles.emptyDescription}>
        Start building your photo collection by taking some pictures!
      </Text>
      <TouchableOpacity style={styles.cameraButton} onPress={openCamera}>
        <Text style={styles.cameraButtonText}>Open Camera</Text>
      </TouchableOpacity>
    </View>
  );

  const renderFooter = () => {
    if (!hasMore) return null;
    
    return (
      <View style={styles.footer}>
        <ActivityIndicator size="small" color="#007AFF" />
      </View>
    );
  };

  if (isLoading && photos.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading photos...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={photos}
        renderItem={renderPhoto}
        keyExtractor={(item) => item.id.toString()}
        numColumns={3}
        contentContainerStyle={photos.length === 0 ? styles.emptyList : styles.list}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={onRefresh}
            tintColor="#007AFF"
          />
        }
        onEndReached={loadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={renderEmptyState}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 10,
  },
  list: {
    padding: 5,
  },
  emptyList: {
    flexGrow: 1,
  },
  photoContainer: {
    flex: 1,
    margin: 2,
    aspectRatio: 1,
  },
  photo: {
    width: '100%',
    height: '100%',
    borderRadius: 4,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  emptyDescription: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
  },
  cameraButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 15,
    paddingHorizontal: 30,
  },
  cameraButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
});