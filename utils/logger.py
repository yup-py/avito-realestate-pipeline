import logging
import os

def setup_logger(name):
    # Auto-create the logs folder so the next person doesn't have to
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs if setup is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # File Handler
        file_handler = logging.FileHandler(os.path.join(log_dir, "pipeline.log"))
        file_handler.setFormatter(formatter)

        # Console Handler (for your terminal)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger