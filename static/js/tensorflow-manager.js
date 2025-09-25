/**
 * PhotoVault TensorFlow.js Manager
 * Handles AI model loading and management for enhanced camera features
 */
class PhotoVaultTensorFlowManager {
    constructor() {
        console.log('🤖 Initializing PhotoVault TensorFlow.js Manager');
        
        this.models = {
            cocoSSD: null,
            blazeFace: null,
            poseNet: null,
            deepLab: null
        };
        
        this.isLoading = false;
        this.loadedModels = new Set();
        this.modelLoadingPromises = new Map();
        
        // Performance settings
        this.config = {
            cocoSSD: {
                base: 'mobilenet_v2',
                minScore: 0.6
            },
            blazeFace: {
                returnTensors: false,
                flipHorizontal: false,
                maxFaces: 10
            },
            poseNet: {
                architecture: 'MobileNetV1',
                outputStride: 16,
                inputResolution: { width: 640, height: 480 },
                multiplier: 0.75
            }
        };
        
        // Initialize TensorFlow.js backend
        this.initializeBackend();
    }

    async initializeBackend() {
        try {
            // Set backend to WebGL for better performance
            await tf.setBackend('webgl');
            console.log('✅ TensorFlow.js WebGL backend initialized');
        } catch (error) {
            console.warn('⚠️ WebGL backend failed, falling back to CPU:', error);
            await tf.setBackend('cpu');
        }
        
        // Enable memory management
        tf.env().set('WEBGL_PACK', true);
        tf.env().set('WEBGL_FORCE_F16_TEXTURES', true);
    }

    async initializeModels(modelNames = ['cocoSSD', 'blazeFace']) {
        this.isLoading = true;
        console.log('🤖 Loading TensorFlow.js models:', modelNames);
        
        try {
            // Load models in parallel for faster initialization
            const loadPromises = modelNames.map(modelName => {
                switch (modelName) {
                    case 'cocoSSD':
                        return this.loadCocoSSD();
                    case 'blazeFace':
                        return this.loadBlazeFace();
                    case 'poseNet':
                        return this.loadPoseNet();
                    case 'deepLab':
                        return this.loadDeepLab();
                    default:
                        return Promise.resolve();
                }
            });
            
            await Promise.allSettled(loadPromises);
            console.log('✅ TensorFlow.js models loaded successfully');
            this.isLoading = false;
            return true;
        } catch (error) {
            console.error('❌ Failed to load TensorFlow.js models:', error);
            this.isLoading = false;
            return false;
        }
    }

    async loadCocoSSD() {
        if (this.modelLoadingPromises.has('cocoSSD')) {
            return this.modelLoadingPromises.get('cocoSSD');
        }

        const loadPromise = (async () => {
            try {
                console.log('⏳ Loading COCO-SSD model...');
                this.models.cocoSSD = await cocoSsd.load(this.config.cocoSSD);
                this.loadedModels.add('cocoSSD');
                console.log('✅ COCO-SSD model loaded successfully');
                return this.models.cocoSSD;
            } catch (error) {
                console.error('❌ Failed to load COCO-SSD:', error);
                throw error;
            }
        })();

        this.modelLoadingPromises.set('cocoSSD', loadPromise);
        return loadPromise;
    }

    async loadBlazeFace() {
        if (this.modelLoadingPromises.has('blazeFace')) {
            return this.modelLoadingPromises.get('blazeFace');
        }

        const loadPromise = (async () => {
            try {
                console.log('⏳ Loading BlazeFace model...');
                this.models.blazeFace = await blazeface.load();
                this.loadedModels.add('blazeFace');
                console.log('✅ BlazeFace model loaded successfully');
                return this.models.blazeFace;
            } catch (error) {
                console.error('❌ Failed to load BlazeFace:', error);
                throw error;
            }
        })();

        this.modelLoadingPromises.set('blazeFace', loadPromise);
        return loadPromise;
    }

    async loadPoseNet() {
        if (this.modelLoadingPromises.has('poseNet')) {
            return this.modelLoadingPromises.get('poseNet');
        }

        const loadPromise = (async () => {
            try {
                console.log('⏳ Loading PoseNet model...');
                this.models.poseNet = await posenet.load(this.config.poseNet);
                this.loadedModels.add('poseNet');
                console.log('✅ PoseNet model loaded successfully');
                return this.models.poseNet;
            } catch (error) {
                console.error('❌ Failed to load PoseNet:', error);
                throw error;
            }
        })();

        this.modelLoadingPromises.set('poseNet', loadPromise);
        return loadPromise;
    }

