from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import logging
import traceback
from dotenv import load_dotenv
from services.transcription_service import TranscriptionService
from services.nlp_service import NLPService
from services.report_generator import ReportGenerator
from config.logging_config import setup_logging, log_request_info
import tempfile
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# Set up logging
logger = setup_logging(app)
log_request_info(app)

transcription_service = TranscriptionService()
nlp_service = NLPService()
report_generator = ReportGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    temp_file_path = None
    try:
        logger.info("Transcription request received")
        
        if 'audio' not in request.files:
            logger.warning("No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        logger.info(f"Audio file received: {audio_file.filename}, size: {audio_file.content_length}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file_path = temp_file.name
            audio_file.save(temp_file_path)
            logger.debug(f"Audio saved to temporary file: {temp_file_path}")
            
            logger.info("Starting transcription process")
            transcription = transcription_service.transcribe_audio(temp_file_path)
            logger.info(f"Transcription completed: {len(transcription)} characters")
            
            return jsonify({'transcription': transcription})
    
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500
    
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        logger.info("Report generation request received")
        
        data = request.get_json()
        if not data:
            logger.warning("No JSON data in request")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        transcription = data.get('transcription', '')
        logger.info(f"Processing transcription: {len(transcription)} characters")
        
        if not transcription:
            logger.warning("Empty transcription provided")
            return jsonify({'error': 'No transcription provided'}), 400
        
        logger.info("Starting NLP entity extraction")
        entities = nlp_service.extract_entities(transcription)
        logger.info(f"Extracted {len(entities)} entities")
        
        logger.info("Structuring extracted data")
        structured_data = nlp_service.structure_data(entities, transcription)
        
        logger.info("Generating final report")
        report = report_generator.generate_report(structured_data)
        logger.info("Report generation completed successfully")
        
        return jsonify({
            'structured_data': structured_data,
            'report': report
        })
    
    except Exception as e:
        error_msg = f"Report generation failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/api/log-error', methods=['POST'])
def log_frontend_error():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No error data provided'}), 400
            
        error_message = data.get('message', 'Unknown error')
        context = data.get('context', 'Unknown context')
        timestamp = data.get('timestamp', 'Unknown timestamp')
        user_agent = data.get('userAgent', 'Unknown user agent')
        url = data.get('url', 'Unknown URL')
        stack = data.get('stack', 'No stack trace')
        
        logger.error(f"FRONTEND ERROR - Context: {context}")
        logger.error(f"Message: {error_message}")
        logger.error(f"URL: {url}")
        logger.error(f"User Agent: {user_agent}")
        logger.error(f"Timestamp: {timestamp}")
        logger.error(f"Stack Trace: {stack}")
        
        return jsonify({'status': 'logged'})
        
    except Exception as e:
        logger.error(f"Failed to log frontend error: {str(e)}")
        return jsonify({'error': 'Failed to log error'}), 500

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error for {request.url}")
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    logger.warning(f"405 error: {request.method} not allowed for {request.url}")
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Pediatric EMR Speech-to-Report Application")
    logger.info("Server starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)