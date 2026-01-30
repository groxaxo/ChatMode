# Enhanced Logging for ChatMode

This document describes the enhanced logging system that makes debugging easier.

## Quick Start

### Enable Debug Mode

Set in your `.env` file:
```bash
DEBUG_MODE=true
# or
LOG_LEVEL=DEBUG
```

Or set environment variable:
```bash
export DEBUG_MODE=true
```

### View Logs

```bash
# Main application log
tail -f logs/chatmode.log

# Debug log (verbose)
tail -f logs/chatmode_debug.log

# Error log only
tail -f logs/chatmode_errors.log
```

## New Logging Features

### 1. **Request Tracing with Correlation IDs**
Every HTTP request gets a unique correlation ID that flows through the entire request lifecycle:
- Automatically added to request/response headers (`X-Correlation-ID`)
- Included in all log entries for that request
- Makes it easy to trace a single request through multiple components

### 2. **Performance Timing**
Function execution times are automatically logged:
```python
from chatmode.logger_config import log_execution_time

@log_execution_time(logger)
def my_function():
    # Your code here
    pass
```

### 3. **Operation Context Manager**
Log operations with automatic timing and status tracking:
```python
from chatmode.logger_config import log_operation

with log_operation(logger, "Processing user data"):
    # Your code here
    pass
# Logs: "Starting: Processing user data" and "Completed: Processing user data in X.XXXs"
```

### 4. **HTTP Request/Response Logging**
Detailed logging of all API calls:
- Request method, URL, and timing
- Response status codes
- Error details when requests fail

### 5. **Debug Log File**
When DEBUG_MODE is enabled:
- Separate `chatmode_debug.log` with all DEBUG level messages
- Function names included in log format
- More verbose output for troubleshooting

### 6. **Structured JSON Logging**
For production deployments with log aggregation:
```python
setup_logging(structured=True)
```
Produces JSON logs like:
```json
{
  "timestamp": "2026-01-30T12:34:56.789Z",
  "level": "INFO",
  "logger": "chatmode.session",
  "message": "Session started",
  "correlation_id": "abc123",
  "source": {
    "filename": "session.py",
    "lineno": 75,
    "funcName": "start"
  }
}
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO |
| `DEBUG_MODE` | Enable verbose debug mode | false |
| `LOG_DIR` | Directory for log files | ./logs |
| `STRUCTURED_LOGGING` | Use JSON structured logging | false |

### Programmatic Configuration

```python
from chatmode.logger_config import setup_logging

# Basic setup
setup_logging(log_level="DEBUG")

# With all options
setup_logging(
    log_level="DEBUG",
    log_dir="./logs",
    log_to_file=True,
    log_to_console=True,
    structured=False,
    debug_mode=True,
)
```

## Usage Examples

### Basic Logging
```python
from chatmode.logger_config import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.debug(f"Processing {len(items)} items")
logger.error("Failed to connect", exc_info=True)
```

### Correlation IDs
```python
from chatmode.logger_config import correlation_context, get_correlation_id

# Set correlation ID for a block of code
with correlation_context("my-request-id"):
    logger.info("This will include the correlation ID")
    # All logs in this block will have the same correlation ID

# Or get/set manually
correlation_id = get_correlation_id()  # Auto-generates if not set
```

### Logging Dictionaries
```python
from chatmode.logger_config import log_dict

log_dict(logger, "User data", user_data)
# Pretty-prints the dictionary in the log
```

### HTTP Request Logging
```python
from chatmode.logger_config import log_request_response

log_request_response(
    logger,
    method="POST",
    url="https://api.example.com/data",
    status_code=200,
    duration_ms=150.5,
)
```

## Log File Locations

All logs are stored in the `LOG_DIR` directory (default: `./logs`):

- `chatmode.log` - Main application log (all levels)
- `chatmode_debug.log` - Debug-level messages only (when DEBUG_MODE enabled)
- `chatmode_errors.log` - Error and critical messages only
- `backend.log` - Additional backend service logs
- `uvicorn.log` - Web server logs

## Best Practices

1. **Use DEBUG level for development**: Set `DEBUG_MODE=true` during development
2. **Use correlation IDs**: Always use correlation contexts when tracing multi-step operations
3. **Log at appropriate levels**:
   - DEBUG: Detailed information for debugging
   - INFO: General application flow
   - WARNING: Unexpected but handled situations
   - ERROR: Errors that need attention
   - CRITICAL: System-critical failures
4. **Include context**: Use `extra=` parameter to add structured data to logs
5. **Use exc_info**: Always include `exc_info=True` when logging exceptions

## Troubleshooting

### Logs not appearing
- Check that `LOG_DIR` is writable
- Verify `LOG_LEVEL` is set correctly
- Ensure `setup_logging()` is called before logging

### Too much log output
- Set `LOG_LEVEL=INFO` or higher
- Disable `DEBUG_MODE`
- Use structured logging and filter at the aggregation layer

### Correlation IDs not showing
- Ensure you're using `get_logger()` from `chatmode.logger_config`
- Check that requests are going through the FastAPI middleware
- Verify correlation ID is being passed in request headers
