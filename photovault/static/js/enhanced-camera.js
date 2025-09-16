/**
 * PhotoVault Enhanced Camera Handler
 * Provides full-screen camera functionality with landscape mode and tap-to-capture
 */
class PhotoVaultEnhancedCamera {
    constructor() {
        console.log('🚀 Initializing PhotoVault Enhanced Camera System');
        
        // DOM Elements
        this.elements = this.initializeElements();
        
        // Camera properties
        this.availableCameras = [];
        this.currentStream = null;
        this.isFullscreen = false;
        this.isCapturing = false;
        this.orientationLocked = false;
        
        // Configuration
        this.config = {
            maxFileSize: 16 * 1024 * 1024, // 16MB
            videoConstraints: {
                width: { ideal: 1920, max: 3840 },
                height: { ideal: 1080, max: 2160 },
                frameRate: { ideal: 30, max: 60 }
            },
            captureQuality: 0.92,
            supportedFormats: ['image/jpeg', 'image/png', 'image/webp']
        };
        
        // Initialize system
        this.initialize();
    }

    initializeElements() {
        const elements = {};
        
        // Camera controls
        elements.cameraSelect = document.getElementById('camera-select');
        elements.cameraSelectFullscreen = document.getElementById('camera-select-fullscreen');
        elements.startCameraBtn = document.getElementById('start-camera-btn');
        elements.closeCameraBtn = document.getElementById('close-camera');
        
        // Video and canvas
        elements.cameraVideo = document.getElementById('camera-video');
        elements.photoCanvas = document.getElementById('photo-canvas');
        elements.cameraFullscreen = document.getElementById('camera-fullscreen');
        
        // UI feedback
        elements.captureIndicator = document.getElementById('capture-indicator');
        elements.cameraWarning = document.getElementById('camera-warning');
        elements.uploadProgress = document.getElementById('upload-progress');
        elements.uploadResults = document.getElementById('upload-results');
        
        // File upload
        elements.fileInput = document.getElementById('file-input');
        elements.uploadArea = document.querySelector('.upload-area');
        
        return elements;
    }

    async initialize() {
        try {
            // Check for required APIs
            if (!this.checkAPISupport()) {
                throw new Error('Required APIs not supported');
            }
            
            // Initialize camera system
            await this.initializeCamera();
            
            // Setup all event listeners
            this.setupEventListeners();
            
            // Setup file upload
            this.setupFileUpload();
            
            console.log('✅ PhotoVault Enhanced Camera initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize camera system:', error);
            this.showError('Failed to initialize camera system: ' + error.message);
        }
    }

    checkAPISupport() {
        const required = [
            'navigator.mediaDevices',
            'navigator.mediaDevices.getUserMedia',
            'navigator.mediaDevices.enumerateDevices'
        ];
        
        const missing = required.filter(api => {
            const keys = api.split('.');
            let obj = window;
            for (const key of keys) {
                if (!(key in obj)) return true;
                obj = obj[key];
            }
            return false;
        });
        
        if (missing.length > 0) {
            console.error('Missing required APIs:', missing);
            return false;
        }
        
        return true;
    }

    async initializeCamera() {
        try {
            console.log('🔍 Requesting camera permissions...');
            
            // Request camera permissions first
            const tempStream = await navigator.mediaDevices.getUserMedia({ 
                video: true, 
                audio: false 
            });
            
            // Stop temporary stream immediately
            tempStream.getTracks().forEach(track => track.stop());
            console.log('✅ Camera permissions granted');
            
            // Enumerate available cameras
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.availableCameras = devices.filter(device => 
                device.kind === 'videoinput' && device.deviceId
            );
            
            console.log(`📷 Found ${this.availableCameras.length} camera(s):`, 
                this.availableCameras.map(cam => cam.label || 'Unknown Camera'));
            
            if (this.availableCameras.length === 0) {
                throw new Error('No cameras found on this device');
            }
            
            // Populate camera selection dropdowns
            this.populateCameraSelects();
            
            // Enable camera functionality
            this.enableCameraButton();
            this.hideWarning();
            
        } catch (error) {
            console.error('❌ Camera initialization failed:', error);
            
            if (error.name === 'NotAllowedError') {
                this.showError('Camera access denied. Please allow camera access and refresh the page.');
            } else if (error.name === 'NotFoundError') {
                this.showError('No cameras found on this device.');
            } else {
                this.showError('Camera not available: ' + error.message);
            }
            
            throw error;
        }
    }

