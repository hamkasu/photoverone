/**
 * PhotoVault Upload & Camera Handler - Clean Implementation
 * Fixes all conflicting implementations and provides unified functionality
 */

class PhotoVaultUploader {
    constructor() {
        // State management
        this.selectedFiles = [];
        this.capturedPhotos = [];
        this.isUploading = false;
        this.currentStream = null;
        this.availableCameras = [];
        this.maxFileSize = 16 * 1024 * 1024; // 16MB
        this.allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        
        // Smart camera features
        this.openCVReady = false;
        this.edgeDetectionEnabled = true;
        this.perspectiveCorrectionEnabled = true;
        this.detectionInterval = null;
        this.lastDetectedCorners = null;
        
        // Grid lines feature
        this.gridLinesEnabled = false;
        
        // Focus confirmation feature  
        this.focusConfirmationEnabled = true;
        this.isFocused = false;
        this.focusThreshold = 100; // Laplacian variance threshold for focus detection
        
        // Motion detection and stability
        this.motionDetectionEnabled = true;
        this.stabilityIndicatorEnabled = true;
        this.isStable = false;
        this.hasMotion = false;
        this.lastFrameData = null;
        this.motionThreshold = 5000; // Pixel difference threshold for motion detection
        this.stabilityFrames = 0;
        this.stabilityRequiredFrames = 10; // Frames of stability needed for "steady" status
        
        // Camera adjustments
        this.cameraBrightness = 100;
        this.cameraContrast = 100;
        this.cameraSaturation = 100;
        
        this.init();
    }
    
    init() {
        console.log('PhotoVault Uploader: Initializing...');
        this.bindEvents();
        this.initializeCamera().catch(err => {
            console.warn('Camera initialization failed:', err);
        });
    }
    
    bindEvents() {
        // File input events
        const fileInput = document.getElementById('file');
        const uploadForm = document.getElementById('uploadForm');
        const uploadArea = document.getElementById('uploadArea');
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        }
        
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        if (uploadArea) {
            // Click to select files - but avoid triggering on buttons or interactive elements
            uploadArea.addEventListener('click', (e) => {
                // Don't trigger file input if clicking on buttons, interactive elements, or thumbnails
                if (e.target.tagName === 'BUTTON' || 
                    e.target.closest('button') || 
                    e.target.closest('.btn') ||
                    e.target.closest('#filePreviews') ||
                    e.target === fileInput) {
                    return;
                }
                fileInput?.click();
            });
            
            // Drag and drop
            this.setupDragAndDrop(uploadArea);
        }
        
