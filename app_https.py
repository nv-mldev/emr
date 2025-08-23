from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from services.transcription_service import TranscriptionService
from services.nlp_service import NLPService
from services.report_generator import ReportGenerator
import tempfile
import json
import ssl

load_dotenv()

app = Flask(__name__)
CORS(app)

transcription_service = TranscriptionService()
nlp_service = NLPService()
report_generator = ReportGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            
            transcription = transcription_service.transcribe_audio(temp_file.name)
            
            os.unlink(temp_file.name)
            
            return jsonify({'transcription': transcription})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        transcription = data.get('transcription', '')
        
        if not transcription:
            return jsonify({'error': 'No transcription provided'}), 400
        
        entities = nlp_service.extract_entities(transcription)
        
        structured_data = nlp_service.structure_data(entities, transcription)
        
        report = report_generator.generate_report(structured_data)
        
        return jsonify({
            'structured_data': structured_data,
            'report': report
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Create a self-signed SSL context for development
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('cert.pem', 'key.pem')
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context='adhoc')