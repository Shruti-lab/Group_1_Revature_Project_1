import os
import logging

def setup_logging(app):
    # Get the project root directory (two levels above this file)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    # ✅ Set default log file path if not defined in app config
    log_file_path = app.config.get("LOG_FILE_PATH", "logs/app.log")

    # ✅ Ensure it’s always a string
    if not isinstance(log_file_path, str):
        log_file_path = "logs/app.log"

    # ✅ Join paths safely
    full_log_path = os.path.join(project_root, log_file_path)

    # ✅ Create log directory if it doesn’t exist
    os.makedirs(os.path.dirname(full_log_path), exist_ok=True)

    # ✅ Setup file handler
    handler = logging.FileHandler(full_log_path)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    # ✅ Add handler to Flask app’s logger
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Logging initialized successfully.")
