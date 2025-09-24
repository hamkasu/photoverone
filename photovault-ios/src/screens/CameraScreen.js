import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  SafeAreaView,
  Dimensions,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import * as ImageManipulator from 'expo-image-manipulator';
import { apiService } from '../services/api';

const { width, height } = Dimensions.get('window');

export default function CameraScreen({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState('back');
  const [flash, setFlash] = useState('off');
  const [isUploading, setIsUploading] = useState(false);
  const cameraRef = useRef(null);

  useEffect(() => {
    requestPermission();
  }, []);

  if (!permission) {
    return <View style={styles.container} />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          PhotoVault needs access to your camera to take photos
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const toggleCameraFacing = () => {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  };

  const toggleFlash = () => {
    setFlash(current => {
      switch (current) {
        case 'off': return 'on';
        case 'on': return 'auto';
        case 'auto': return 'off';
        default: return 'off';
      }
    });
  };

  const getFlashIcon = () => {
    switch (flash) {
      case 'on': return 'flash';
      case 'auto': return 'flash-auto';
      default: return 'flash-off';
    }
  };

  const takePicture = async () => {
    if (!cameraRef.current || isUploading) return;

    try {
      setIsUploading(true);
      
      // Take photo
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: false,
      });

      // Compress and optimize image
      const compressedImage = await ImageManipulator.manipulateAsync(
        photo.uri,
        [{ resize: { width: 2048 } }], // Resize to max 2048px width
        {
          compress: 0.8,
          format: ImageManipulator.SaveFormat.JPEG,
        }
      );

      // Upload to PhotoVault backend
      const metadata = {
        source: 'camera',
        facing: facing,
        timestamp: new Date().toISOString(),
      };

      await apiService.uploadCameraPhoto(compressedImage.uri, metadata);

      Alert.alert(
        'Success',
        'Photo uploaded successfully!',
        [
          {
            text: 'Take Another',
            style: 'default',
          },
          {
            text: 'View Gallery',
            style: 'default',
            onPress: () => navigation.navigate('Gallery'),
          },
        ]
      );

    } catch (error) {
      console.error('Error taking/uploading photo:', error);
      Alert.alert(
        'Error',
        'Failed to upload photo. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsUploading(false);
    }
  };

  const goBack = () => {
    navigation.goBack();
  };

  return (
    <SafeAreaView style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        facing={facing}
        flash={flash}
        autofocus="on"
      >
        {/* Top Controls */}
        <View style={styles.topControls}>
          <TouchableOpacity style={styles.controlButton} onPress={goBack}>
            <Ionicons name="close" size={30} color="#fff" />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.controlButton} onPress={toggleFlash}>
            <Ionicons name={getFlashIcon()} size={30} color="#fff" />
          </TouchableOpacity>
        </View>

        {/* Bottom Controls */}
        <View style={styles.bottomControls}>
          <View style={styles.controlsRow}>
            {/* Gallery Button */}
            <TouchableOpacity 
              style={styles.sideButton}
              onPress={() => navigation.navigate('Gallery')}
            >
              <Ionicons name="images" size={30} color="#fff" />
            </TouchableOpacity>

            {/* Capture Button */}
            <TouchableOpacity
              style={[
                styles.captureButton,
                isUploading && styles.captureButtonDisabled
              ]}
              onPress={takePicture}
              disabled={isUploading}
            >
              <View style={styles.captureButtonInner}>
                {isUploading ? (
                  <Text style={styles.uploadingText}>•••</Text>
                ) : (
                  <View style={styles.captureButtonCircle} />
                )}
              </View>
            </TouchableOpacity>

            {/* Flip Camera Button */}
            <TouchableOpacity 
              style={styles.sideButton}
              onPress={toggleCameraFacing}
            >
              <Ionicons name="camera-reverse" size={30} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </CameraView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    padding: 20,
  },
  permissionText: {
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 30,
  },
  permissionButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 15,
    paddingHorizontal: 30,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  camera: {
    flex: 1,
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingHorizontal: 20,
  },
  controlButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  bottomControls: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingBottom: 50,
    paddingHorizontal: 20,
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sideButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureButtonDisabled: {
    opacity: 0.5,
  },
  captureButtonInner: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureButtonCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#007AFF',
  },
  uploadingText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
});