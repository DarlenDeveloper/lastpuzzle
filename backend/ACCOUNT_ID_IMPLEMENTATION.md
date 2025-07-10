# Account ID Implementation for AIRIES AI Platform

## Overview

This document describes the implementation of account IDs across the AIRIES AI platform to ensure proper logging, tracking, and multi-tenancy support.

## What Was Implemented

### 1. Account ID Generation

- **Format**: `ACC_XXXXXXXXXXXX` (where X is alphanumeric)
- **Length**: 16 characters total (4 prefix + 12 random)
- **Uniqueness**: Guaranteed unique across all accounts
- **Location**: `backend/app/models/user.py` - `generate_account_id()` function

### 2. Database Schema Changes

Added `account_id` field to all relevant tables:

#### Core Tables
- `users` - Primary account holder
- `agents` - AI agents belonging to account
- `conversations` - Conversation sessions
- `conversation_messages` - Individual messages (inherits from conversation)

#### Usage & Billing Tables
- `usage_logs` - All usage tracking
- `credit_transactions` - Credit purchases/usage
- `usage_summaries` - Aggregated usage data
- `user_subscriptions` - Subscription management

#### Knowledge Base Tables
- `knowledge_bases` - Document collections
- `documents` - Individual documents
- `document_chunks` - Text chunks (inherits from document)
- `web_scrape_jobs` - Web scraping tasks
- `query_logs` - Knowledge base queries

#### Telephony Tables
- `sip_trunks` - SIP trunk configurations
- `call_logs` - Call records

### 3. Enhanced Logging System

#### New Logging Module: `backend/app/core/logging.py`

**Features:**
- Account context tracking using `contextvars`
- Structured JSON logging
- Automatic account ID injection into all log entries
- Request ID tracking for correlation
- Specialized loggers for different event types

**Key Components:**
- `AccountContextFilter` - Adds account context to log records
- `StructuredFormatter` - JSON formatter for structured logs
- `AccountLogger` - Enhanced logger with account-aware methods
- Context management functions for setting/clearing account context

#### Logging Methods
```python
logger.log_user_action(action, resource, resource_id, result, extra_data)
logger.log_api_call(method, endpoint, status_code, response_time_ms, extra_data)
logger.log_database_operation(operation, table, record_id, affected_rows, extra_data)
logger.log_business_event(event_type, event_data)
```

### 4. Account Service

#### New Service: `backend/app/services/account_service.py`

**Functions:**
- `generate_account_id()` - Generate unique account IDs
- `ensure_user_has_account_id()` - Ensure users have account IDs
- `get_user_by_account_id()` - Lookup users by account ID
- `validate_account_access()` - Validate user access to account
- `create_record_with_account_id()` - Helper for creating records with account context
- `get_account_usage_summary()` - Generate usage reports by account
- `log_account_activity()` - Log account-specific activities

**AccountContextManager:**
- Async context manager for setting account context
- Automatically sets and clears account context
- Used in service operations for proper logging

### 5. Middleware Integration

#### Account Context Middleware: `backend/app/main.py`

**Features:**
- Automatically extracts account information from requests
- Sets account context for the duration of the request
- Generates unique request IDs for correlation
- Clears context after request completion
- Enhanced request/response logging with account context

### 6. Database Migration

#### Migration File: `backend/alembic/versions/003_add_account_id_fields.py`

**Operations:**
- Adds `account_id` columns to all tables
- Creates indexes for performance
- Populates existing records with generated account IDs
- Maintains referential integrity
- Supports rollback operations

### 7. Updated User Service

#### Enhanced: `backend/app/services/user_service.py`

**Changes:**
- Integrated account service for ID management
- Added account context to all operations
- Enhanced logging for user actions
- Automatic account ID generation for new users
- Account activity logging for audit trails

## Usage Examples

### Setting Account Context

```python
from app.core.logging import set_account_context, get_logger
from app.services.account_service import AccountContextManager

# Manual context setting
set_account_context("ACC_ABC123DEF456", "user-uuid", "request-uuid")

# Using context manager (recommended)
async with AccountContextManager("ACC_ABC123DEF456", "user-uuid"):
    logger = get_logger(__name__)
    logger.info("Operation within account context")
```

