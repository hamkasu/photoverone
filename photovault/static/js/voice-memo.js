/**
 * Voice Memo Recording Component for PhotoVault
 * Uses HTML5 MediaRecorder API for browser-based voice recording
 */

class VoiceMemoRecorder {
    constructor(photoId, containerId, options = {}) {
        this.photoId = photoId;
        this.containerId = containerId;
        this.options = {
            maxDuration: options.maxDuration || 300, // 5 minutes default
            audioBitsPerSecond: options.audioBitsPerSecond || 128000,
            mimeType: options.mimeType || null, // Auto-detect best format
            ...options
        };
        
        // Recording state
        this.isRecording = false;
        this.isPaused = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.recordingStartTime = null;
        this.recordingTimer = null;
        this.currentDuration = 0;
        
        // Initialize component
        this.init();
    }
    
    async init() {
        try {
            // Check browser support
            if (!this.checkBrowserSupport()) {
                this.showError('Your browser does not support voice recording. Please use Chrome, Firefox, or Edge.');
                return;
            }
            
            // Create UI
            this.createUI();
            
            // Bind events
            this.bindEvents();
            
            // Load existing voice memos
            await this.loadVoiceMemos();
            
        } catch (error) {
            console.error('Error initializing voice memo recorder:', error);
            this.showError('Failed to initialize voice recorder');
        }
    }
    
    checkBrowserSupport() {
        return !!(
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia &&
            window.MediaRecorder &&
            MediaRecorder.isTypeSupported
        );
    }
    
    createUI() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID ${this.containerId} not found`);
            return;
        }
        
        container.innerHTML = `
            <div class="voice-memo-recorder">
                <div class="recorder-header">
                    <h5><i class="bi bi-mic"></i> Voice Memos</h5>
                </div>
                
                <!-- Recording Controls -->
                <div class="recording-controls">
                    <button id="recordBtn" class="btn btn-danger btn-sm">
                        <i class="bi bi-mic"></i> Start Recording
                    </button>
                    <button id="stopBtn" class="btn btn-secondary btn-sm" disabled>
                        <i class="bi bi-stop"></i> Stop
                    </button>
                    <button id="pauseBtn" class="btn btn-warning btn-sm" disabled>
                        <i class="bi bi-pause"></i> Pause
                    </button>
                    <span id="recordingTimer" class="recording-timer">00:00</span>
                </div>
                
                <!-- Recording Status -->
                <div id="recordingStatus" class="recording-status d-none">
                    <div class="alert alert-info">
                        <i class="bi bi-record-circle text-danger"></i>
                        Recording... <span id="liveTimer">00:00</span>
                    </div>
                </div>
                
                <!-- Voice Memo Title Input -->
                <div id="memoMetadata" class="memo-metadata d-none">
                    <div class="mb-2">
                        <input type="text" id="memoTitle" class="form-control form-control-sm" 
                               placeholder="Enter memo title (optional)">
                    </div>
                    <div class="mb-2">
                        <button id="saveMemo" class="btn btn-success btn-sm">
                            <i class="bi bi-save"></i> Save Memo
                        </button>
                        <button id="discardMemo" class="btn btn-outline-danger btn-sm">
                            <i class="bi bi-trash"></i> Discard
                        </button>
                    </div>
                </div>
                
                <!-- Error Messages -->
                <div id="errorMessage" class="error-message d-none">
                    <div class="alert alert-danger"></div>
                </div>
                
