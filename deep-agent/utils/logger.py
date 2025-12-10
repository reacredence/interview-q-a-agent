"""Shared logging configuration for the interview Q&A agent."""

import os
import sys
import logging
import structlog

# Configure structured logging if not already configured
_configured = False

def configure_logging():
    """Configure structlog for the application."""
    global _configured
    if _configured:
        return
    
    # Set standard library logging level to INFO to show all logs
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Determine if we're in development (use console renderer) or production (use JSON)
    is_dev = os.getenv("ENVIRONMENT", "dev").lower() in ["dev", "development", "local"]
    
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    # Use console renderer for development, JSON for production
    if is_dev:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    _configured = True

def get_logger(name=None):
    """Get a configured logger instance."""
    configure_logging()
    return structlog.get_logger(name)

