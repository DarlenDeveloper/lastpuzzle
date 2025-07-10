"""
Enhanced logging utilities with account context for AIRIES AI platform
Provides structured logging with account ID tracking for all operations
"""

import logging
import json
from typing import Optional, Dict, Any
from contextvars import ContextVar
from datetime import datetime
import uuid

# Context variable to store current account ID
current_account_id: ContextVar[Optional[str]] = ContextVar('current_account_id', default=None)
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)
current_request_id: ContextVar[Optional[str]] = ContextVar('current_request_id', default=None)


class AccountContextFilter(logging.Filter):
    """Logging filter that adds account context to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add account context to log record
        record.account_id = current_account_id.get()
        record.user_id = current_user_id.get()
        record.request_id = current_request_id.get()
        return True


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'account_id': getattr(record, 'account_id', None),
            'user_id': getattr(record, 'user_id', None),
            'request_id': getattr(record, 'request_id', None),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
            
        return json.dumps(log_entry, default=str)


def setup_logging(log_level: str = "INFO", structured: bool = True) -> None:
    """Setup application logging with account context"""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    if structured:
        # Use structured JSON formatter
        formatter = StructuredFormatter()
    else:
        # Use standard formatter with account context
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[Account: %(account_id)s] [User: %(user_id)s] [Request: %(request_id)s] - '
            '%(message)s'
        )
    
    console_handler.setFormatter(formatter)
    console_handler.addFilter(AccountContextFilter())
    
    root_logger.addHandler(console_handler)


def set_account_context(account_id: Optional[str], user_id: Optional[str] = None, request_id: Optional[str] = None) -> None:
    """Set account context for current request/operation"""
    current_account_id.set(account_id)
    if user_id:
        current_user_id.set(user_id)
    if request_id:
        current_request_id.set(request_id)


def clear_account_context() -> None:
    """Clear account context"""
    current_account_id.set(None)
    current_user_id.set(None)
    current_request_id.set(None)


def get_account_context() -> Dict[str, Optional[str]]:
    """Get current account context"""
    return {
        'account_id': current_account_id.get(),
        'user_id': current_user_id.get(),
        'request_id': current_request_id.get()
    }


class AccountLogger:
    """Logger wrapper that automatically includes account context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log_with_context(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Log message with account context and extra data"""
        extra = {}
        if extra_data:
            extra['extra_data'] = extra_data
        
        self.logger.log(level, message, extra=extra, **kwargs)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message with account context"""
        self._log_with_context(logging.DEBUG, message, extra_data, **kwargs)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message with account context"""
        self._log_with_context(logging.INFO, message, extra_data, **kwargs)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message with account context"""
        self._log_with_context(logging.WARNING, message, extra_data, **kwargs)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message with account context"""
        self._log_with_context(logging.ERROR, message, extra_data, **kwargs)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message with account context"""
        self._log_with_context(logging.CRITICAL, message, extra_data, **kwargs)
    
    def log_user_action(self, action: str, resource: str, resource_id: Optional[str] = None, 
                       result: str = "success", extra_data: Optional[Dict[str, Any]] = None):
        """Log user action with standardized format"""
        log_data = {
            'action': action,
            'resource': resource,
            'resource_id': resource_id,
            'result': result
        }
        if extra_data:
            log_data.update(extra_data)
        
        self.info(f"User action: {action} on {resource}", extra_data=log_data)
    
    def log_api_call(self, method: str, endpoint: str, status_code: int, 
                    response_time_ms: float, extra_data: Optional[Dict[str, Any]] = None):
        """Log API call with standardized format"""
        log_data = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time_ms': response_time_ms
        }
        if extra_data:
            log_data.update(extra_data)
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        self._log_with_context(level, f"API call: {method} {endpoint} - {status_code}", log_data)
    
    def log_database_operation(self, operation: str, table: str, record_id: Optional[str] = None,
                              affected_rows: Optional[int] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log database operation with standardized format"""
        log_data = {
            'operation': operation,
            'table': table,
            'record_id': record_id,
            'affected_rows': affected_rows
        }
        if extra_data:
            log_data.update(extra_data)
        
        self.info(f"Database operation: {operation} on {table}", extra_data=log_data)
    
    def log_business_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log business event with standardized format"""
        log_data = {
            'event_type': event_type,
            'event_data': event_data
        }
        
        self.info(f"Business event: {event_type}", extra_data=log_data)


def get_logger(name: str) -> AccountLogger:
    """Get an AccountLogger instance for the given name"""
    return AccountLogger(name)


# Convenience function to generate request IDs
def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())


# Usage tracking functions
def log_usage_event(logger: AccountLogger, usage_type: str, amount: float, 
                   resource_id: Optional[str] = None, cost_credits: Optional[int] = None):
    """Log usage event for billing and analytics"""
    usage_data = {
        'usage_type': usage_type,
        'amount': amount,
        'resource_id': resource_id,
        'cost_credits': cost_credits,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.log_business_event('usage_tracked', usage_data)


def log_security_event(logger: AccountLogger, event_type: str, severity: str = "medium",
                      details: Optional[Dict[str, Any]] = None):
    """Log security-related events"""
    security_data = {
        'event_type': event_type,
        'severity': severity,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    level = logging.WARNING if severity in ['medium', 'high'] else logging.INFO
    logger._log_with_context(level, f"Security event: {event_type}", security_data)