"""
SPDX-FileCopyrightText: © 2025 Moizes Silva
SPDX-License-Identifier: MIT

Logger module for Sienge MCP Server

This module provides logging functionality for the server,
writing logs to a file to avoid interfering with MCP communication.
"""

import logging
import os
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Dict


class LogLevel(Enum):
    """Log levels enum"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


class SiengeLogger:
    """
    Professional logging system for Sienge MCP Server
    Based on ClickUp MCP logging patterns
    """
    
    def __init__(self, name: str = "SiengeMCP"):
        self.name = name
        self.pid = os.getpid()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file output only"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create file handler
        log_file = log_dir / "sienge-mcp.log"
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [PID:%(process)d] %(levelname)s [%(name)s]: %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        # Log initialization
        logger.info(f"Logger initialized for {self.name}")
        
        return logger
    
    def _format_data(self, data: Any) -> str:
        """Format data for logging"""
        if data is None:
            return ""
        
        if isinstance(data, dict):
            if len(data) <= 4 and all(not isinstance(v, (dict, list)) or v is None for v in data.values()):
                # Simple object with few properties - format inline
                items = [f"{k}={v}" for k, v in data.items()]
                return f" | {' | '.join(items)}"
            else:
                # Complex object - format as JSON
                import json
                try:
                    return f" | {json.dumps(data, indent=2, ensure_ascii=False)}"
                except (TypeError, ValueError):
                    return f" | {str(data)}"
        
        return f" | {str(data)}"
    
    def trace(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log trace level message"""
        log_message = message + (self._format_data(data) if data else "")
        self.logger.log(LogLevel.TRACE.value, log_message)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log debug level message"""
        log_message = message + (self._format_data(data) if data else "")
        self.logger.debug(log_message)
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log info level message"""
        log_message = message + (self._format_data(data) if data else "")
        self.logger.info(log_message)
    
    def warn(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log warning level message"""
        log_message = message + (self._format_data(data) if data else "")
        self.logger.warning(log_message)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log error level message"""
        log_message = message + (self._format_data(data) if data else "")
        self.logger.error(log_message)
    
    def log_operation(self, operation: str, data: Optional[Dict[str, Any]] = None):
        """Log API operation with data"""
        self.debug(f"Operation: {operation}", data)
    
    def log_request(self, method: str, url: str, data: Optional[Dict[str, Any]] = None):
        """Log HTTP request"""
        request_data = {"method": method, "url": url}
        if data:
            request_data["data"] = data
        self.debug("HTTP Request", request_data)
    
    def log_response(self, status_code: int, url: str, data: Optional[Dict[str, Any]] = None):
        """Log HTTP response"""
        response_data = {"status": status_code, "url": url}
        if data:
            response_data["response"] = data
        self.debug("HTTP Response", response_data)


# Global logger instances
_loggers: Dict[str, SiengeLogger] = {}


def get_logger(name: str = "SiengeMCP") -> SiengeLogger:
    """Get or create a logger instance"""
    if name not in _loggers:
        _loggers[name] = SiengeLogger(name)
    return _loggers[name]


# Convenience functions for default logger
def trace(message: str, data: Optional[Dict[str, Any]] = None):
    """Log trace level message using default logger"""
    get_logger().trace(message, data)


def debug(message: str, data: Optional[Dict[str, Any]] = None):
    """Log debug level message using default logger"""
    get_logger().debug(message, data)


def info(message: str, data: Optional[Dict[str, Any]] = None):
    """Log info level message using default logger"""
    get_logger().info(message, data)


def warn(message: str, data: Optional[Dict[str, Any]] = None):
    """Log warning level message using default logger"""
    get_logger().warn(message, data)


def error(message: str, data: Optional[Dict[str, Any]] = None):
    """Log error level message using default logger"""
    get_logger().error(message, data)
