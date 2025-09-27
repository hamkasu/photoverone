/*
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
*/

/**
 * PhotoVault TensorFlow.js Manager - DISABLED
 * AI functionality has been removed from PhotoVault
 */
class PhotoVaultTensorFlowManager {
    constructor() {
        console.log('🤖 PhotoVault TensorFlow.js Manager - AI functionality disabled');
        
        this.models = {
            cocoSSD: null,
            blazeFace: null,
            poseNet: null,
            deepLab: null
        };
        
        this.isLoading = false;
        this.loadedModels = new Set();
        this.modelLoadingPromises = new Map();
        
        // All AI features disabled
        this.config = {};
    }

    async initializeBackend() {
        console.log('ℹ️ TensorFlow.js backend disabled - AI functionality removed');
        return false;
    }

    async initializeModels(modelNames = []) {
        console.log('ℹ️ AI model loading disabled - AI functionality removed');
        this.isLoading = false;
        return false;
    }

    async loadCocoSSD() {
        console.log('ℹ️ COCO-SSD loading disabled - AI functionality removed');
        return null;
    }

    async loadBlazeFace() {
        console.log('ℹ️ BlazeFace loading disabled - AI functionality removed');
        return null;
    }

    async loadPoseNet() {
        console.log('ℹ️ PoseNet loading disabled - AI functionality removed');
        return null;
    }

    async loadDeepLab() {
        console.log('ℹ️ DeepLab loading disabled - AI functionality removed');
        return null;
    }

    // Disabled detection methods
    async detectObjects(imageElement) {
        console.log('ℹ️ Object detection disabled - AI functionality removed');
        return [];
    }

    async detectFaces(imageElement) {
        console.log('ℹ️ Face detection disabled - AI functionality removed');
        return [];
    }

    async estimatePoses(imageElement) {
        console.log('ℹ️ Pose estimation disabled - AI functionality removed');
        return [];
    }

    async segmentImage(imageElement) {
        console.log('ℹ️ Image segmentation disabled - AI functionality removed');
        return null;
    }

    // Status methods
    isModelLoaded(modelName) {
        return false;
    }

    isLoadingModels() {
        return false;
    }

    getLoadedModels() {
        return [];
    }

    // Cleanup methods
    dispose() {
        console.log('ℹ️ TensorFlow.js cleanup disabled - no models to dispose');
    }

    disposeModel(modelName) {
        console.log(`ℹ️ Model ${modelName} disposal disabled - AI functionality removed`);
    }
}

// Global instance - disabled but maintains compatibility
window.photoVaultTensorFlow = new PhotoVaultTensorFlowManager();

// Compatibility exports for existing code
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoVaultTensorFlowManager;
}