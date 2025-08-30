import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app):
    """
    Set up comprehensive logging for the application
    """
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Main application log
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    app_handler.setFormatter(log_format)
    app_handler.setLevel(logging.INFO)
    
    # Error log
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setFormatter(log_format)
    error_handler.setLevel(logging.ERROR)
    
    # Google Cloud API log
    gcp_log_file = os.path.join(log_dir, 'gcp_api.log')
    gcp_handler = logging.handlers.RotatingFileHandler(
        gcp_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    gcp_handler.setFormatter(log_format)
    gcp_handler.setLevel(logging.DEBUG)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    
    # Configure Flask app logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(app_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    
    # Configure Google Cloud loggers
    gcp_loggers = [
        'google.cloud.speech',
        'google.cloud.language',
        'google.auth',
        'google.api_core'
    ]
    
    for logger_name in gcp_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(gcp_handler)
    
    # Configure service loggers
    service_loggers = [
        'services.transcription_service',
        'services.nlp_service', 
        'services.report_generator'
    ]
    
    for logger_name in service_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(app_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)
    
    app.logger.info("Logging system initialized")
    app.logger.info(f"Log files: {app_log_file}, {error_log_file}, {gcp_log_file}")
    
    return app.logger

def log_request_info(app):
    """
    Log request information for debugging
    """
    from flask import request
    
    @app.before_request
    def log_request():
        app.logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")
        if request.is_json:
            app.logger.debug(f"JSON payload size: {len(str(request.get_json()))}")
    
    @app.after_request
    def log_response(response):
        app.logger.info(f"Response: {response.status_code} for {request.endpoint}")
        return response