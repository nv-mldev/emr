import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymongo
from bson import ObjectId
from pydub import AudioSegment
import requests
from dotenv import load_dotenv
from celery import Celery
from google.cloud import speech
from google.cloud import storage
import io

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
client = pymongo.MongoClient(os.getenv('MONGODB_URL', 'mongodb://localhost:27017'))
db = client['medical_dictation']

# Celery configuration for async processing
celery = Celery(
    app.import_name,
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

# Google Cloud Speech client
try:
    speech_client = speech.SpeechClient()
    logger.info("Google Cloud Speech client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Google Cloud Speech client: {str(e)}")
    speech_client = None

# Google Cloud Storage client (optional for large files)
try:
    storage_client = storage.Client()
    BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
    if BUCKET_NAME:
        bucket = storage_client.bucket(BUCKET_NAME)
    else:
        bucket = None
    logger.info("Google Cloud Storage client initialized")
except Exception as e:
    logger.warning(f"Google Cloud Storage not configured: {str(e)}")
    storage_client = None
    bucket = None

# Service URLs
UPLOAD_SERVICE_URL = os.getenv('UPLOAD_SERVICE_URL', 'http://localhost:5003')
PATIENT_SERVICE_URL = os.getenv('PATIENT_SERVICE_URL', 'http://localhost:5002')

@app.route('/health', methods=['GET'])
def health_check():
    speech_status = "connected" if speech_client else "failed"
    storage_status = "connected" if storage_client else "not_configured"
    
    return jsonify({
        "status": "healthy",
        "service": "speech-service",
        "google_speech_api": speech_status,
        "google_storage": storage_status
    }), 200

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Start medical audio transcription process"""
    try:
        data = request.json
        audio_file_id = data.get('audio_file_id')
        file_path = data.get('file_path')
        doctor_id = data.get('doctor_id')
        patient_context = data.get('patient_context', {})
        
        if not all([audio_file_id, file_path, doctor_id]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({"error": "Audio file not found"}), 404
        
        if not speech_client:
            return jsonify({"error": "Speech service not available"}), 503
        
        # Create transcription record
        transcription = {
            "audio_file_id": ObjectId(audio_file_id),
            "doctor_id": ObjectId(doctor_id),
            "patient_context": patient_context,
            "processing_status": "processing",
            "created_at": datetime.utcnow()
        }
        
        transcription_id = db.transcriptions.insert_one(transcription).inserted_id
        
        # Start async transcription
        transcribe_medical_audio_task.delay(
            str(transcription_id),
            file_path,
            audio_file_id,
            doctor_id,
            patient_context
        )
        
        return jsonify({
            "status": "processing",
            "transcription_id": str(transcription_id)
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting transcription: {str(e)}")
        return jsonify({"error": "Failed to start transcription"}), 500

@celery.task
def transcribe_medical_audio_task(transcription_id, file_path, audio_file_id, doctor_id, patient_context):
    """Async task to transcribe medical audio using Google Speech API"""
    try:
        logger.info(f"Starting medical transcription for file: {file_path}")
        
        # Update status to processing
        db.transcriptions.update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {"processing_status": "processing"}}
        )
        
        # Preprocess audio for Google Speech API
        processed_audio_data = preprocess_audio_for_google(file_path)
        
        if not processed_audio_data:
            raise Exception("Failed to preprocess audio file")
        
        # Configure Google Speech recognition for medical content
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            
            # Medical-specific configurations
            model="medical_dictation",  # Use medical dictation model
            use_enhanced=True,  # Use enhanced model for better accuracy
            enable_automatic_punctuation=True,
            enable_speaker_diarization=True,
            diarization_speaker_count=2,  # Doctor and potentially patient
            
            # Medical vocabulary and context
            speech_contexts=[
                speech.SpeechContext(
                    phrases=[
                        # Common medical terms and abbreviations
                        "blood pressure", "heart rate", "respiratory rate", "temperature",
                        "chief complaint", "history of present illness", "past medical history",
                        "review of systems", "physical examination", "assessment and plan",
                        "diagnosis", "prescription", "medication", "dosage", "mg", "ml",
                        "hypertension", "diabetes", "cardiovascular", "pulmonary",
                        "gastrointestinal", "neurological", "dermatological"
                    ],
                    boost=20.0  # Boost recognition of these medical terms
                )
            ],
            
            # Additional medical configurations
            enable_word_time_offsets=True,
            enable_word_confidence=True,
            metadata=speech.RecognitionMetadata(
                interaction_type=speech.RecognitionMetadata.InteractionType.DICTATION,
                industry_naics_code_of_audio=621111,  # Offices of Physicians
                microphone_distance=speech.RecognitionMetadata.MicrophoneDistance.NEARFIELD,
                original_media_type=speech.RecognitionMetadata.OriginalMediaType.AUDIO,
                recording_device_type=speech.RecognitionMetadata.RecordingDeviceType.SMARTPHONE
            )
        )
        
        # Create audio object
        audio = speech.RecognitionAudio(content=processed_audio_data)
        
        # Perform the transcription
        logger.info("Performing medical transcription with Google Speech API...")
        
        if len(processed_audio_data) > 10 * 1024 * 1024:  # > 10MB, use long running operation
            operation = speech_client.long_running_recognize(config=config, audio=audio)
            logger.info("Using long running recognition for large file...")
            response = operation.result(timeout=300)  # 5 minutes timeout
        else:
            response = speech_client.recognize(config=config, audio=audio)
        
        # Process results
        if not response.results:
            raise Exception("No transcription results received")
        
        # Extract transcription and confidence
        full_transcript = ""
        word_details = []
        overall_confidence = 0.0
        confidence_count = 0
        
        for result in response.results:
            alternative = result.alternatives[0]
            full_transcript += alternative.transcript + " "
            
            if hasattr(alternative, 'confidence'):
                overall_confidence += alternative.confidence
                confidence_count += 1
            
            # Extract word-level details
            if hasattr(alternative, 'words'):
                for word_info in alternative.words:
                    word_details.append({
                        "word": word_info.word,
                        "confidence": getattr(word_info, 'confidence', 0.0),
                        "start_time": word_info.start_time.total_seconds(),
                        "end_time": word_info.end_time.total_seconds()
                    })
        
        # Calculate average confidence
        avg_confidence = overall_confidence / confidence_count if confidence_count > 0 else 0.0
        
        raw_text = full_transcript.strip()
        
        # Post-process for medical context
        processed_text = post_process_medical_transcription(raw_text, patient_context)
        
        # Update transcription in database
        db.transcriptions.update_one(
            {"_id": ObjectId(transcription_id)},
            {
                "$set": {
                    "raw_text": raw_text,
                    "processed_text": processed_text,
                    "confidence_score": avg_confidence,
                    "word_details": word_details,
                    "processing_status": "completed",
                    "processed_at": datetime.utcnow(),
                    "model_used": "google_medical_dictation"
                }
            }
        )
        
        # Get or create patient record
        patient_info = get_or_create_patient(doctor_id, processed_text, patient_context)
        
        # Save to patient's history
        save_to_patient_history(patient_info["_id"], transcription_id, processed_text)
        
        # Notify other services
        notify_transcription_complete(doctor_id, transcription_id, processed_text, patient_info)
        
        logger.info(f"Medical transcription completed successfully: {transcription_id}")
        
    except Exception as e:
        logger.error(f"Error in medical transcription task: {str(e)}")
        
        # Update status to failed
        db.transcriptions.update_one(
            {"_id": ObjectId(transcription_id)},
            {
                "$set": {
                    "processing_status": "failed",
                    "error_message": str(e),
                    "processed_at": datetime.utcnow()
                }
            }
        )

def preprocess_audio_for_google(file_path):
    """Convert audio to format suitable for Google Speech API"""
    try:
        # Load audio with pydub
        audio = AudioSegment.from_file(file_path)
        
        # Convert to format required by Google Speech API
        # - 16kHz sample rate
        # - 16-bit PCM
        # - Mono channel
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)  # 16-bit
        
        # Export to bytes
        audio_data = io.BytesIO()
        audio.export(audio_data, format="wav")
        
        return audio_data.getvalue()
        
    except Exception as e:
        logger.error(f"Audio preprocessing failed: {str(e)}")
        return None

def post_process_medical_transcription(text, patient_context):
    """Enhanced post-processing for medical transcriptions"""
    try:
        processed = text.strip()
        
        # Capitalize sentences
        sentences = processed.split('. ')
        processed = '. '.join([s.strip().capitalize() if s else s for s in sentences])
        
        # Medical abbreviations standardization
        medical_corrections = {
            # Vital signs
            ' bp ': ' blood pressure ',
            ' hr ': ' heart rate ',
            ' rr ': ' respiratory rate ',
            ' temp ': ' temperature ',
            ' o2 sat ': ' oxygen saturation ',
            
            # Medical history sections
            ' cc ': ' chief complaint ',
            ' hpi ': ' history of present illness ',
            ' pmh ': ' past medical history ',
            ' psh ': ' past surgical history ',
            ' fh ': ' family history ',
            ' sh ': ' social history ',
            ' ros ': ' review of systems ',
            ' pe ': ' physical examination ',
            ' a&p ': ' assessment and plan ',
            
            # Common medical terms
            ' h/o ': ' history of ',
            ' w/ ': ' with ',
            ' w/o ': ' without ',
            ' s/p ': ' status post ',
            ' r/o ': ' rule out ',
            
            # Units standardization
            ' mg ': ' milligrams ',
            ' ml ': ' milliliters ',
            ' mcg ': ' micrograms ',
            ' iu ': ' international units ',
        }
        
        text_lower = processed.lower()
        for abbrev, full_form in medical_corrections.items():
            text_lower = text_lower.replace(abbrev, full_form)
        
        # Format common medication dosages
        import re
        dosage_pattern = r'(\d+(?:\.\d+)?)\s*(mg|milligrams|ml|milliliters|mcg|micrograms)'
        processed = re.sub(dosage_pattern, r'\1 \2', text_lower, flags=re.IGNORECASE)
        
        # Add patient context if available
        if patient_context and patient_context.get('patient_id'):
            processed = f"Patient ID: {patient_context['patient_id']}\n\n{processed}"
        
        return processed.strip()
        
    except Exception as e:
        logger.warning(f"Error in medical post-processing: {str(e)}")
        return text

def get_or_create_patient(doctor_id, transcription_text, patient_context):
    """Enhanced patient management with medical context"""
    try:
        # Use provided patient context or create anonymous
        patient_name = patient_context.get('name', 'Anonymous Patient')
        patient_id_hint = patient_context.get('patient_id', None)
        
        # Look for existing patient
        if patient_id_hint:
            existing_patient = db.patients.find_one({
                "doctor_id": ObjectId(doctor_id),
                "patient_id": patient_id_hint
            })
            if existing_patient:
                return existing_patient
        
        # Create new patient record
        patient = {
            "patient_id": patient_id_hint or f"MED_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "doctor_id": ObjectId(doctor_id),
            "name": patient_name,
            "created_at": datetime.utcnow(),
            "last_transcription": datetime.utcnow()
        }
        
        patient_obj_id = db.patients.insert_one(patient).inserted_id
        patient["_id"] = patient_obj_id
        
        return patient
        
    except Exception as e:
        logger.error(f"Error managing patient record: {str(e)}")
        return {"_id": None, "patient_id": "ERROR", "name": "Unknown"}

def save_to_patient_history(patient_id, transcription_id, processed_text):
    """Save transcription to patient's medical history"""
    try:
        if patient_id:
            db.transcriptions.update_one(
                {"_id": ObjectId(transcription_id)},
                {"$set": {"patient_id": ObjectId(patient_id)}}
            )
            
            # Update patient's last transcription date
            db.patients.update_one(
                {"_id": ObjectId(patient_id)},
                {"$set": {"last_transcription": datetime.utcnow()}}
            )
    except Exception as e:
        logger.error(f"Error saving to patient history: {str(e)}")

def notify_transcription_complete(doctor_id, transcription_id, processed_text, patient_info):
    """Notify other services about completed transcription"""
    try:
        # This could notify the frontend via websockets, send emails, etc.
        logger.info(f"Transcription {transcription_id} completed for doctor {doctor_id}")
        
        # Future: Add real-time notifications here
        
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")

@app.route('/transcription/<transcription_id>', methods=['GET'])
def get_transcription(transcription_id):
    """Get transcription status and result"""
    try:
        transcription = db.transcriptions.find_one({"_id": ObjectId(transcription_id)})
        if not transcription:
            return jsonify({"error": "Transcription not found"}), 404
        
        # Convert ObjectIds to strings for JSON serialization
        transcription['_id'] = str(transcription['_id'])
        transcription['audio_file_id'] = str(transcription['audio_file_id'])
        transcription['doctor_id'] = str(transcription['doctor_id'])
        if 'patient_id' in transcription:
            transcription['patient_id'] = str(transcription['patient_id'])
        
        return jsonify(transcription), 200
        
    except Exception as e:
        logger.error(f"Error retrieving transcription: {str(e)}")
        return jsonify({"error": "Failed to retrieve transcription"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)