    async loadDeepLab() {
        if (this.modelLoadingPromises.has('deepLab')) {
            return this.modelLoadingPromises.get('deepLab');
        }

        const loadPromise = (async () => {
            try {
                console.log('⏳ Loading DeepLab model...');
                this.models.deepLab = await deeplab.load({
                    base: 'pascal',
                    quantizationBytes: 2
                });
                this.loadedModels.add('deepLab');
                console.log('✅ DeepLab model loaded successfully');
                return this.models.deepLab;
            } catch (error) {
                console.error('❌ Failed to load DeepLab:', error);
                throw error;
            }
        })();

        this.modelLoadingPromises.set('deepLab', loadPromise);
        return loadPromise;
    }

    // Object Detection with COCO-SSD
    async detectObjects(imageElement) {
        if (!this.models.cocoSSD) {
            console.warn('COCO-SSD model not loaded');
            return [];
        }

        try {
            const predictions = await this.models.cocoSSD.detect(imageElement);
            return predictions.filter(prediction => prediction.score > this.config.cocoSSD.minScore);
        } catch (error) {
            console.error('Object detection failed:', error);
            return [];
        }
    }

    // Face Detection with BlazeFace
    async detectFaces(imageElement) {
        if (!this.models.blazeFace) {
            console.warn('BlazeFace model not loaded');
            return [];
        }

        try {
            const predictions = await this.models.blazeFace.estimateFaces(
                imageElement, 
                this.config.blazeFace.returnTensors
            );
            
            return predictions.map(face => ({
                bbox: [
                    face.topLeft[0], 
                    face.topLeft[1], 
                    face.bottomRight[0] - face.topLeft[0], 
                    face.bottomRight[1] - face.topLeft[1]
                ],
                landmarks: face.landmarks,
                probability: face.probability || 1.0
            }));
        } catch (error) {
            console.error('Face detection failed:', error);
            return [];
        }
    }

    // Pose Detection with PoseNet
    async detectPoses(imageElement) {
        if (!this.models.poseNet) {
            console.warn('PoseNet model not loaded');
            return [];
        }

        try {
            const poses = await this.models.poseNet.estimateMultiplePoses(imageElement);
            return poses.filter(pose => pose.score > 0.3);
        } catch (error) {
            console.error('Pose detection failed:', error);
            return [];
        }
    }

    // Image Segmentation with DeepLab
    async segmentImage(imageElement) {
        if (!this.models.deepLab) {
            console.warn('DeepLab model not loaded');
            return null;
        }

        try {
            const segmentation = await this.models.deepLab.segment(imageElement);
            return segmentation;
        } catch (error) {
            console.error('Image segmentation failed:', error);
            return null;
        }
    }

    // Memory management
    disposeModels() {
        Object.keys(this.models).forEach(modelName => {
            if (this.models[modelName] && this.models[modelName].dispose) {
                this.models[modelName].dispose();
                this.models[modelName] = null;
            }
        });
        this.loadedModels.clear();
        console.log('🗑️ TensorFlow.js models disposed');
    }

    // Performance monitoring
    getMemoryInfo() {
        return {
            numTensors: tf.memory().numTensors,
            numDataBuffers: tf.memory().numDataBuffers,
            numBytes: tf.memory().numBytes,
            loadedModels: Array.from(this.loadedModels)
        };
    }

    // Model status check
    isModelLoaded(modelName) {
        return this.loadedModels.has(modelName) && this.models[modelName] !== null;
    }

    getLoadingStatus() {
        return {
            isLoading: this.isLoading,
            loadedModels: Array.from(this.loadedModels),
            totalModels: Object.keys(this.models).length
        };
    }
}

// Activity Recognition Class
class ActivityRecognizer {
    constructor(tensorflowManager) {
        this.tensorflowManager = tensorflowManager;
        this.activityPatterns = {
            'waving': {
                keypoints: ['leftWrist', 'rightWrist', 'nose'],
                threshold: 0.5
            },
            'sitting': {
                keypoints: ['leftHip', 'rightHip', 'leftKnee', 'rightKnee'],
                threshold: 0.6
            },
            'standing': {
                keypoints: ['leftHip', 'rightHip', 'leftAnkle', 'rightAnkle'],
                threshold: 0.6
            },
            'raising_hands': {
                keypoints: ['leftWrist', 'rightWrist', 'leftShoulder', 'rightShoulder'],
                threshold: 0.5
            }
        };
    }