### Creating Records with Account Context

```python
from app.services.account_service import create_record_with_account_id

# Create agent with automatic account ID
agent = await create_record_with_account_id(
    db=db,
    model_class=Agent,
    account_id="ACC_ABC123DEF456",
    name="My Agent",
    user_id=user.id,
    # ... other fields
)
```

### Logging with Account Context

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# All these logs will include account context automatically
logger.log_user_action("create_agent", "agent", str(agent.id))
logger.log_database_operation("INSERT", "agents", str(agent.id))
logger.log_business_event("agent_created", {"agent_id": str(agent.id)})
```

### Getting Account Usage Summary

```python
from app.services.account_service import get_account_usage_summary

summary = await get_account_usage_summary(
    db=db,
    account_id="ACC_ABC123DEF456",
    period_days=30
)
```

## Log Format

### Structured JSON Logs

```json
{
  "timestamp": "2025-01-07T17:45:00.000Z",
  "level": "INFO",
  "logger": "app.services.user_service",
  "message": "User action: create_agent on agent",
  "account_id": "ACC_ABC123DEF456",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "req_789xyz",
  "module": "user_service",
  "function": "create_user",
  "line": 45,
  "extra": {
    "action": "create_agent",
    "resource": "agent",
    "resource_id": "agent-uuid",
    "result": "success"
  }
}
```

## Benefits

### 1. Complete Audit Trail
- Every operation is logged with account context
- Full traceability of actions across the platform
- Request correlation through request IDs

### 2. Multi-Tenant Support
- Clear separation of data by account
- Account-based access control
- Isolated usage tracking and billing

### 3. Enhanced Monitoring
- Account-level performance metrics
- Usage pattern analysis
- Security event tracking

### 4. Compliance & Security
- Detailed audit logs for compliance
- Account-based security monitoring
- Data privacy through account isolation

### 5. Operational Insights
- Account usage analytics
- Performance monitoring by account
- Billing accuracy and transparency

## Migration Notes

### For Existing Data
1. Run the migration: `alembic upgrade head`
2. All existing records will get account IDs automatically
3. No data loss or service interruption
4. Indexes created for optimal performance

### For New Development
1. Always use account-aware services
2. Set account context in operations
3. Use structured logging methods
4. Include account validation in endpoints

## Security Considerations

### Account ID Protection
- Account IDs are not sensitive but should not be exposed unnecessarily
- Use proper authorization checks before operations
- Validate account access for all operations

### Logging Security
- Logs may contain account IDs - ensure proper log access controls
- Structured logs make it easier to filter sensitive information
- Request IDs help with debugging without exposing account details

## Performance Impact

### Database
- Minimal impact due to proper indexing
- Account ID queries are optimized
- Existing queries unaffected

### Logging
- Structured logging has minimal overhead
- Context variables are thread-safe and efficient
- JSON formatting adds small serialization cost

### Memory
- Context variables use minimal memory
- Account context cleared after each request
- No memory leaks from context management

## Future Enhancements

### Planned Features
1. Account-based rate limiting
2. Account hierarchy support (organizations)
3. Cross-account resource sharing
4. Advanced analytics dashboard
5. Account-based backup and restore

### Monitoring Integration
1. Prometheus metrics by account
2. Grafana dashboards for account analytics
3. Alert rules for account-specific thresholds
4. Log aggregation and analysis tools

## Troubleshooting

### Common Issues
1. **Missing Account Context**: Ensure middleware is properly configured
2. **Account ID Not Generated**: Check user creation process
3. **Logging Not Working**: Verify logger setup and context setting
4. **Migration Issues**: Check database permissions and constraints

### Debug Commands
```bash
# Check account IDs in database
SELECT account_id, email FROM users LIMIT 10;

# Verify account context in logs
grep "account_id" /var/log/airies/app.log

# Test account service
python -c "from app.services.account_service import generate_account_id; print(generate_account_id())"
```

This implementation provides a robust foundation for account-based operations, logging, and multi-tenancy in the AIRIES AI platform.