# import logging
# import os
# import sys
# from logging.handlers import RotatingFileHandler

# def setup_logging(app):
#     """
#     Configure logging: stream to CLI (stdout) and rotate to file at /logs/app.log.
#     Called this from create_app() after app.config is loaded.
#     """

#     # Get log level from config or default to INFO
#     log_level_name = app.config.get('LOG_LEVEL','INFO').upper()
#     log_level = getattr(logging,log_level_name,logging.INFO)

#     #Formatting in logs file
#     fmt = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
#     formatter = logging.Formatter(fmt)

#     # Get logs file path from config
#     log_file_path = app.config.get('LOG_FILE','logs/app.log')

#     # Get absolute file path of logs file
#     project_root = os.path.dirname(app.root_path)
#     full_log_path = os.path.join(project_root, log_file_path)
    
#     # Ensures logs directory exists
#     log_dir = os.path.dirname(full_log_path)
#     os.makedirs(log_dir, exist_ok=True)

#     # Create log handlers
#     # File handler (rotating) - 5MB max, keep 5 backup files
#     file_handler = RotatingFileHandler(full_log_path, maxBytes=5 * 1024 * 1024, backupCount=5)
#     file_handler.setLevel(log_level)
#     file_handler.setFormatter(formatter)

#     # Stream handler to CLI (stdout)
#     stream_handler = logging.StreamHandler(sys.stdout)
#     stream_handler.setLevel(log_level)
#     stream_handler.setFormatter(formatter)

#     # Configure root logger
#     root_logger = logging.getLogger()
#     root_logger.setLevel(log_level)

#     # Clear existing handlers to avoid duplicates
#     root_logger.handlers.clear()

#     # Add handlers
#     root_logger.addHandler(file_handler)
#     root_logger.addHandler(stream_handler)

#     # Configure Flask app logger ONLY if using this
#     # app.logger.setLevel(log_level)
#     # app.logger.handlers.clear()
#     # app.logger.addHandler(file_handler)
#     # app.logger.addHandler(stream_handler)

#     # Prevent werkzeug from duplicating logs
#     logging.getLogger('werkzeug').propagate = False

#     app.logger.info("Logging setup complete - logs will be written to CLI and file")




import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """
    Scheduler-safe logging configuration.
    Works for Flask + APScheduler + File + Console.
    """

    # Get log level
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)

    # Log file path
    log_file_path = app.config.get("LOG_FILE", "logs/app.log")
    if not isinstance(log_file_path, str):
        log_file_path = "logs/app.log"

    # Build final path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    full_log_path = os.path.join(project_root, log_file_path)

    # Ensure directory
    os.makedirs(os.path.dirname(full_log_path), exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # ------------------------
    # FILE HANDLER
    # ------------------------
    file_handler = RotatingFileHandler(full_log_path, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # ------------------------
    # STREAM HANDLER (terminal)
    # ------------------------
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    # ------------------------
    # ROOT LOGGER (DON’T CLEAR)
    # ------------------------
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Add file handler only once
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)

    # Add stream handler only once
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(stream_handler)

    # ------------------------
    # FLASK APP LOGGER
    # ------------------------
    app.logger.setLevel(log_level)

    # Avoid adding duplicates
    if file_handler not in app.logger.handlers:
        app.logger.addHandler(file_handler)

    if stream_handler not in app.logger.handlers:
        app.logger.addHandler(stream_handler)

    # Prevent werkzeug duplication
    logging.getLogger("werkzeug").propagate = False

    # TEST PRINT (this MUST show)
    app.logger.info("Logging setup complete — scheduler-compatible.")
