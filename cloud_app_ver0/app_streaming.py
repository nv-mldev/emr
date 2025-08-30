from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import base64
import io
from services.transcription_service import TranscriptionService
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

transcription_service = TranscriptionService()
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('streaming_index.html')

@socketio.on('start_recording')
def handle_start_recording():
    logger.info("Starting streaming transcription session")
    emit('recording_started', {'status': 'Recording started'})

@socketio.on('audio_data')
def handle_audio_data(data):
    try:
        # Get audio data from client
        audio_data = data['audio']
        
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
        
        # Process with streaming recognition (simplified)
        # In production, this would maintain a streaming connection
        logger.info(f"Received audio chunk: {len(audio_bytes)} bytes")
        
        # For now, emit back a placeholder transcription
        emit('transcription_update', {
            'text': 'Real-time transcription would appear here...',
            'is_final': False
        })
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        emit('error', {'message': str(e)})

@socketio.on('stop_recording')
def handle_stop_recording():
    logger.info("Stopping streaming transcription session")
    emit('recording_stopped', {'status': 'Recording stopped'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)