    populateCameraSelects() {
        const selects = [this.elements.cameraSelect, this.elements.cameraSelectFullscreen];
        
        selects.forEach(select => {
            if (!select) return;
            
            // Clear existing options
            select.innerHTML = '<option value="">Select Camera...</option>';
            
            // Add camera options
            this.availableCameras.forEach((camera, index) => {
                const option = document.createElement('option');
                option.value = camera.deviceId;
                
                // Generate user-friendly camera name
                let cameraName = this.getCameraDisplayName(camera, index);
                option.textContent = cameraName;
                
                select.appendChild(option);
            });
            
            // Auto-select first camera
            if (this.availableCameras.length > 0) {
                select.value = this.availableCameras[0].deviceId;
            }
        });
        
        console.log('📝 Camera selection dropdowns populated');
    }

    getCameraDisplayName(camera, index) {
        let name = camera.label || `Camera ${index + 1}`;
        
        // Add descriptive labels for common camera types
        if (index === 0 && !camera.label) {
            name += ' (Default)';
        }
        
        // Try to identify camera facing direction
        const label = camera.label.toLowerCase();
        if (label.includes('front') || label.includes('user')) {
            name += ' (Front)';
        } else if (label.includes('back') || label.includes('rear') || label.includes('environment')) {
            name += ' (Rear)';
        }
        
        return name;
    }

