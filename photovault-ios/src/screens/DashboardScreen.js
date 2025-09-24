import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { apiService } from '../services/api';

export default function DashboardScreen({ navigation }) {
  const [isUploading, setIsUploading] = useState(false);
  const menuItems = [
    {
      id: 'camera',
      title: 'Camera',
      description: 'Capture new photos',
      icon: 'camera',
      color: '#007AFF',
      onPress: () => navigation.navigate('Camera'),
    },
    {
      id: 'gallery',
      title: 'Gallery',
      description: 'View your photos',
      icon: 'images',
      color: '#34C759',
      onPress: () => navigation.navigate('Gallery'),
    },
    {
      id: 'upload',
      title: 'Upload',
      description: 'Upload from device',
      icon: 'cloud-upload',
      color: '#FF9500',
      onPress: () => handleUploadFromDevice(),
    },
    {
      id: 'enhance',
      title: 'Enhancement',
      description: 'Improve photo quality',
      icon: 'sparkles',
      color: '#AF52DE',
      onPress: () => {
        // TODO: Navigate to enhancement screen
        console.log('Enhancement');
      },
    },
  ];

  const handleUploadFromDevice = async () => {
    try {
      // Request permission
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (!permissionResult.granted) {
        Alert.alert(
          'Permission Required',
          'PhotoVault needs access to your photo library to upload photos.'
        );
        return;
      }

      // Launch image picker
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
        allowsMultipleSelection: false,
      });

      if (result.canceled || !result.assets || result.assets.length === 0) {
        return;
      }

      setIsUploading(true);
      
      const asset = result.assets[0];
      
      // Upload the photo
      const metadata = {
        source: 'gallery',
        timestamp: new Date().toISOString(),
      };

      await apiService.uploadCameraPhoto(asset.uri, metadata);

      Alert.alert(
        'Success',
        'Photo uploaded successfully!',
        [
          {
            text: 'View Gallery',
            onPress: () => navigation.navigate('Gallery'),
          },
          {
            text: 'OK',
            style: 'cancel',
          },
        ]
      );

    } catch (error) {
      console.error('Upload error:', error);
      Alert.alert(
        'Upload Failed', 
        'Failed to upload photo. Please try again.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const renderMenuItem = (item) => (
    <TouchableOpacity
      key={item.id}
      style={[
        styles.menuItem, 
        isUploading && item.id === 'upload' && styles.menuItemDisabled
      ]}
      onPress={item.onPress}
      disabled={isUploading && item.id === 'upload'}
    >
      <View style={[styles.iconContainer, { backgroundColor: item.color }]}>
        <Ionicons name={item.icon} size={30} color="#fff" />
      </View>
      <View style={styles.menuContent}>
        <Text style={styles.menuTitle}>
          {isUploading && item.id === 'upload' ? 'Uploading...' : item.title}
        </Text>
        <Text style={styles.menuDescription}>{item.description}</Text>
      </View>
      <Ionicons name="chevron-forward" size={20} color="#666" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.welcomeText}>Welcome to PhotoVault</Text>
          <Text style={styles.subtitleText}>Professional Photo Management</Text>
        </View>

        <View style={styles.menuContainer}>
          {menuItems.map(renderMenuItem)}
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>0</Text>
            <Text style={styles.statLabel}>Photos</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>0</Text>
            <Text style={styles.statLabel}>Albums</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>0 MB</Text>
            <Text style={styles.statLabel}>Storage</Text>
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
  header: {
    padding: 20,
    alignItems: 'center',
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  subtitleText: {
    fontSize: 16,
    color: '#666',
  },
  menuContainer: {
    padding: 20,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  menuItemDisabled: {
    opacity: 0.6,
  },
  iconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  menuContent: {
    flex: 1,
  },
  menuTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 2,
  },
  menuDescription: {
    fontSize: 14,
    color: '#666',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 20,
    marginTop: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
  },
});