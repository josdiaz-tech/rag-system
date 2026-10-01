# app/core/logging_config.py
"""
Structured logging configuration for the RAG system
Logs to both console and files with JSON formatting
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger
from pathlib import Path


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp in readable format
        if not log_record.get('timestamp'):
            # Human-readable: 2025-11-12 22:12:26
            log_record['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


def setup_logging(log_dir: str = "../../logs", log_level: str = "INFO"):
    """
    Setup structured logging for the application
    
    Creates:
    - Console output (formatted for readability)
    - JSON log file (for parsing/analysis)
    - Error log file (errors only)
    - Automatic log rotation (10MB per file, keep 5 files)
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True, parents=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # 1. Console Handler (human-readable format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 2. JSON File Handler (all logs, machine-readable)
    json_handler = logging.handlers.RotatingFileHandler(
        log_path / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    json_handler.setLevel(logging.INFO)
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    json_handler.setFormatter(json_formatter)
    logger.addHandler(json_handler)
    
    # 3. Error File Handler (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / 'errors.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    logger.addHandler(error_handler)
    
    # CRITICAL: Silence noisy loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)  # Only warnings/errors
    logging.getLogger('watchfiles').setLevel(logging.WARNING)  # Only warnings/errors
    logging.getLogger('asyncio').setLevel(logging.WARNING)  # Only warnings/errors
    
    # Don't log the initialization itself
    print(f"📝 Logging initialized: {log_path.absolute()}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(name)


# Specialized loggers for different concerns
def get_query_logger() -> logging.Logger:
    """Get logger specifically for query tracking"""
    return logging.getLogger('queries')


def get_security_logger() -> logging.Logger:
    """Get logger specifically for security events"""
    return logging.getLogger('security')


def get_cost_logger() -> logging.Logger:
    """Get logger specifically for cost tracking"""
    return logging.getLogger('costs')