                <!-- Voice Memo List -->
                <div class="voice-memo-list">
                    <div id="memoList"></div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Recording control buttons
        document.getElementById('recordBtn').addEventListener('click', () => this.startRecording());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopRecording());
        document.getElementById('pauseBtn').addEventListener('click', () => this.togglePause());
        
        // Save and discard buttons
        document.getElementById('saveMemo').addEventListener('click', () => this.saveMemo());
        document.getElementById('discardMemo').addEventListener('click', () => this.discardMemo());
    }
    
    async startRecording() {
        try {
            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                }
            });
            
            // Determine best MIME type
            const mimeType = this.getBestMimeType();
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: mimeType,
                audioBitsPerSecond: this.options.audioBitsPerSecond
            });
            
            // Setup event handlers
            this.setupMediaRecorderEvents();
            
            // Start recording
            this.mediaRecorder.start();
            
            // Update UI
            this.updateRecordingUI(true);
            
            // Start timer
            this.startTimer();
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.showError('Failed to start recording. Please check microphone permissions.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.stopTimer();
            
            // Stop audio stream
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
            }
            
            // Update UI
            this.updateRecordingUI(false);
        }
    }
    
    togglePause() {
        if (!this.mediaRecorder || !this.isRecording) return;
        
        if (this.isPaused) {
            this.mediaRecorder.resume();
            this.isPaused = false;
            document.getElementById('pauseBtn').innerHTML = '<i class="bi bi-pause"></i> Pause';
            this.startTimer();
        } else {
            this.mediaRecorder.pause();
            this.isPaused = true;
            document.getElementById('pauseBtn').innerHTML = '<i class="bi bi-play"></i> Resume';
            this.stopTimer();
        }
    }
    
    setupMediaRecorderEvents() {
        this.audioChunks = [];
        
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };
        
        this.mediaRecorder.onstart = () => {
            this.isRecording = true;
            console.log('Recording started');
        };
        
        this.mediaRecorder.onstop = () => {
            this.isRecording = false;
            this.isPaused = false;
            this.processRecording();
            console.log('Recording stopped');
        };
        
        this.mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            this.showError('Recording error occurred');
        };
    }
    
    processRecording() {
        if (this.audioChunks.length === 0) {
            this.showError('No audio data recorded');
            return;
        }
        
        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { type: this.mediaRecorder.mimeType });
        
        // Create audio URL for preview
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Show metadata input
        this.showMemoMetadata(audioBlob, audioUrl);
    }
    
    showMemoMetadata(audioBlob, audioUrl) {
        // Show metadata input section
        document.getElementById('memoMetadata').classList.remove('d-none');
        
        // Store for later use
        this.currentRecording = {
            blob: audioBlob,
            url: audioUrl,
            duration: this.currentDuration
        };
        
        // Focus on title input
        document.getElementById('memoTitle').focus();
    }
    
    async saveMemo() {
        if (!this.currentRecording) {
            this.showError('No recording to save');
            return;
        }
        
        try {
            const title = document.getElementById('memoTitle').value.trim();
            
            // Create FormData for upload
            const formData = new FormData();
            formData.append('audio', this.currentRecording.blob, 'voice_memo.webm');
            formData.append('title', title);
            formData.append('duration', this.currentRecording.duration);
            
            // Show saving status
            this.showSavingStatus();
            
            // Upload to server
            const response = await fetch(`/api/photos/${this.photoId}/voice-memos`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Voice memo saved successfully!');
                this.resetRecorder();
                await this.loadVoiceMemos(); // Refresh list
            } else {
                this.showError(result.error || 'Failed to save voice memo');
            }
            
        } catch (error) {
            console.error('Error saving voice memo:', error);
            this.showError('Failed to save voice memo');
        } finally {
            this.hideSavingStatus();
        }
    }
    
    discardMemo() {
        if (this.currentRecording) {
            URL.revokeObjectURL(this.currentRecording.url);
            this.currentRecording = null;
        }
        
        this.resetRecorder();
    }
    
    resetRecorder() {
        // Reset UI
        document.getElementById('memoMetadata').classList.add('d-none');
        document.getElementById('memoTitle').value = '';
        
        // Reset state
        this.audioChunks = [];
        this.currentRecording = null;
        this.currentDuration = 0;
        
        // Update timer display
        document.getElementById('recordingTimer').textContent = '00:00';
    }
    
    async loadVoiceMemos() {
        try {
            const response = await fetch(`/api/photos/${this.photoId}/voice-memos`);
            const result = await response.json();
            
            if (result.success) {
                this.renderVoiceMemos(result.voice_memos);
            } else {
                console.error('Failed to load voice memos:', result.error);
            }
            
        } catch (error) {
            console.error('Error loading voice memos:', error);
        }
    }
    
    renderVoiceMemos(voiceMemos) {
        const memoList = document.getElementById('memoList');
        
        if (voiceMemos.length === 0) {
            memoList.innerHTML = '<p class="text-muted small">No voice memos yet. Record one above!</p>';
            return;
        }
        
        memoList.innerHTML = voiceMemos.map(memo => `
            <div class="voice-memo-item" data-memo-id="${memo.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="memo-info flex-grow-1">
                        <div class="memo-title">
                            ${memo.title ? `<strong>${this.escapeHtml(memo.title)}</strong>` : '<em>Untitled memo</em>'}
                        </div>
                        <div class="memo-meta text-muted small">
                            <i class="bi bi-clock"></i> ${memo.duration_formatted} • 
                            <i class="bi bi-file-earmark"></i> ${memo.file_size_mb}MB • 
                            ${this.formatDate(memo.created_at)}
                        </div>
                        <div class="memo-controls mt-1">
                            <button class="btn btn-outline-primary btn-sm play-memo" data-memo-id="${memo.id}">
                                <i class="bi bi-play"></i> Play
                            </button>
                            <button class="btn btn-outline-danger btn-sm delete-memo" data-memo-id="${memo.id}">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
                <audio class="memo-audio d-none" data-memo-id="${memo.id}" controls>
                    <source src="/api/voice-memos/${memo.id}" type="${memo.mime_type || 'audio/webm'}">
                    Your browser does not support audio playback.
                </audio>
            </div>
        `).join('');
        
        // Bind events for memo controls
        this.bindMemoEvents();
    }
    
    bindMemoEvents() {
        // Play/pause buttons
        document.querySelectorAll('.play-memo').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const memoId = e.target.closest('.play-memo').dataset.memoId;
                this.toggleMemoPlayback(memoId);
            });
        });
        
        // Delete buttons
        document.querySelectorAll('.delete-memo').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const memoId = e.target.closest('.delete-memo').dataset.memoId;
                this.deleteMemo(memoId);
            });
        });
    }
    
    toggleMemoPlayback(memoId) {
        const audio = document.querySelector(`audio[data-memo-id="${memoId}"]`);
        const playBtn = document.querySelector(`.play-memo[data-memo-id="${memoId}"]`);
        
        if (!audio || !playBtn) return;
        
        if (audio.paused) {
            // Pause all other audios
            document.querySelectorAll('.memo-audio').forEach(otherAudio => {
                if (otherAudio !== audio) {
                    otherAudio.pause();
                }
            });
            
            // Reset all play buttons
            document.querySelectorAll('.play-memo').forEach(btn => {
                btn.innerHTML = '<i class="bi bi-play"></i> Play';
            });
            
            // Play this audio
            audio.play();
            playBtn.innerHTML = '<i class="bi bi-pause"></i> Pause';
            
            // Update button when audio ends
            audio.onended = () => {
                playBtn.innerHTML = '<i class="bi bi-play"></i> Play';
            };
            
        } else {
            audio.pause();
            playBtn.innerHTML = '<i class="bi bi-play"></i> Play';
        }
    }
    
    async deleteMemo(memoId) {
        if (!confirm('Are you sure you want to delete this voice memo?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/voice-memos/${memoId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Voice memo deleted successfully!');
                await this.loadVoiceMemos(); // Refresh list
            } else {
                this.showError(result.error || 'Failed to delete voice memo');
            }
            
        } catch (error) {
            console.error('Error deleting voice memo:', error);
            this.showError('Failed to delete voice memo');
        }
    }
    
    // Utility methods
    
    getBestMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/wav'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return 'audio/webm'; // fallback
    }
    
    updateRecordingUI(recording) {
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const status = document.getElementById('recordingStatus');
        
        if (recording) {
            recordBtn.disabled = true;
            stopBtn.disabled = false;
            pauseBtn.disabled = false;
            status.classList.remove('d-none');
        } else {
            recordBtn.disabled = false;
            stopBtn.disabled = true;
            pauseBtn.disabled = true;
            status.classList.add('d-none');
        }
    }
    
    startTimer() {
        this.recordingStartTime = Date.now() - (this.currentDuration * 1000);
        this.recordingTimer = setInterval(() => {
            this.currentDuration = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const formatted = this.formatDuration(this.currentDuration);
            document.getElementById('recordingTimer').textContent = formatted;
            document.getElementById('liveTimer').textContent = formatted;
            
            // Stop at max duration
            if (this.currentDuration >= this.options.maxDuration) {
                this.stopRecording();
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }
    
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    getCSRFToken() {
        return document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
    }
    
    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.querySelector('.alert').textContent = message;
        errorDiv.classList.remove('d-none');
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorDiv.classList.add('d-none');
        }, 5000);
    }
    
    showSuccess(message) {
        // Create success alert
        const container = document.querySelector('.voice-memo-recorder');
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success';
        successDiv.innerHTML = `<i class="bi bi-check-circle"></i> ${message}`;
        
        container.insertBefore(successDiv, container.firstChild);
        
        // Remove after 3 seconds
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }
    
    showSavingStatus() {
        const saveBtn = document.getElementById('saveMemo');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
    }
    
    hideSavingStatus() {
        const saveBtn = document.getElementById('saveMemo');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-save"></i> Save Memo';
    }
}

// Export for use in other modules
window.VoiceMemoRecorder = VoiceMemoRecorder;