    setupEventListeners() {
        console.log('🎧 Setting up event listeners...');
        
        // Camera control buttons
        this.elements.startCameraBtn?.addEventListener('click', () => {
            this.enterFullScreenCamera();
        });
        
        this.elements.closeCameraBtn?.addEventListener('click', () => {
            this.exitFullScreenCamera();
        });
        
        // Camera selection synchronization
        this.elements.cameraSelect?.addEventListener('change', (e) => {
            if (this.elements.cameraSelectFullscreen) {
                this.elements.cameraSelectFullscreen.value = e.target.value;
            }
            if (this.isFullscreen) {
                this.switchCamera(e.target.value);
            }
        });
        
        this.elements.cameraSelectFullscreen?.addEventListener('change', (e) => {
            if (this.elements.cameraSelect) {
                this.elements.cameraSelect.value = e.target.value;
            }
            if (this.isFullscreen) {
                this.switchCamera(e.target.value);
            }
        });
        
        // Video tap/click to capture
        this.elements.cameraVideo?.addEventListener('click', (e) => {
            if (this.isFullscreen && !this.isCapturing) {
                this.capturePhoto();
            }
        });
        
        // Prevent context menu on video
        this.elements.cameraVideo?.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.isFullscreen) {
                switch (e.key) {
                    case 'Escape':
                        this.exitFullScreenCamera();
                        break;
                    case ' ':
                    case 'Enter':
                        e.preventDefault();
                        if (!this.isCapturing) {
                            this.capturePhoto();
                        }
                        break;
                }
            }
        });
        
        // Screen orientation change
        if (screen.orientation) {
            screen.orientation.addEventListener('change', () => {
                if (this.isFullscreen) {
                    console.log('📱 Orientation changed:', screen.orientation.type);
                    this.handleOrientationChange();
                }
            });
        }
        
        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isFullscreen) {
                console.log('📱 App hidden while camera active - pausing');
                this.pauseCamera();
            } else if (!document.hidden && this.isFullscreen) {
                console.log('📱 App visible - resuming camera');
                this.resumeCamera();
            }
        });
        
        // Window resize handler
        window.addEventListener('resize', () => {
            if (this.isFullscreen) {
                this.handleWindowResize();
            }
        });
    }

    async enterFullScreenCamera() {
        try {
            const selectedCameraId = this.elements.cameraSelect?.value;
            if (!selectedCameraId) {
                this.showError('Please select a camera first');
                return;
            }

            console.log('📱 Entering full screen camera mode...');
            this.showLoadingIndicator();
            
            // Lock to landscape orientation
            await this.lockOrientation();
            
            // Start camera stream
            await this.startCamera(selectedCameraId);
            
            // Enter full screen mode
            this.elements.cameraFullscreen?.classList.add('active');
            this.isFullscreen = true;
            
            // Disable page scrolling
            document.body.style.overflow = 'hidden';
            
            // Hide loading indicator
            this.hideLoadingIndicator();
            
            console.log('✅ Full screen camera mode activated');
            
            // Show success message briefly
            this.showCaptureSuccess('Camera ready - tap screen to capture!', 2000);
            
        } catch (error) {
            console.error('❌ Failed to enter full screen camera:', error);
            this.hideLoadingIndicator();
            this.showError('Failed to start camera: ' + error.message);
        }
    }

    async exitFullScreenCamera() {
        console.log('📱 Exiting full screen camera mode...');
        
        try {
            // Stop camera stream
            if (this.currentStream) {
                this.currentStream.getTracks().forEach(track => {
                    track.stop();
                    console.log('🔇 Stopped camera track:', track.kind);
                });
                this.currentStream = null;
            }
            
            // Exit full screen
            this.elements.cameraFullscreen?.classList.remove('active');
            this.isFullscreen = false;
            
            // Restore page scrolling
            document.body.style.overflow = '';
            
            // Unlock orientation
            await this.unlockOrientation();
            
            console.log('✅ Full screen camera mode deactivated');
            
        } catch (error) {
            console.error('❌ Error exiting full screen camera:', error);
        }
    }

    async lockOrientation() {
        if (!screen.orientation?.lock) {
            console.log('⚠️ Screen orientation lock not supported');
            return;
        }
        
        try {
            await screen.orientation.lock('landscape');
            this.orientationLocked = true;
            console.log('🔒 Locked to landscape orientation');
        } catch (error) {
            console.log('⚠️ Could not lock orientation:', error.message);
            // Not critical, continue without orientation lock
        }
    }

    async unlockOrientation() {
        if (!screen.orientation?.unlock || !this.orientationLocked) {
            return;
        }
        
        try {
            screen.orientation.unlock();
            this.orientationLocked = false;
            console.log('🔓 Unlocked screen orientation');
        } catch (error) {
            console.log('⚠️ Could not unlock orientation:', error.message);
        }
    }

    async startCamera(deviceId) {
        try {
            console.log('🎥 Starting camera:', deviceId);
            
            const constraints = {
                video: {
                    deviceId: { exact: deviceId },
                    ...this.config.videoConstraints,
                    facingMode: this.getCameraFacingMode(deviceId)
                },
                audio: false
            };
            
            this.currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            if (this.elements.cameraVideo) {
                this.elements.cameraVideo.srcObject = this.currentStream;
                
                // Wait for video to be ready
                await new Promise((resolve, reject) => {
                    this.elements.cameraVideo.addEventListener('loadedmetadata', resolve, { once: true });
                    this.elements.cameraVideo.addEventListener('error', reject, { once: true });
                    
                    // Timeout after 10 seconds
                    setTimeout(() => reject(new Error('Camera load timeout')), 10000);
                });
            }
            
            const track = this.currentStream.getVideoTracks()[0];
            const settings = track.getSettings();
            
            console.log('✅ Camera started successfully:', {
                deviceId: settings.deviceId,
                resolution: `${settings.width}x${settings.height}`,
                frameRate: settings.frameRate,
                facingMode: settings.facingMode
            });
            
        } catch (error) {
            console.error('❌ Failed to start camera:', error);
            throw error;
        }
    }

    getCameraFacingMode(deviceId) {
        const camera = this.availableCameras.find(cam => cam.deviceId === deviceId);
        if (!camera) return 'environment';
        
        const label = camera.label.toLowerCase();
        if (label.includes('front') || label.includes('user')) {
            return 'user';
        } else if (label.includes('back') || label.includes('rear') || label.includes('environment')) {
            return 'environment';
        }
        
        return 'environment'; // Default to rear camera
    }

    async switchCamera(deviceId) {
        if (!deviceId || !this.isFullscreen) return;
        
        console.log('🔄 Switching camera to:', deviceId);
        
        try {
            // Stop current stream
            if (this.currentStream) {
                this.currentStream.getTracks().forEach(track => track.stop());
            }
            
            // Start new camera
            await this.startCamera(deviceId);
            
        } catch (error) {
            console.error('❌ Failed to switch camera:', error);
            this.showError('Failed to switch camera: ' + error.message);
        }
    }

    async capturePhoto() {
        if (!this.currentStream || !this.isFullscreen || this.isCapturing) return;
        
        this.isCapturing = true;
        console.log('📸 Capturing photo...');
        
        try {
            // Visual feedback
            this.showCaptureFlash();
            this.triggerHapticFeedback();
            
            // Get video element
            const video = this.elements.cameraVideo;
            const canvas = this.elements.photoCanvas;
            const ctx = canvas.getContext('2d');
            
            // Wait for video to be properly loaded
            if (video.videoWidth === 0 || video.videoHeight === 0) {
                throw new Error('Video not ready');
            }
            
            // Set canvas dimensions to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            console.log('📐 Capturing at resolution:', canvas.width, 'x', canvas.height);
            
            // Draw video frame to canvas
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to blob
            const blob = await new Promise((resolve, reject) => {
                canvas.toBlob(resolve, 'image/jpeg', this.config.captureQuality);
                setTimeout(() => reject(new Error('Capture timeout')), 5000);
            });
            
            if (!blob) {
                throw new Error('Failed to create image blob');
            }
            
            // Create file
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            const filename = `photovault-${timestamp}.jpg`;
            const file = new File([blob], filename, { type: 'image/jpeg' });
            
            const sizeKB = (blob.size / 1024).toFixed(1);
            const sizeMB = (blob.size / 1024 / 1024).toFixed(2);
            
            console.log(`📷 Photo captured: ${filename} (${sizeMB}MB)`);
            
            // Upload the photo
            const uploadSuccess = await this.uploadFiles([file]);
            
            if (uploadSuccess) {
                this.showCaptureSuccess('Photo captured and uploaded successfully!');
                
                // Auto-exit after successful capture (optional)
                setTimeout(() => {
                    this.exitFullScreenCamera();
                }, 1500);
            } else {
                throw new Error('Upload failed');
            }
            
        } catch (error) {
            console.error('❌ Failed to capture photo:', error);
            this.showError('Failed to capture photo: ' + error.message);
        } finally {
            this.isCapturing = false;
        }
    }

    showCaptureFlash() {
        if (!this.elements.captureIndicator) return;
        
        this.elements.captureIndicator.classList.add('flash');
        setTimeout(() => {
            this.elements.captureIndicator.classList.remove('flash');
        }, 200);
    }

    triggerHapticFeedback() {
        if ('vibrate' in navigator) {
            navigator.vibrate([50, 30, 50]); // Short-pause-short vibration pattern
        }
    }

    showCaptureSuccess(message, duration = 1500) {
        // Remove existing success message
        const existing = document.querySelector('.capture-success');
        if (existing) {
            existing.remove();
        }
        
        // Create new success message
        const successElement = document.createElement('div');
        successElement.className = 'capture-success';
        successElement.innerHTML = `
            <i class="fas fa-check-circle"></i>
            ${message}
        `;
        
        document.body.appendChild(successElement);
        
        // Remove after duration
        setTimeout(() => {
            if (successElement.parentNode) {
                successElement.parentNode.removeChild(successElement);
            }
        }, duration);
    }

    setupFileUpload() {
        console.log('📁 Setting up file upload...');
        
        if (!this.elements.fileInput || !this.elements.uploadArea) {
            console.log('⚠️ File upload elements not found');
            return;
        }
        
        // File input change
        this.elements.fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                this.uploadFiles(files);
            }
        });
        
        // Drag and drop
        this.elements.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.elements.uploadArea.classList.add('drag-over');
        });
        
        this.elements.uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.elements.uploadArea.classList.remove('drag-over');
        });
        
        this.elements.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.elements.uploadArea.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                this.uploadFiles(files);
            }
        });
    }

    async uploadFiles(files) {
        console.log(`📤 Uploading ${files.length} file(s)...`);
        
        const progressContainer = this.elements.uploadProgress;
        const progressBar = progressContainer?.querySelector('.progress-bar');
        const statusDiv = document.getElementById('upload-status');
        const resultsDiv = this.elements.uploadResults;
        
        if (progressContainer) progressContainer.style.display = 'block';
        if (progressBar) progressBar.style.width = '0%';
        if (statusDiv) statusDiv.textContent = 'Preparing upload...';
        
        let successCount = 0;
        const totalFiles = files.length;
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            try {
                // Validate file
                if (!this.validateFile(file)) {
                    console.log(`⚠️ Skipping invalid file: ${file.name}`);
                    continue;
                }
                
                if (statusDiv) {
                    statusDiv.textContent = `Uploading ${file.name}... (${i + 1}/${totalFiles})`;
                }
                
                // Upload file
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    successCount++;
                    console.log(`✅ Upload successful: ${file.name}`);
                } else {
                    console.error(`❌ Upload failed: ${file.name} - ${result.error}`);
                }
                
                // Update progress
                const progress = ((i + 1) / totalFiles) * 100;
                if (progressBar) progressBar.style.width = `${progress}%`;
                
            } catch (error) {
                console.error(`❌ Upload error: ${file.name}`, error);
            }
        }
        
        // Show final results
        const message = `Upload complete: ${successCount}/${totalFiles} files uploaded successfully`;
        if (statusDiv) statusDiv.textContent = message;
        
        if (successCount > 0 && resultsDiv) {
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    Successfully uploaded ${successCount} file(s)!
                </div>
            `;
            
            // Reset file input
            if (this.elements.fileInput) {
                this.elements.fileInput.value = '';
            }
        }
        
        // Hide progress after delay
        setTimeout(() => {
            if (progressContainer) progressContainer.style.display = 'none';
        }, 3000);
        
        return successCount > 0;
    }

    validateFile(file) {
        // Check file type
        if (!this.config.supportedFormats.includes(file.type) && 
            !file.type.startsWith('image/')) {
            console.warn(`Unsupported file type: ${file.type}`);
            return false;
        }
        
        // Check file size
        if (file.size > this.config.maxFileSize) {
            const maxSizeMB = (this.config.maxFileSize / 1024 / 1024).toFixed(1);
            const fileSizeMB = (file.size / 1024 / 1024).toFixed(1);
            console.warn(`File too large: ${fileSizeMB}MB (max: ${maxSizeMB}MB)`);
            return false;
        }
        
        return true;
    }

    // UI Helper Methods
    showLoadingIndicator() {
        if (this.elements.cameraFullscreen) {
            const loading = document.createElement('div');
            loading.className = 'camera-loading';
            loading.innerHTML = `
                <div class="spinner"></div>
                <div>Starting camera...</div>
            `;
            this.elements.cameraFullscreen.appendChild(loading);
        }
    }

    hideLoadingIndicator() {
        const loading = document.querySelector('.camera-loading');
        if (loading) {
            loading.remove();
        }
    }

    showError(message) {
        if (this.elements.cameraWarning) {
            this.elements.cameraWarning.textContent = message;
            this.elements.cameraWarning.style.display = 'block';
        }
        console.error('UI Error:', message);
    }

    hideWarning() {
        if (this.elements.cameraWarning) {
            this.elements.cameraWarning.style.display = 'none';
        }
    }

    enableCameraButton() {
        if (this.elements.startCameraBtn) {
            this.elements.startCameraBtn.disabled = false;
            this.elements.startCameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Start Full Screen Camera';
        }
    }

    // Event handlers for lifecycle events
    handleOrientationChange() {
        console.log('📱 Handling orientation change...');
        // Could add specific orientation handling logic here
    }

    handleWindowResize() {
        console.log('📱 Handling window resize...');
        // Could add specific resize handling logic here
    }

    pauseCamera() {
        if (this.currentStream) {
            this.currentStream.getVideoTracks().forEach(track => {
                track.enabled = false;
            });
        }
    }

    resumeCamera() {
        if (this.currentStream) {
            this.currentStream.getVideoTracks().forEach(track => {
                track.enabled = true;
            });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.photoVaultCamera = new PhotoVaultEnhancedCamera();
});

// Export for module usage (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoVaultEnhancedCamera;
}