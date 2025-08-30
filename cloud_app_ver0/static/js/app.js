class SpeechToReportApp {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingTime = 0;
        this.recordingInterval = null;
        this.currentTranscription = '';
        this.currentReport = null;
        
        this.initializeElements();
        this.bindEvents();
        this.checkBrowserSupport();
    }
    
    initializeElements() {
        this.startBtn = document.getElementById('startRecord');
        this.stopBtn = document.getElementById('stopRecord');
        this.generateBtn = document.getElementById('generateReport');
        this.exportJsonBtn = document.getElementById('exportJson');
        this.exportTextBtn = document.getElementById('exportText');
        
        this.statusSpan = document.getElementById('recordingStatus');
        this.timeDiv = document.getElementById('recordingTime');
        this.transcriptionArea = document.getElementById('transcriptionArea');
        this.jsonOutput = document.getElementById('jsonOutput');
        this.reportOutput = document.getElementById('reportOutput');
    }
    
    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.generateBtn.addEventListener('click', () => this.generateReport());
        this.exportJsonBtn.addEventListener('click', () => this.exportJson());
        this.exportTextBtn.addEventListener('click', () => this.exportText());
    }
    
    checkBrowserSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showError('Your browser does not support audio recording. Please use Chrome, Firefox, or Safari.');
            this.startBtn.disabled = true;
            return;
        }
        
        // Check if we're on HTTPS or localhost
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            this.showError('Voice recording requires HTTPS or localhost. Please use https:// or access via localhost.');
            this.startBtn.disabled = true;
            return;
        }
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 44100,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            // Try to use WAV format if supported, fallback to webm
            let options = { mimeType: 'audio/webm' };
            if (MediaRecorder.isTypeSupported('audio/wav')) {
                options = { mimeType: 'audio/wav' };
            } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                options = { mimeType: 'audio/webm;codecs=opus' };
            }
            
            this.mediaRecorder = new MediaRecorder(stream, options);
            this.audioChunks = [];
            
            console.log('Recording with format:', options.mimeType);
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processAudio();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordingTime = 0;
            
            this.updateUI();
            this.startTimer();
            
        } catch (error) {
            this.logError(error, 'Microphone Access');
            this.showError('Error accessing microphone: ' + error.message);
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        this.isRecording = false;
        this.stopTimer();
        this.updateUI();
    }
    
    startTimer() {
        this.recordingInterval = setInterval(() => {
            this.recordingTime++;
            this.updateTimer();
        }, 1000);
    }
    
    stopTimer() {
        if (this.recordingInterval) {
            clearInterval(this.recordingInterval);
            this.recordingInterval = null;
        }
    }
    
    updateTimer() {
        const minutes = Math.floor(this.recordingTime / 60);
        const seconds = this.recordingTime % 60;
        this.timeDiv.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Auto-stop at 5 minutes for practical reasons
        if (this.recordingTime >= 300) { // 5 minutes
            this.timeDiv.style.color = '#dc3545';
            if (this.recordingTime === 300) {
                console.warn('Maximum recording length reached (5 minutes). Auto-stopping...');
                this.stopRecording();
                alert('Recording automatically stopped at 5 minutes. For longer dictations, please record in segments.');
            }
        }
        // Warn at 4.5 minutes
        else if (this.recordingTime >= 270) { // 4.5 minutes
            this.timeDiv.style.color = '#ff8c00';
            if (this.recordingTime === 270) {
                console.warn('Recording will auto-stop in 30 seconds...');
            }
        }
        // Show info at 2 minutes
        else if (this.recordingTime >= 120) { // 2 minutes
            this.timeDiv.style.color = '#ffc107';
        }
    }
    
    updateUI() {
        if (this.isRecording) {
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.generateBtn.disabled = true;
            this.statusSpan.textContent = 'Recording...';
            this.statusSpan.classList.add('recording');
        } else {
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            this.generateBtn.disabled = !this.currentTranscription;
            this.statusSpan.textContent = 'Ready to record';
            this.statusSpan.classList.remove('recording');
        }
    }
    
    async processAudio() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        this.transcriptionArea.textContent = 'Transcribing audio...';
        this.transcriptionArea.classList.add('loading');
        
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.currentTranscription = data.transcription;
            this.transcriptionArea.textContent = this.currentTranscription;
            this.generateBtn.disabled = false;
            
        } catch (error) {
            this.logError(error, 'Audio Transcription');
            this.showError('Error transcribing audio: ' + error.message);
            this.transcriptionArea.textContent = 'Error transcribing audio. Please try again.';
        } finally {
            this.transcriptionArea.classList.remove('loading');
        }
    }
    
    async generateReport() {
        if (!this.currentTranscription) {
            this.showError('No transcription available to generate report.');
            return;
        }
        
        this.jsonOutput.textContent = 'Processing transcription...';
        this.reportOutput.textContent = 'Generating report...';
        this.generateBtn.disabled = true;
        this.generateBtn.classList.add('loading');
        
        try {
            const response = await fetch('/api/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transcription: this.currentTranscription
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.currentReport = data;
            
            this.jsonOutput.textContent = JSON.stringify(data.structured_data, null, 2);
            this.reportOutput.textContent = data.report.discharge_summary;
            
            this.exportJsonBtn.disabled = false;
            this.exportTextBtn.disabled = false;
            
        } catch (error) {
            this.logError(error, 'Report Generation');
            this.showError('Error generating report: ' + error.message);
            this.jsonOutput.textContent = 'Error generating structured data.';
            this.reportOutput.textContent = 'Error generating report.';
        } finally {
            this.generateBtn.disabled = false;
            this.generateBtn.classList.remove('loading');
        }
    }
    
    exportJson() {
        if (!this.currentReport) return;
        
        const dataStr = JSON.stringify(this.currentReport.structured_data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `medical-report-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }
    
    exportText() {
        if (!this.currentReport) return;
        
        const textBlob = new Blob([this.currentReport.report.discharge_summary], { type: 'text/plain' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(textBlob);
        link.download = `discharge-summary-${new Date().toISOString().split('T')[0]}.txt`;
        link.click();
    }
    
    logError(error, context = '') {
        const errorData = {
            message: error.message || error,
            stack: error.stack || 'No stack trace',
            context: context,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        console.error('Frontend Error:', errorData);
        
        // Send error to backend for logging
        fetch('/api/log-error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(errorData)
        }).catch(e => console.error('Failed to send error to backend:', e));
    }
    
    showError(message) {
        this.logError(message, 'User Error');
        alert('Error: ' + message);
        console.error(message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SpeechToReportApp();
});