    async recognizeActivity(imageElement) {
        try {
            const poses = await this.tensorflowManager.detectPoses(imageElement);
            
            if (poses.length === 0) {
                return { activity: 'unknown', confidence: 0, poses: [] };
            }
            
            const activities = poses.map(pose => this.classifyPose(pose));
            
            // Return the most confident activity
            const bestActivity = activities.reduce((best, current) => 
                current.confidence > best.confidence ? current : best,
                { activity: 'unknown', confidence: 0 }
            );
            
            return {
                ...bestActivity,
                poses: poses.length,
                allActivities: activities
            };
        } catch (error) {
            console.error('Activity recognition failed:', error);
            return { activity: 'unknown', confidence: 0, poses: [] };
        }
    }

    classifyPose(pose) {
        const keypoints = pose.keypoints;
        
        // Get specific keypoints
        const nose = keypoints.find(kp => kp.part === 'nose');
        const leftWrist = keypoints.find(kp => kp.part === 'leftWrist');
        const rightWrist = keypoints.find(kp => kp.part === 'rightWrist');
        const leftShoulder = keypoints.find(kp => kp.part === 'leftShoulder');
        const rightShoulder = keypoints.find(kp => kp.part === 'rightShoulder');
        const leftHip = keypoints.find(kp => kp.part === 'leftHip');
        const rightHip = keypoints.find(kp => kp.part === 'rightHip');
        const leftAnkle = keypoints.find(kp => kp.part === 'leftAnkle');
        const rightAnkle = keypoints.find(kp => kp.part === 'rightAnkle');
        
        // Check for waving (hands above shoulders)
        if (this.isKeypointValid(nose) && this.isKeypointValid(leftWrist) && 
            this.isKeypointValid(rightWrist) && this.isKeypointValid(leftShoulder)) {
            const avgShoulderY = (leftShoulder.position.y + rightShoulder.position.y) / 2;
            if (leftWrist.position.y < avgShoulderY || rightWrist.position.y < avgShoulderY) {
                return { activity: 'waving', confidence: 0.8 };
            }
        }
        
        // Check for raising hands (both hands up)
        if (this.isKeypointValid(leftWrist) && this.isKeypointValid(rightWrist) && 
            this.isKeypointValid(leftShoulder) && this.isKeypointValid(rightShoulder)) {
            const avgShoulderY = (leftShoulder.position.y + rightShoulder.position.y) / 2;
            if (leftWrist.position.y < avgShoulderY && rightWrist.position.y < avgShoulderY) {
                return { activity: 'raising_hands', confidence: 0.9 };
            }
        }
        
        // Check for sitting (ankles closer to hips than expected)
        if (this.isKeypointValid(leftHip) && this.isKeypointValid(rightHip) && 
            this.isKeypointValid(leftAnkle) && this.isKeypointValid(rightAnkle)) {
            const avgHipY = (leftHip.position.y + rightHip.position.y) / 2;
            const avgAnkleY = (leftAnkle.position.y + rightAnkle.position.y) / 2;
            const legLength = avgAnkleY - avgHipY;
            
            if (legLength < 150) { // Threshold for sitting position
                return { activity: 'sitting', confidence: 0.7 };
            }
        }
        
        return { activity: 'standing', confidence: 0.5 };
    }

    isKeypointValid(keypoint) {
        return keypoint && keypoint.score > 0.3;
    }
}

// Smart Composition Analyzer
class SmartComposition {
    constructor(tensorflowManager) {
        this.tensorflowManager = tensorflowManager;
        this.ruleOfThirds = {
            horizontalLines: [1/3, 2/3],
            verticalLines: [1/3, 2/3]
        };
    }