        // Camera events
        this.bindCameraEvents();
    }
    
    bindCameraEvents() {
        const startCameraBtn = document.getElementById('startCameraBtn');
        const captureBtn = document.getElementById('captureBtn');
        const cameraSelect = document.getElementById('cameraSelect');
        
        if (startCameraBtn) {
            startCameraBtn.addEventListener('click', () => this.startCamera());
        }
        
        if (captureBtn) {
            captureBtn.addEventListener('click', () => this.capturePhoto());
        }
        
        if (cameraSelect) {
            cameraSelect.addEventListener('change', () => this.onCameraSelected());
        }
        
        // Smart camera controls
        const autoDetectEdges = document.getElementById('autoDetectEdges');
        const perspectiveCorrection = document.getElementById('perspectiveCorrection');
        const showGridLines = document.getElementById('showGridLines');
        
        if (autoDetectEdges) {
            autoDetectEdges.addEventListener('change', (e) => {
                this.edgeDetectionEnabled = e.target.checked;
                if (!this.edgeDetectionEnabled) {
                    this.clearOverlay();
                }
            });
        }
        
        if (perspectiveCorrection) {
            perspectiveCorrection.addEventListener('change', (e) => {
                this.perspectiveCorrectionEnabled = e.target.checked;
            });
        }
        
        if (showGridLines) {
            showGridLines.addEventListener('change', (e) => {
                this.gridLinesEnabled = e.target.checked;
                this.toggleGridLines();
            });
        }
        
        // Camera adjustment controls
        const cameraBrightness = document.getElementById('cameraBrightness');
        const cameraContrast = document.getElementById('cameraContrast');
        const cameraSaturation = document.getElementById('cameraSaturation');
        const resetCameraAdjustments = document.getElementById('resetCameraAdjustments');
        
        if (cameraBrightness) {
            cameraBrightness.addEventListener('input', (e) => {
                this.cameraBrightness = parseInt(e.target.value);
                this.updateVideoFilters();
                this.updateBrightnessDisplay(this.cameraBrightness);
            });
        }
        
        if (cameraContrast) {
            cameraContrast.addEventListener('input', (e) => {
                this.cameraContrast = parseInt(e.target.value);
                this.updateVideoFilters();
                this.updateContrastDisplay(this.cameraContrast);
            });
        }
        
        if (cameraSaturation) {
            cameraSaturation.addEventListener('input', (e) => {
                this.cameraSaturation = parseInt(e.target.value);
                this.updateVideoFilters();
                this.updateSaturationDisplay(this.cameraSaturation);
            });
        }
        
        if (resetCameraAdjustments) {
            resetCameraAdjustments.addEventListener('click', () => {
                this.resetCameraAdjustments();
            });
        }
    }
    
    // OpenCV integration
    onOpenCVReady() {
        console.log('OpenCV.js integration activated');
        this.openCVReady = true;
    }
    
    // Smart camera functionality
    startEdgeDetection() {
        if (!this.openCVReady || !this.edgeDetectionEnabled) return;
        
        const video = document.getElementById('cameraVideo');
        const overlay = document.getElementById('overlayCanvas');
        
        if (!video || !overlay) return;
        
        // Match overlay canvas size to video
        overlay.width = video.videoWidth || video.offsetWidth;
        overlay.height = video.videoHeight || video.offsetHeight;
        
        // Start real-time detection
        this.detectionInterval = setInterval(() => {
            this.detectPhotoEdges();
        }, 200); // Detect every 200ms for smooth performance
    }
    
    detectPhotoEdges() {
        if (!this.openCVReady || !window.cv) return;
        
        const video = document.getElementById('cameraVideo');
        const overlay = document.getElementById('overlayCanvas');
        const ctx = overlay.getContext('2d');
        
        try {
            // Create canvas to capture video frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to OpenCV Mat
            const src = cv.imread(canvas);
            const gray = new cv.Mat();
            const blur = new cv.Mat();
            const edges = new cv.Mat();
            const contours = new cv.MatVector();
            const hierarchy = new cv.Mat();
            
            // Image processing pipeline for photo edge detection
            cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY);
            cv.GaussianBlur(gray, blur, new cv.Size(5, 5), 0);
            cv.Canny(blur, edges, 50, 150);
            
            // Find contours
            cv.findContours(edges, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
            
            // Clear overlay
            ctx.clearRect(0, 0, overlay.width, overlay.height);
            
            // Analyze focus quality if enabled
            if (this.focusConfirmationEnabled) {
                this.analyzeFocus(src);
            }
            
            // Analyze motion and stability if enabled
            if (this.motionDetectionEnabled || this.stabilityIndicatorEnabled) {
                this.analyzeMotionAndStability(src);
            }
            
            // Find the largest rectangular contour (likely a photo)
            let largestArea = 0;
            let bestContour = null;
            
            for (let i = 0; i < contours.size(); ++i) {
                const contour = contours.get(i);
                const area = cv.contourArea(contour);
                
                if (area > largestArea && area > 5000) { // Minimum area threshold
                    // Approximate contour to polygon
                    const approx = new cv.Mat();
                    const epsilon = 0.02 * cv.arcLength(contour, true);
                    cv.approxPolyDP(contour, approx, epsilon, true);
                    
                    // Check if it's roughly rectangular (4 corners)
                    if (approx.rows === 4) {
                        largestArea = area;
                        bestContour = approx.clone();
                    }
                    approx.delete();
                }
                contour.delete();
            }
            
            // Draw detected photo edges
            if (bestContour) {
                this.drawPhotoOverlay(ctx, bestContour, overlay.width / canvas.width, overlay.height / canvas.height);
                this.lastDetectedCorners = this.extractCorners(bestContour);
                bestContour.delete();
            }
            
            // Draw focus outline if in focus
            if (this.focusConfirmationEnabled && this.isFocused) {
                this.drawFocusOutline(ctx, overlay.width, overlay.height);
            }
            
            // Draw motion and stability indicators
            this.drawStabilityIndicators(ctx, overlay.width, overlay.height);
            
            // Cleanup
            src.delete();
            gray.delete();
            blur.delete();
            edges.delete();
            contours.delete();
            hierarchy.delete();
            
        } catch (error) {
            console.warn('Edge detection error:', error);
        }
    }
    
    drawPhotoOverlay(ctx, contour, scaleX, scaleY) {
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.fillStyle = 'rgba(0, 255, 0, 0.1)';
        
        ctx.beginPath();
        for (let i = 0; i < contour.rows; i++) {
            const point = contour.data32S.slice(i * 2, i * 2 + 2);
            const x = point[0] * scaleX;
            const y = point[1] * scaleY;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();
        ctx.stroke();
        ctx.fill();
        
        // Add corner indicators
        ctx.fillStyle = '#00ff00';
        for (let i = 0; i < contour.rows; i++) {
            const point = contour.data32S.slice(i * 2, i * 2 + 2);
            const x = point[0] * scaleX;
            const y = point[1] * scaleY;
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, 2 * Math.PI);
            ctx.fill();
        }
    }
    
    extractCorners(contour) {
        const corners = [];
        for (let i = 0; i < contour.rows; i++) {
            const point = contour.data32S.slice(i * 2, i * 2 + 2);
            corners.push({x: point[0], y: point[1]});
        }
        return corners;
    }
    
    clearOverlay() {
        const overlay = document.getElementById('overlayCanvas');
        if (overlay) {
            const ctx = overlay.getContext('2d');
            ctx.clearRect(0, 0, overlay.width, overlay.height);
        }
    }
    
    stopEdgeDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
        this.clearOverlay();
    }
    
    async initializeCamera() {
        if (!navigator.mediaDevices?.getUserMedia) {
            console.log('Camera not supported');
            this.disableCameraUI('Camera not supported in this browser');
            return;
        }
        
        try {
            // Request permission and enumerate devices
            await navigator.mediaDevices.getUserMedia({ video: true });
            await this.enumerateCameras();
        } catch (error) {
            console.error('Camera initialization error:', error);
            this.disableCameraUI('Camera permission denied');
        }
    }
    
    async enumerateCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.availableCameras = devices.filter(device => device.kind === 'videoinput');
            const cameraSelect = document.getElementById('cameraSelect');
            
            if (cameraSelect && this.availableCameras.length > 0) {
                cameraSelect.innerHTML = '<option value="">Select Camera...</option>';
                this.availableCameras.forEach((camera, index) => {
                    const option = document.createElement('option');
                    option.value = camera.deviceId;
                    option.textContent = camera.label || `Camera ${index + 1}`;
                    cameraSelect.appendChild(option);
                });
                
                // Auto-select first camera
                if (this.availableCameras.length === 1) {
                    cameraSelect.value = this.availableCameras[0].deviceId;
                }
            } else {
                this.disableCameraUI('No cameras found');
            }
        } catch (error) {
            console.error('Error enumerating cameras:', error);
            this.disableCameraUI('Could not access cameras');
        }
    }
    
    disableCameraUI(message) {
        const cameraSelect = document.getElementById('cameraSelect');
        const startCameraBtn = document.getElementById('startCameraBtn');
        
        if (cameraSelect) {
            cameraSelect.innerHTML = `<option value="">${message}</option>`;
            cameraSelect.disabled = true;
        }
        
        if (startCameraBtn) {
            startCameraBtn.disabled = true;
            startCameraBtn.textContent = message;
        }
    }
    
    onCameraSelected() {
        const startCameraBtn = document.getElementById('startCameraBtn');
        const cameraSelect = document.getElementById('cameraSelect');
        
        if (startCameraBtn && cameraSelect) {
            startCameraBtn.disabled = !cameraSelect.value;
            startCameraBtn.textContent = cameraSelect.value ? 'Start Camera' : 'Select Camera First';
        }
    }
    
    async startCamera() {
        const cameraSelect = document.getElementById('cameraSelect');
        const video = document.getElementById('cameraVideo');
        const captureBtn = document.getElementById('captureBtn');
        const startCameraBtn = document.getElementById('startCameraBtn');
        
        if (!cameraSelect?.value) {
            this.showMessage('Please select a camera', 'warning');
            return;
        }
        
        try {
            // Stop existing stream
            this.stopCamera();
            
            const constraints = {
                video: {
                    deviceId: { exact: cameraSelect.value },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };
            
            this.currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            const cameraContainer = document.getElementById('cameraContainer');
            const cameraPlaceholder = document.querySelector('.camera-placeholder');
            
            if (video) {
                video.srcObject = this.currentStream;
                video.style.display = 'block';
                
                // Wait for video to be ready, then start smart detection
                video.addEventListener('loadedmetadata', () => {
                    if (cameraContainer) {
                        cameraContainer.style.display = 'block';
                    }
                    if (cameraPlaceholder) {
                        cameraPlaceholder.style.display = 'none';
                    }
                    
                    // Apply current brightness/contrast adjustments
                    this.updateVideoFilters();
                    
                    // Show grid lines if enabled
                    if (this.gridLinesEnabled) {
                        setTimeout(() => {
                            this.showGridLines();
                        }, 500);
                    }
                    
                    // Start edge detection after a short delay
                    setTimeout(() => {
                        this.startEdgeDetection();
                    }, 1000);
                });
            }
            
            if (captureBtn) {
                captureBtn.style.display = 'block';
            }
            
            if (startCameraBtn) {
                startCameraBtn.textContent = 'Stop Camera';
                startCameraBtn.onclick = () => this.stopCamera();
            }
            
            this.showMessage('Smart camera started - edge detection active!', 'success');
        } catch (error) {
            console.error('Camera start error:', error);
            this.handleCameraError(error);
        }
    }
    
    stopCamera() {
        // Stop smart detection
        this.stopEdgeDetection();
        
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
            this.currentStream = null;
        }
        
        const video = document.getElementById('cameraVideo');
        const captureBtn = document.getElementById('captureBtn');
        const startCameraBtn = document.getElementById('startCameraBtn');
        const cameraContainer = document.getElementById('cameraContainer');
        const cameraPlaceholder = document.querySelector('.camera-placeholder');
        
        if (video) {
            video.style.display = 'none';
            video.srcObject = null;
        }
        
        if (cameraContainer) {
            cameraContainer.style.display = 'none';
        }
        
        if (cameraPlaceholder) {
            cameraPlaceholder.style.display = 'block';
        }
        
        if (captureBtn) {
            captureBtn.style.display = 'none';
        }
        
        if (startCameraBtn) {
            startCameraBtn.textContent = 'Start Camera';
            startCameraBtn.onclick = () => this.startCamera();
        }
    }
    
    handleCameraError(error) {
        let message = 'Camera error occurred';
        
        switch (error.name) {
            case 'NotAllowedError':
                message = 'Camera permission denied. Please allow camera access and try again.';
                break;
            case 'NotFoundError':
                message = 'No camera found. Please check your camera connection.';
                break;
            case 'NotReadableError':
                message = 'Camera is being used by another application.';
                break;
            case 'OverconstrainedError':
                message = 'Camera constraints not supported. Try a different camera.';
                break;
        }
        
        this.showMessage(message, 'error');
    }
    
    capturePhoto() {
        const video = document.getElementById('cameraVideo');
        const canvas = document.getElementById('captureCanvas');
        const captureBtn = document.getElementById('captureBtn');
        
        if (!video || !canvas || !this.currentStream) {
            this.showMessage('Camera not ready', 'error');
            return;
        }
        
        // Disable capture button temporarily to prevent double clicks
        if (captureBtn) {
            captureBtn.disabled = true;
            captureBtn.innerHTML = '<i class="bi bi-camera-fill"></i> Capturing...';
        }
        
        // Add camera shutter effect
        this.showCameraShutterEffect();
        
        const context = canvas.getContext('2d');
        
        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        if (canvas.width === 0 || canvas.height === 0) {
            this.showMessage('Could not capture photo - invalid dimensions', 'error');
            this.resetCaptureButton();
            return;
        }
        
        // Apply brightness/contrast/saturation adjustments to the canvas
        const brightness = this.cameraBrightness / 100;
        const contrast = this.cameraContrast / 100;
        const saturation = this.cameraSaturation / 100;
        context.filter = `brightness(${brightness}) contrast(${contrast}) saturate(${saturation})`;
        
        // Draw current frame with adjustments
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Reset canvas filter for further processing
        context.filter = 'none';

        // Apply smart enhancements if enabled
        let processedCanvas = canvas;
        if (this.perspectiveCorrectionEnabled && this.lastDetectedCorners && this.openCVReady && window.cv) {
            processedCanvas = this.applyPerspectiveCorrection(canvas, this.lastDetectedCorners);
        }

        // Auto-save to database: Upload immediately
        processedCanvas.toBlob((blob) => {
            if (!blob) {
                this.showMessage('Failed to capture photo', 'error');
                this.resetCaptureButton();
                return;
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const file = new File([blob], `camera-photo-${timestamp}.jpg`, { type: 'image/jpeg' });

            // Immediately upload single file
            this.uploadSingleFile(file)
                .then(() => {
                    // Only add to captured photos for tracking, NOT to selectedFiles
                    this.capturedPhotos.push(file);
                    
                    // Enhanced success confirmation
                    this.showSuccessConfirmation();
                    
                    // Reset capture button
                    setTimeout(() => {
                        this.resetCaptureButton();
                    }, 1500);
                })
                .catch((error) => {
                    this.showMessage(`Upload failed: ${error.message}`, 'error');
                    console.error('Upload error:', error);
                    this.resetCaptureButton();
                });
        }, 'image/jpeg', 0.9);
    }
    
    applyPerspectiveCorrection(canvas, corners) {
        try {
            if (!window.cv || corners.length !== 4) return canvas;
            
            const src = cv.imread(canvas);
            const dst = new cv.Mat();
            
            // Sort corners to get them in correct order (top-left, top-right, bottom-right, bottom-left)
            const sortedCorners = this.sortCorners(corners);
            
            // Define source points (detected corners)
            const srcPoints = cv.matFromArray(4, 1, cv.CV_32FC2, [
                sortedCorners[0].x, sortedCorners[0].y,  // top-left
                sortedCorners[1].x, sortedCorners[1].y,  // top-right
                sortedCorners[2].x, sortedCorners[2].y,  // bottom-right
                sortedCorners[3].x, sortedCorners[3].y   // bottom-left
            ]);
            
            // Calculate output dimensions to maintain aspect ratio
            const width1 = Math.sqrt(Math.pow(sortedCorners[1].x - sortedCorners[0].x, 2) + 
                                   Math.pow(sortedCorners[1].y - sortedCorners[0].y, 2));
            const width2 = Math.sqrt(Math.pow(sortedCorners[2].x - sortedCorners[3].x, 2) + 
                                   Math.pow(sortedCorners[2].y - sortedCorners[3].y, 2));
            const height1 = Math.sqrt(Math.pow(sortedCorners[3].x - sortedCorners[0].x, 2) + 
                                    Math.pow(sortedCorners[3].y - sortedCorners[0].y, 2));
            const height2 = Math.sqrt(Math.pow(sortedCorners[2].x - sortedCorners[1].x, 2) + 
                                    Math.pow(sortedCorners[2].y - sortedCorners[1].y, 2));
            
            const outputWidth = Math.max(width1, width2);
            const outputHeight = Math.max(height1, height2);
            
            // Define destination points (rectangle)
            const dstPoints = cv.matFromArray(4, 1, cv.CV_32FC2, [
                0, 0,                           // top-left
                outputWidth, 0,                 // top-right
                outputWidth, outputHeight,      // bottom-right
                0, outputHeight                 // bottom-left
            ]);
            
            // Apply perspective transformation
            const transform = cv.getPerspectiveTransform(srcPoints, dstPoints);
            cv.warpPerspective(src, dst, transform, new cv.Size(outputWidth, outputHeight));
            
            // Create output canvas
            const outputCanvas = document.createElement('canvas');
            cv.imshow(outputCanvas, dst);
            
            // Cleanup
            src.delete();
            dst.delete();
            srcPoints.delete();
            dstPoints.delete();
            transform.delete();
            
            console.log('Applied perspective correction successfully');
            return outputCanvas;
            
        } catch (error) {
            console.warn('Perspective correction failed, using original:', error);
            return canvas;
        }
    }
    
    sortCorners(corners) {
        // Sort corners to: top-left, top-right, bottom-right, bottom-left
        const sorted = [...corners];
        
        // Find center point
        const centerX = sorted.reduce((sum, p) => sum + p.x, 0) / 4;
        const centerY = sorted.reduce((sum, p) => sum + p.y, 0) / 4;
        
        // Sort by angle from center
        sorted.sort((a, b) => {
            const angleA = Math.atan2(a.y - centerY, a.x - centerX);
            const angleB = Math.atan2(b.y - centerY, b.x - centerX);
            return angleA - angleB;
        });
        
        // Rearrange to standard order: top-left, top-right, bottom-right, bottom-left
        const result = new Array(4);
        let topLeft = 0;
        let minSum = sorted[0].x + sorted[0].y;
        
        for (let i = 1; i < 4; i++) {
            const sum = sorted[i].x + sorted[i].y;
            if (sum < minSum) {
                minSum = sum;
                topLeft = i;
            }
        }
        
        result[0] = sorted[topLeft];                    // top-left
        result[1] = sorted[(topLeft + 1) % 4];         // top-right
        result[2] = sorted[(topLeft + 2) % 4];         // bottom-right
        result[3] = sorted[(topLeft + 3) % 4];         // bottom-left
        
        return result;
    }
    
    // Camera adjustment helper methods
    updateVideoFilters() {
        const video = document.getElementById('cameraVideo');
        if (video && this.currentStream) {
            const brightness = this.cameraBrightness / 100;
            const contrast = this.cameraContrast / 100;
            const saturation = this.cameraSaturation / 100;
            video.style.filter = `brightness(${brightness}) contrast(${contrast}) saturate(${saturation})`;
        }
    }
    
    updateBrightnessDisplay(value) {
        const brightnessDisplay = document.getElementById('brightnessValue');
        if (brightnessDisplay) {
            brightnessDisplay.textContent = `${value}%`;
        }
    }
    
    updateContrastDisplay(value) {
        const contrastDisplay = document.getElementById('contrastValue');
        if (contrastDisplay) {
            contrastDisplay.textContent = `${value}%`;
        }
    }
    
    updateSaturationDisplay(value) {
        const saturationDisplay = document.getElementById('saturationValue');
        if (saturationDisplay) {
            saturationDisplay.textContent = `${value}%`;
        }
    }
    
    resetCameraAdjustments() {
        this.cameraBrightness = 100;
        this.cameraContrast = 100;
        this.cameraSaturation = 100;
        
        // Update UI controls
        const brightnessSlider = document.getElementById('cameraBrightness');
        const contrastSlider = document.getElementById('cameraContrast');
        const saturationSlider = document.getElementById('cameraSaturation');
        
        if (brightnessSlider) {
            brightnessSlider.value = 100;
        }
        if (contrastSlider) {
            contrastSlider.value = 100;
        }
        if (saturationSlider) {
            saturationSlider.value = 100;
        }
        
        // Update displays
        this.updateBrightnessDisplay(100);
        this.updateContrastDisplay(100);
        this.updateSaturationDisplay(100);
        
        // Apply to video
        this.updateVideoFilters();
        
        this.showMessage('Camera adjustments reset to default', 'info');
    }
    
    // Grid lines functionality
    toggleGridLines() {
        const gridCanvas = document.getElementById('gridCanvas');
        if (!gridCanvas) return;
        
        if (this.gridLinesEnabled) {
            this.showGridLines();
        } else {
            this.hideGridLines();
        }
    }
    
    showGridLines() {
        const video = document.getElementById('cameraVideo');
        const gridCanvas = document.getElementById('gridCanvas');
        
        if (!video || !gridCanvas || !this.currentStream) return;
        
        // Match grid canvas size to video
        gridCanvas.width = video.videoWidth || video.offsetWidth;
        gridCanvas.height = video.videoHeight || video.offsetHeight;
        gridCanvas.style.display = 'block';
        
        this.drawGridLines();
    }
    
    hideGridLines() {
        const gridCanvas = document.getElementById('gridCanvas');
        if (gridCanvas) {
            gridCanvas.style.display = 'none';
        }
    }
    
    drawGridLines() {
        const gridCanvas = document.getElementById('gridCanvas');
        if (!gridCanvas) return;
        
        const ctx = gridCanvas.getContext('2d');
        const width = gridCanvas.width;
        const height = gridCanvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Set grid line style
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]); // Dashed lines
        
        // Draw rule of thirds grid (2 vertical + 2 horizontal lines)
        ctx.beginPath();
        
        // Vertical lines
        const verticalStep = width / 3;
        for (let i = 1; i < 3; i++) {
            const x = verticalStep * i;
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
        }
        
        // Horizontal lines
        const horizontalStep = height / 3;
        for (let i = 1; i < 3; i++) {
            const y = horizontalStep * i;
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
        }
        
        ctx.stroke();
        
        // Add subtle corner markers for better composition guidance
        ctx.setLineDash([]); // Solid lines for corners
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.lineWidth = 2;
        
        const cornerSize = 20;
        const corners = [
            {x: verticalStep, y: horizontalStep},         // Top-left intersection
            {x: verticalStep * 2, y: horizontalStep},     // Top-right intersection
            {x: verticalStep, y: horizontalStep * 2},     // Bottom-left intersection
            {x: verticalStep * 2, y: horizontalStep * 2}  // Bottom-right intersection
        ];
        
        corners.forEach(corner => {
            ctx.beginPath();
            ctx.arc(corner.x, corner.y, 4, 0, 2 * Math.PI);
            ctx.stroke();
        });
    }
    
    // Focus confirmation functionality
    analyzeFocus(src) {
        if (!this.openCVReady || !window.cv) return;
        
        try {
            const gray = new cv.Mat();
            const laplacian = new cv.Mat();
            
            // Convert to grayscale for focus analysis
            cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY);
            
            // Apply Laplacian operator to detect edges (higher variance = better focus)
            cv.Laplacian(gray, laplacian, cv.CV_64F);
            
            // Calculate variance of Laplacian
            const mean = cv.mean(laplacian);
            const variance = this.calculateVariance(laplacian, mean[0]);
            
            // Update focus status based on variance threshold
            this.isFocused = variance > this.focusThreshold;
            
            // Cleanup
            gray.delete();
            laplacian.delete();
            
        } catch (error) {
            console.warn('Focus analysis error:', error);
        }
    }
    
    calculateVariance(mat, mean) {
        // Simple variance calculation for focus detection
        let sum = 0;
        let count = 0;
        
        for (let i = 0; i < mat.rows; i++) {
            for (let j = 0; j < mat.cols; j++) {
                const pixel = mat.data64F[i * mat.cols + j];
                sum += Math.pow(pixel - mean, 2);
                count++;
            }
        }
        
        return count > 0 ? sum / count : 0;
    }
    
    
    // Enhanced focus confirmation with green outline
    drawFocusOutline(ctx, width, height) {
        if (!this.focusConfirmationEnabled || !this.isFocused) return;
        
        ctx.save();
        
        // Draw green outline around entire camera view
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 4;
        ctx.setLineDash([]);
        
        // Main outline
        ctx.beginPath();
        ctx.rect(2, 2, width - 4, height - 4);
        ctx.stroke();
        
        // Inner glow effect
        ctx.strokeStyle = 'rgba(0, 255, 0, 0.5)';
        ctx.lineWidth = 8;
        ctx.beginPath();
        ctx.rect(0, 0, width, height);
        ctx.stroke();
        
        // Corner indicators for extra emphasis
        const cornerSize = 30;
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        
        // Top-left corner
        ctx.beginPath();
        ctx.moveTo(10, 10);
        ctx.lineTo(10 + cornerSize, 10);
        ctx.moveTo(10, 10);
        ctx.lineTo(10, 10 + cornerSize);
        ctx.stroke();
        
        // Top-right corner
        ctx.beginPath();
        ctx.moveTo(width - 10, 10);
        ctx.lineTo(width - 10 - cornerSize, 10);
        ctx.moveTo(width - 10, 10);
        ctx.lineTo(width - 10, 10 + cornerSize);
        ctx.stroke();
        
        // Bottom-left corner
        ctx.beginPath();
        ctx.moveTo(10, height - 10);
        ctx.lineTo(10 + cornerSize, height - 10);
        ctx.moveTo(10, height - 10);
        ctx.lineTo(10, height - 10 - cornerSize);
        ctx.stroke();
        
        // Bottom-right corner
        ctx.beginPath();
        ctx.moveTo(width - 10, height - 10);
        ctx.lineTo(width - 10 - cornerSize, height - 10);
        ctx.moveTo(width - 10, height - 10);
        ctx.lineTo(width - 10, height - 10 - cornerSize);
        ctx.stroke();
        
        // "IN FOCUS" text indicator
        ctx.fillStyle = '#00ff00';
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('IN FOCUS', width / 2, 30);
        
        ctx.restore();
    }
    
    // Motion detection and stability analysis
    analyzeMotionAndStability(src) {
        if (!this.openCVReady || !window.cv) return;
        
        try {
            const gray = new cv.Mat();
            cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY);
            
            if (this.lastFrameData) {
                // Calculate frame difference for motion detection
                const diff = new cv.Mat();
                cv.absdiff(gray, this.lastFrameData, diff);
                
                // Calculate total pixel differences
                const sum = cv.sumElems(diff);
                const motionLevel = sum[0];
                
                // Update motion status
                this.hasMotion = motionLevel > this.motionThreshold;
                
                // Update stability tracking
                if (this.hasMotion) {
                    this.stabilityFrames = 0;
                    this.isStable = false;
                } else {
                    this.stabilityFrames++;
                    if (this.stabilityFrames >= this.stabilityRequiredFrames) {
                        this.isStable = true;
                    }
                }
                
                diff.delete();
            }
            
            // Store current frame for next comparison
            if (this.lastFrameData) {
                this.lastFrameData.delete();
            }
            this.lastFrameData = gray.clone();
            
            gray.delete();
            
        } catch (error) {
            console.warn('Motion detection error:', error);
        }
    }
    
    // Draw motion and stability indicators
    drawStabilityIndicators(ctx, width, height) {
        const margin = 15;
        const indicatorSize = 24;
        
        ctx.save();
        
        // Motion warning (top-left corner)
        if (this.motionDetectionEnabled && this.hasMotion) {
            const x = margin;
            const y = margin;
            
            // Pulsing red warning for motion
            const alpha = 0.6 + 0.4 * Math.sin(Date.now() / 200);
            ctx.fillStyle = `rgba(255, 0, 0, ${alpha})`;
            ctx.strokeStyle = '#ff0000';
            ctx.lineWidth = 2;
            
            // Warning triangle
            ctx.beginPath();
            ctx.moveTo(x + indicatorSize / 2, y);
            ctx.lineTo(x, y + indicatorSize);
            ctx.lineTo(x + indicatorSize, y + indicatorSize);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            
            // Exclamation mark
            ctx.fillStyle = 'white';
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('!', x + indicatorSize / 2, y + indicatorSize - 6);
            
            // Warning text
            ctx.fillStyle = '#ff0000';
            ctx.font = 'bold 11px Arial';
            ctx.textAlign = 'left';
            ctx.fillText('MOTION DETECTED', x + indicatorSize + 8, y + indicatorSize / 2 + 4);
        }
        
        // Stability indicator (bottom-left corner)
        if (this.stabilityIndicatorEnabled) {
            const x = margin;
            const y = height - indicatorSize - margin;
            
            if (this.isStable) {
                // Green stable indicator
                ctx.fillStyle = 'rgba(0, 255, 0, 0.8)';
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 2;
                
                // Stable circle with checkmark
                ctx.beginPath();
                ctx.arc(x + indicatorSize / 2, y + indicatorSize / 2, indicatorSize / 2, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();
                
                ctx.fillStyle = 'white';
                ctx.font = 'bold 14px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('✓', x + indicatorSize / 2, y + indicatorSize / 2);
                
                // Stable text
                ctx.fillStyle = '#00ff00';
                ctx.font = 'bold 11px Arial';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText('STABLE', x + indicatorSize + 8, y + indicatorSize / 2);
                
            } else {
                // Yellow stabilizing indicator
                const progress = Math.min(this.stabilityFrames / this.stabilityRequiredFrames, 1);
                ctx.fillStyle = 'rgba(255, 165, 0, 0.8)';
                ctx.strokeStyle = '#ffa500';
                ctx.lineWidth = 2;
                
                // Progress circle
                ctx.beginPath();
                ctx.arc(x + indicatorSize / 2, y + indicatorSize / 2, indicatorSize / 2, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();
                
                // Progress arc
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(x + indicatorSize / 2, y + indicatorSize / 2, indicatorSize / 2 - 2, 
                       -Math.PI / 2, -Math.PI / 2 + (2 * Math.PI * progress));
                ctx.stroke();
                
                // Stabilizing text
                ctx.fillStyle = '#ffa500';
                ctx.font = 'bold 11px Arial';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText('STABILIZING...', x + indicatorSize + 8, y + indicatorSize / 2);
            }
        }
        
        ctx.restore();
    }
    
    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('files[]', file);
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content 
                       || document.querySelector('input[name="csrf_token"]')?.value;
        if (csrfToken) {
            formData.append('csrf_token', csrfToken);
        }
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                return data;
            } else {
                throw new Error(data.message || data.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            throw error;
        }
    }
    
    handleFileSelection(event) {
        const files = Array.from(event.target.files || []);
        
        if (files.length === 0) {
            return;
        }
        
        const validFiles = this.validateFiles(files);
        
        if (validFiles.length === 0) {
            this.showMessage('No valid image files selected', 'warning');
            return;
        }
        
        this.selectedFiles = [...this.selectedFiles, ...validFiles];
        this.updateFileDisplay();
        
        const message = validFiles.length === 1 
            ? `Selected: ${validFiles[0].name}`
            : `Selected ${validFiles.length} files`;
        this.showMessage(message, 'success');
    }
    
    validateFiles(files) {
        return files.filter(file => {
            if (!this.allowedTypes.includes(file.type.toLowerCase())) {
                this.showMessage(`${file.name}: Invalid file type`, 'error');
                return false;
            }
            
            if (file.size > this.maxFileSize) {
                this.showMessage(`${file.name}: File too large (max 16MB)`, 'error');
                return false;
            }
            
            return true;
        });
    }
    
    updateFileDisplay() {
        const uploadBtn = document.getElementById('uploadBtn');
        const previews = document.getElementById('filePreviews');
        
        // Update upload button state
        if (uploadBtn) {
            uploadBtn.disabled = this.selectedFiles.length === 0 || this.isUploading;
        }
        
        // Update file previews
        if (previews) {
            if (this.selectedFiles.length > 0) {
                previews.style.display = '';
                this.renderFilePreview();
            } else {
                previews.innerHTML = '';
                previews.style.display = 'none';
            }
        }
    }
    
    renderFilePreview() {
        const container = document.getElementById('filePreviews');
        if (!container) return;
        container.innerHTML = '';

        this.selectedFiles.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'position-relative d-inline-block me-2 mb-2';
            item.style.width = '100px';
            item.style.height = '100px';

            const img = document.createElement('img');
            img.alt = file.name;
            img.className = 'rounded border';
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';

            if (file.type && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => { img.src = e.target.result; };
                reader.readAsDataURL(file);
            } else {
                img.src = '/static/img/placeholder.png';
            }

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-sm btn-danger position-absolute top-0 end-0 translate-middle';
            removeBtn.style.zIndex = '2';
            removeBtn.innerHTML = '<i class="bi bi-x"></i>';
            removeBtn.addEventListener('click', () => this.removeFile(index));

            const caption = document.createElement('div');
            caption.className = 'position-absolute bottom-0 start-0 w-100 bg-dark bg-opacity-50 text-white text-truncate px-1';
            caption.style.fontSize = '0.7rem';
            caption.textContent = file.name;

            item.appendChild(img);
            item.appendChild(removeBtn);
            item.appendChild(caption);
            container.appendChild(item);
        });
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFileDisplay();
        this.showMessage('File removed', 'info');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize uploader when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('uploadForm')) {
        window.photoVaultUploader = new PhotoVaultUploader();
    }
});

