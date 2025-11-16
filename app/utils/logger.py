import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """
    Configure logging: stream to CLI (stdout) and rotate to file at /logs/app.log.
    Called this from create_app() after app.config is loaded.
    """

    # Get log level from config or default to INFO
    log_level_name = app.config.get('LOG_LEVEL','INFO').upper()
    log_level = getattr(logging,log_level_name,logging.INFO)

    #Formatting in logs file
    fmt = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    formatter = logging.Formatter(fmt)

    # Get logs file path from config
    log_file_path = app.config.get('LOG_FILE','logs/app.log')

    # Get absolute file path of logs file
    project_root = os.path.dirname(app.root_path)
    full_log_path = os.path.join(project_root, log_file_path)
    
    # Ensures logs directory exists
    log_dir = os.path.dirname(full_log_path)
    os.makedirs(log_dir, exist_ok=True)

    # Create log handlers
    # File handler (rotating) - 5MB max, keep 5 backup files
    file_handler = RotatingFileHandler(full_log_path, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Stream handler to CLI (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    # Configure Flask app logger ONLY if using this
    # app.logger.setLevel(log_level)
    # app.logger.handlers.clear()
    # app.logger.addHandler(file_handler)
    # app.logger.addHandler(stream_handler)

    # Prevent werkzeug from duplicating logs
    logging.getLogger('werkzeug').propagate = False

    app.logger.info("Logging setup complete - logs will be written to CLI and file")