    async analyzeComposition(imageElement) {
        try {
            const objects = await this.tensorflowManager.detectObjects(imageElement);
            const faces = await this.tensorflowManager.detectFaces(imageElement);
            const poses = await this.tensorflowManager.detectPoses(imageElement);
            
            const imageWidth = imageElement.width || imageElement.videoWidth;
            const imageHeight = imageElement.height || imageElement.videoHeight;
            
            // Find main subjects
            const mainSubjects = objects.filter(obj => 
                ['person', 'cat', 'dog', 'bird'].includes(obj.class) && obj.score > 0.7
            );

            const suggestions = [];
            
            // Analyze rule of thirds
            mainSubjects.forEach(subject => {
                const suggestion = this.analyzeRuleOfThirds(subject, imageWidth, imageHeight);
                if (suggestion) {
                    suggestions.push(suggestion);
                }
            });
            
            // Analyze face positioning
            faces.forEach(face => {
                const faceSuggestion = this.analyzeFacePosition(face, imageWidth, imageHeight);
                if (faceSuggestion) {
                    suggestions.push(faceSuggestion);
                }
            });

            return {
                mainSubjects,
                faces: faces.length,
                poses: poses.length,
                suggestions,
                composition: this.getCompositionScore(mainSubjects, faces, imageWidth, imageHeight)
            };
        } catch (error) {
            console.error('Composition analysis failed:', error);
            return {
                mainSubjects: [],
                faces: 0,
                poses: 0,
                suggestions: [],
                composition: { score: 0, feedback: 'Analysis failed' }
            };
        }
    }

    analyzeRuleOfThirds(subject, imageWidth, imageHeight) {
        const [x, y, width, height] = subject.bbox;
        const centerX = x + width / 2;
        const centerY = y + height / 2;
        
        const relativeX = centerX / imageWidth;
        const relativeY = centerY / imageHeight;
        
        // Check if subject is too centered
        const isHorizontallyCentered = Math.abs(relativeX - 0.5) < 0.1;
        const isVerticallyCentered = Math.abs(relativeY - 0.5) < 0.1;
        
        if (isHorizontallyCentered && isVerticallyCentered) {
            return {
                type: 'rule-of-thirds',
                severity: 'medium',
                message: `Try positioning the ${subject.class} off-center for better composition`,
                subject: subject.class,
                suggestedPosition: this.getNearestThirdsIntersection(relativeX, relativeY)
            };
        }
        
        return null;
    }

    analyzeFacePosition(face, imageWidth, imageHeight) {
        const [x, y, width, height] = face.bbox;
        const faceTop = y;
        const relativeTop = faceTop / imageHeight;
        
        // Check if face is too close to top edge
        if (relativeTop < 0.1) {
            return {
                type: 'face-positioning',
                severity: 'high',
                message: 'Face is too close to the top edge - leave more headroom',
                suggestedCrop: {
                    action: 'move_down',
                    amount: imageHeight * 0.1
                }
            };
        }
        
        return null;
    }

    getNearestThirdsIntersection(x, y) {
        const intersections = [
            { x: 1/3, y: 1/3 }, { x: 2/3, y: 1/3 },
            { x: 1/3, y: 2/3 }, { x: 2/3, y: 2/3 }
        ];
        
        let nearest = intersections[0];
        let minDistance = this.getDistance(x, y, nearest.x, nearest.y);
        
        intersections.forEach(intersection => {
            const distance = this.getDistance(x, y, intersection.x, intersection.y);
            if (distance < minDistance) {
                minDistance = distance;
                nearest = intersection;
            }
        });
        
        return nearest;
    }

    getDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }

    getCompositionScore(subjects, faces, imageWidth, imageHeight) {
        let score = 50; // Base score
        let feedback = [];
        
        // Bonus for having subjects
        if (subjects.length > 0) {
            score += 20;
            feedback.push('Good subject detection');
        }
        
        // Bonus for faces
        if (faces.length > 0) {
            score += 15;
            feedback.push('Faces detected');
        }
        
        // Analyze subject positioning
        subjects.forEach(subject => {
            const [x, y, width, height] = subject.bbox;
            const centerX = (x + width / 2) / imageWidth;
            const centerY = (y + height / 2) / imageHeight;
            
            // Check rule of thirds positioning
            const distanceToThirds = Math.min(
                Math.abs(centerX - 1/3),
                Math.abs(centerX - 2/3)
            );
            
            if (distanceToThirds < 0.1) {
                score += 10;
                feedback.push('Good rule of thirds positioning');
            }
        });
        
        return {
            score: Math.min(100, Math.max(0, score)),
            feedback: feedback.join(', ') || 'Basic composition'
        };
    }
}

// Export for global use
window.PhotoVaultTensorFlowManager = PhotoVaultTensorFlowManager;
window.ActivityRecognizer = ActivityRecognizer;
window.SmartComposition = SmartComposition;