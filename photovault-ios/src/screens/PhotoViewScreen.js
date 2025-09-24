import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Dimensions,
  ScrollView,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';
import { apiService } from '../services/api';

const { width, height } = Dimensions.get('window');

export default function PhotoViewScreen({ route, navigation }) {
  const { photo } = route.params;
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = () => {
    Alert.alert(
      'Delete Photo',
      'Are you sure you want to delete this photo? This action cannot be undone.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: confirmDelete,
        },
      ]
    );
  };

  const confirmDelete = async () => {
    setIsDeleting(true);
    try {
      await apiService.deletePhoto(photo.id);
      Alert.alert(
        'Success',
        'Photo deleted successfully',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error) {
      console.error('Error deleting photo:', error);
      Alert.alert('Error', 'Failed to delete photo. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleShare = async () => {
    try {
      const isAvailable = await Sharing.isAvailableAsync();
      if (!isAvailable) {
        Alert.alert('Share', 'Sharing is not available on this device');
        return;
      }

      // Download the image to local storage first
      const downloadPath = `${FileSystem.documentDirectory}${photo.filename}`;
      const downloadObject = await FileSystem.downloadAsync(photo.url, downloadPath);
      
      if (downloadObject.status === 200) {
        await Sharing.shareAsync(downloadObject.uri, {
          mimeType: 'image/jpeg',
          dialogTitle: 'Share Photo',
        });
      } else {
        Alert.alert('Error', 'Failed to download photo for sharing');
      }
    } catch (error) {
      console.error('Share error:', error);
      Alert.alert('Error', 'Failed to share photo. Please try again.');
    }
  };

  const handleEdit = () => {
    // TODO: Navigate to edit screen
    Alert.alert('Edit', 'Photo editing functionality coming soon!');
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Unknown date';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} bounces={false}>
        {/* Photo */}
        <View style={styles.imageContainer}>
          <Image
            source={{ uri: photo.url }}
            style={styles.image}
            resizeMode="contain"
          />
        </View>

        {/* Photo Info */}
        <View style={styles.infoContainer}>
          <Text style={styles.filename}>{photo.filename}</Text>
          
          <View style={styles.detailsContainer}>
            <View style={styles.detailRow}>
              <Ionicons name="calendar" size={16} color="#666" />
              <Text style={styles.detailText}>
                {formatDate(photo.upload_date || photo.created_at)}
              </Text>
            </View>

            {photo.file_size && (
              <View style={styles.detailRow}>
                <Ionicons name="document" size={16} color="#666" />
                <Text style={styles.detailText}>
                  {formatFileSize(photo.file_size)}
                </Text>
              </View>
            )}

            {photo.dimensions && (
              <View style={styles.detailRow}>
                <Ionicons name="resize" size={16} color="#666" />
                <Text style={styles.detailText}>
                  {photo.dimensions}
                </Text>
              </View>
            )}

            {photo.source && (
              <View style={styles.detailRow}>
                <Ionicons name="camera" size={16} color="#666" />
                <Text style={styles.detailText}>
                  {photo.source === 'camera' ? 'Camera' : 'Upload'}
                </Text>
              </View>
            )}
          </View>

          {/* Action Buttons */}
          <View style={styles.actionsContainer}>
            <TouchableOpacity style={styles.actionButton} onPress={handleEdit}>
              <Ionicons name="create" size={24} color="#007AFF" />
              <Text style={styles.actionButtonText}>Edit</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
              <Ionicons name="share" size={24} color="#007AFF" />
              <Text style={styles.actionButtonText}>Share</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.actionButton, isDeleting && styles.actionButtonDisabled]} 
              onPress={handleDelete}
              disabled={isDeleting}
            >
              <Ionicons 
                name="trash" 
                size={24} 
                color={isDeleting ? "#666" : "#FF3B30"} 
              />
              <Text style={[
                styles.actionButtonText, 
                { color: isDeleting ? "#666" : "#FF3B30" }
              ]}>
                {isDeleting ? 'Deleting...' : 'Delete'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  scrollView: {
    flex: 1,
  },
  imageContainer: {
    width: width,
    height: height * 0.6,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: width,
    height: '100%',
  },
  infoContainer: {
    flex: 1,
    padding: 20,
  },
  filename: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  detailsContainer: {
    marginBottom: 30,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  detailText: {
    fontSize: 16,
    color: '#ccc',
    marginLeft: 10,
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  actionButton: {
    alignItems: 'center',
    padding: 10,
  },
  actionButtonDisabled: {
    opacity: 0.5,
  },
  actionButtonText: {
    fontSize: 12,
    color: '#007AFF',
    marginTop: 5,
  },
});