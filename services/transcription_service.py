from google.cloud import speech
import os
import logging
import traceback

class TranscriptionService:
    def __init__(self):
        self.client = speech.SpeechClient()
        self.logger = logging.getLogger('services.transcription_service')
        self.logger.info("TranscriptionService initialized")
        
    def transcribe_audio(self, audio_file_path):
        self.logger.info(f"Starting transcription for file: {audio_file_path}")
        
        try:
            with open(audio_file_path, 'rb') as audio_file:
                content = audio_file.read()
                
            file_size = len(content)
            self.logger.info(f"Audio file size: {file_size} bytes")
            
            if file_size == 0:
                raise Exception("Audio file is empty")
            
            # Use appropriate method based on file size
            if file_size > 10000000:  # 10MB limit for long running
                self.logger.info("Very large file detected, using long running recognition")
                return self._transcribe_long_running(audio_file_path)
            elif file_size > 500000:  # 500KB - 10MB use chunked processing
                self.logger.info("Large file detected, using chunked processing")
                return self._transcribe_chunked(content)
            else:
                self.logger.info("Small file, using synchronous recognition")
                return self._transcribe_sync(content)
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {str(e)}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _transcribe_sync(self, content):
        """Handle short audio with synchronous recognition"""
        configs_to_try = [
            # Configuration 1: Medical model with auto-detect
            speech.RecognitionConfig(
                language_code="en-US",
                model="medical_dictation",
                use_enhanced=True,
                enable_automatic_punctuation=True,
                enable_spoken_punctuation=True,
            ),
            # Configuration 2: WEBM_OPUS with medical model
            speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
                model="medical_dictation",
                use_enhanced=True,
                enable_automatic_punctuation=True,
            ),
            # Configuration 3: Latest short model
            speech.RecognitionConfig(
                language_code="en-US",
                model="latest_short", 
                use_enhanced=True,
                enable_automatic_punctuation=True,
            ),
        ]
        
        audio = speech.RecognitionAudio(content=content)
        
        for i, config in enumerate(configs_to_try):
            try:
                self.logger.info(f"Trying sync config {i+1}: {getattr(config, 'model', 'default')}")
                
                response = self.client.recognize(config=config, audio=audio)
                
                transcription = ""
                for result in response.results:
                    transcription += result.alternatives[0].transcript + " "
                
                if transcription.strip():
                    self.logger.info(f"Sync transcription successful with config {i+1}")
                    return transcription.strip()
                    
            except Exception as e:
                self.logger.warning(f"Sync config {i+1} failed: {str(e)}")
                continue
        
        raise Exception("All synchronous transcription configurations failed")
    
    def _transcribe_chunked(self, content):
        """Handle medium-sized audio by chunking"""
        self.logger.info("Processing audio in chunks")
        
        # Simple chunking - split audio into ~500KB chunks
        chunk_size = 400000  # 400KB chunks
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        self.logger.info(f"Split audio into {len(chunks)} chunks")
        
        full_transcription = ""
        
        for i, chunk in enumerate(chunks):
            try:
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} bytes)")
                
                chunk_transcription = self._transcribe_sync(chunk)
                if chunk_transcription:
                    full_transcription += chunk_transcription + " "
                    
            except Exception as e:
                self.logger.warning(f"Chunk {i+1} failed: {str(e)}")
                continue
        
        if not full_transcription.strip():
            raise Exception("All audio chunks failed to transcribe")
            
        self.logger.info(f"Chunked transcription completed: {len(full_transcription)} characters")
        return full_transcription.strip()
    
    def _transcribe_long_running(self, audio_file_path):
        """Handle very large files with long running recognition"""
        self.logger.info("Using long running recognition for very large file")
        
        # For production, upload to Google Cloud Storage
        # For now, return helpful error
        raise Exception("Very large audio files (>10MB) require Google Cloud Storage integration. Please break into smaller segments or contact support.")
    
    def _transcribe_long_audio(self, audio_file_path):
        """Handle long audio files using LongRunningRecognize"""
        self.logger.info("Using long running recognition for large audio file")
        
        # Upload to Google Cloud Storage would be ideal, but for now we'll try chunking
        # For production, implement GCS upload and use uri parameter
        raise Exception("Audio file too long (>1 minute). Please record shorter segments or implement GCS upload for long files.")
    
    def stream_transcribe_audio(self, audio_generator):
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            model="medical_dictation",
            use_enhanced=True,
            enable_automatic_punctuation=True,
        )
        
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )
        
        audio_generator = (speech.StreamingRecognizeRequest(audio_content=chunk)
                          for chunk in audio_generator)
        
        requests = iter([speech.StreamingRecognizeRequest(
            streaming_config=streaming_config)] + list(audio_generator))
        
        responses = self.client.streaming_recognize(requests)
        
        for response in responses:
            for result in response.results:
                if result.is_final:
                    yield result.alternatives[0].transcript