// Missing methods - added as prototype methods
PhotoVaultUploader.prototype.showMessage = function(message, type = 'info', timeout = 3000) {
    const box = document.getElementById('uploadProgress');
    if (!box) { console.log(`[${type}] ${message}`); return; }
    const map = { success: 'alert-success', info: 'alert-info', warning: 'alert-warning', error: 'alert-danger' };
    box.className = `alert ${map[type] || 'alert-info'} mt-3`;
    box.textContent = message;
    box.style.display = 'block';
    if (timeout !== 0) {
        clearTimeout(this._msgTimer);
        this._msgTimer = setTimeout(() => { box.style.display = 'none'; }, timeout);
    }
};

// Camera shutter effect for photo capture confirmation
PhotoVaultUploader.prototype.showCameraShutterEffect = function() {
    // Create a full-screen white overlay for shutter effect
    const shutterOverlay = document.createElement('div');
    shutterOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: white;
        z-index: 9999;
        opacity: 0.9;
        pointer-events: none;
        transition: opacity 0.1s ease-out;
    `;
    
    document.body.appendChild(shutterOverlay);
    
    // Fade out the overlay
    setTimeout(() => {
        shutterOverlay.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(shutterOverlay);
        }, 100);
    }, 100);
    
    // Optional: Camera shutter sound effect (uncomment if needed)
    // this.playCameraShutterSound();
};

// Enhanced success confirmation with icons and animations
PhotoVaultUploader.prototype.showSuccessConfirmation = function() {
    // Create enhanced success message with icon
    const successMessage = `
        <i class="bi bi-check-circle-fill text-success"></i> 
        <strong>Photo Captured Successfully!</strong>
        <br><small>Your photo has been saved and uploaded to PhotoVault</small>
    `;
    
    // Show the enhanced message
    const box = document.getElementById('uploadProgress');
    if (box) {
        box.className = 'alert alert-success mt-3';
        box.innerHTML = successMessage;
        box.style.display = 'block';
        box.style.animation = 'fadeInScale 0.5s ease-out';
        
        // Add temporary styling for the success animation
        if (!document.getElementById('success-animation-style')) {
            const style = document.createElement('style');
            style.id = 'success-animation-style';
            style.textContent = `
                @keyframes fadeInScale {
                    0% { 
                        opacity: 0; 
                        transform: scale(0.8); 
                    }
                    50% { 
                        opacity: 1; 
                        transform: scale(1.05); 
                    }
                    100% { 
                        opacity: 1; 
                        transform: scale(1); 
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Show follow-up message after 3 seconds
        setTimeout(() => {
            box.innerHTML = `
                <i class="bi bi-images text-primary"></i> 
                <strong>Ready for Next Photo</strong>
                <br><small>View your photos in the <a href="/dashboard" class="text-decoration-none">Dashboard</a></small>
            `;
            box.className = 'alert alert-info mt-3';
        }, 3000);
        
        // Auto-hide after 6 seconds
        setTimeout(() => {
            box.style.display = 'none';
        }, 6000);
    }
};

// Reset capture button to original state
PhotoVaultUploader.prototype.resetCaptureButton = function() {
    const captureBtn = document.getElementById('captureBtn');
    if (captureBtn) {
        captureBtn.disabled = false;
        captureBtn.innerHTML = '<i class="bi bi-camera-fill"></i> Capture Photo';
    }
};

// Optional: Camera shutter sound effect
PhotoVaultUploader.prototype.playCameraShutterSound = function() {
    try {
        // Create a short beep sound using Web Audio API
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    } catch (error) {
        // Silently ignore if audio context is not supported
        console.log('Audio context not supported');
    }
};

PhotoVaultUploader.prototype.setupDragAndDrop = function(area) {
    const stop = (e) => { e.preventDefault(); e.stopPropagation(); };
    ['dragenter','dragover'].forEach(ev => area.addEventListener(ev, (e)=>{ stop(e); area.classList.add('dragover'); }));
    ['dragleave','drop'].forEach(ev => area.addEventListener(ev, (e)=>{ stop(e); area.classList.remove('dragover'); }));
    area.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer?.files || []);
        if (!files.length) return;
        const valid = this.validateFiles(files);
        if (!valid.length) { this.showMessage('No valid image files dropped', 'warning'); return; }
        this.selectedFiles = this.selectedFiles.concat(valid);
        this.updateFileDisplay();
        this.showMessage(`Added ${valid.length} file(s)`, 'success');
    });
};

PhotoVaultUploader.prototype.handleFormSubmit = async function(e) {
    e.preventDefault();
    if (this.isUploading) return;
    if (!this.selectedFiles.length) { this.showMessage('Please select files first', 'warning'); return; }
    this.isUploading = true;
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) uploadBtn.disabled = true;
    let ok = 0, fail = 0;
    this.showMessage(`Uploading ${this.selectedFiles.length} file(s)...`, 'info', 0);
    for (const file of this.selectedFiles) {
        try { 
            await this.uploadSingleFile(file); 
            ok++; 
            this.showMessage(`Uploaded ${ok}/${this.selectedFiles.length}`, 'info', 0); 
        }
        catch { 
            fail++; 
        }
    }
    this.isUploading = false;
    if (uploadBtn) uploadBtn.disabled = false;
    this.selectedFiles = [];
    this.updateFileDisplay();
    this.showMessage(fail ? `Uploaded ${ok}, failed ${fail}` : `Uploaded ${ok} file(s) successfully`, fail ? 'warning' : 'success');
};