import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

// Configuration
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://cfc6a4a4-df9e-4337-8286-d6a28cb5851b-00-3ngw5jucfqdys.picard.replit.dev';

// Create axios instance
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'photovault_auth_token';

export const setAuthToken = async (token) => {
  if (token) {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    delete api.defaults.headers.common['Authorization'];
  }
};

export const getAuthToken = async () => {
  try {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
};

// Initialize token on app start
export const initializeAuth = async () => {
  const token = await getAuthToken();
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }
};

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      await setAuthToken(null);
      // Redirect to login would happen here
    }
    return Promise.reject(error);
  }
);

// API Service methods
export const apiService = {
  // Authentication
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.token) {
      await setAuthToken(response.data.token);
    }
    return response.data;
  },

  register: async (username, email, password) => {
    const response = await api.post('/auth/register', { username, email, password });
    return response.data;
  },

  logout: async () => {
    await setAuthToken(null);
  },

  // User profile
  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  // Photos
  uploadPhoto: async (formData) => {
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getPhotos: async (page = 1, limit = 20) => {
    const response = await api.get(`/gallery/photos?page=${page}&limit=${limit}`);
    return response.data;
  },

  getPhoto: async (photoId) => {
    const response = await api.get(`/photo/${photoId}`);
    return response.data;
  },

  deletePhoto: async (photoId) => {
    const response = await api.delete(`/photo/${photoId}`);
    return response.data;
  },

  // Camera uploads
  uploadCameraPhoto: async (imageUri, metadata = {}) => {
    const formData = new FormData();
    formData.append('photo', {
      uri: imageUri,
      type: 'image/jpeg',
      name: `camera_capture_${Date.now()}.jpg`,
    });
    
    // Add metadata
    Object.keys(metadata).forEach(key => {
      formData.append(key, metadata[key]);
    });

    return await apiService.uploadPhoto(formData);
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/api');
    return response.data;
  },
};

export default api;