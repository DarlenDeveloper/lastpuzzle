"""
Account management service for AIRIES AI platform
Handles account ID generation, validation, and context management
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import secrets
import string

from ..models.user import User
from ..core.logging import get_logger, set_account_context

logger = get_logger(__name__)


def generate_account_id() -> str:
    """Generate a unique account ID"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    return f"ACC_{random_part}"


async def ensure_user_has_account_id(db: AsyncSession, user: User) -> str:
    """Ensure user has an account ID, generate one if missing"""
    if not user.account_id:
        user.account_id = generate_account_id()
        await db.commit()
        await db.refresh(user)
        
        logger.info(
            f"Generated account ID for user {user.id}",
            extra_data={
                'user_id': str(user.id),
                'account_id': user.account_id,
                'email': user.email
            }
        )
    
    return user.account_id


async def get_user_by_account_id(db: AsyncSession, account_id: str) -> Optional[User]:
    """Get user by account ID"""
    result = await db.execute(
        select(User).where(User.account_id == account_id)
    )
    return result.scalar_one_or_none()


async def validate_account_access(db: AsyncSession, account_id: str, user_id: str) -> bool:
    """Validate that a user has access to an account"""
    result = await db.execute(
        select(User).where(
            User.account_id == account_id,
            User.id == user_id
        )
    )
    user = result.scalar_one_or_none()
    return user is not None


class AccountContextManager:
    """Context manager for setting account context in operations"""
    
    def __init__(self, account_id: str, user_id: Optional[str] = None, request_id: Optional[str] = None):
        self.account_id = account_id
        self.user_id = user_id
        self.request_id = request_id
        self.logger = get_logger(f"{__name__}.AccountContextManager")
    
    async def __aenter__(self):
        """Set account context when entering"""
        set_account_context(self.account_id, self.user_id, self.request_id)
        self.logger.debug(
            f"Set account context",
            extra_data={
                'account_id': self.account_id,
                'user_id': self.user_id,
                'request_id': self.request_id
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clear account context when exiting"""
        from ..core.logging import clear_account_context
        clear_account_context()
        self.logger.debug("Cleared account context")


async def create_record_with_account_id(
    db: AsyncSession,
    model_class,
    account_id: str,
    **kwargs
) -> Any:
    """Create a new record with account_id automatically set"""
    
    # Add account_id to the record data
    kwargs['account_id'] = account_id
    
    # Create the record
    record = model_class(**kwargs)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    logger.log_database_operation(
        operation="CREATE",
        table=model_class.__tablename__,
        record_id=str(record.id),
        extra_data={'account_id': account_id}
    )
    
    return record


async def get_account_usage_summary(db: AsyncSession, account_id: str, period_days: int = 30) -> Dict[str, Any]:
    """Get usage summary for an account"""
    from ..models.usage import UsageLog, CreditTransaction
    from ..models.conversation import Conversation
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get usage statistics
    usage_result = await db.execute(
        select(
            func.count(UsageLog.id).label('total_usage_records'),
            func.sum(UsageLog.amount).label('total_usage_amount'),
            func.sum(UsageLog.cost_credits).label('total_cost_credits')
        ).where(
            UsageLog.account_id == account_id,
            UsageLog.timestamp >= start_date
        )
    )
    usage_stats = usage_result.first()
    
    # Get conversation statistics
    conv_result = await db.execute(
        select(
            func.count(Conversation.id).label('total_conversations'),
            func.sum(Conversation.duration_seconds).label('total_duration_seconds'),
            func.sum(Conversation.total_tokens).label('total_tokens')
        ).where(
            Conversation.account_id == account_id,
            Conversation.created_at >= start_date
        )
    )
    conv_stats = conv_result.first()
    
    # Get credit transactions
    credit_result = await db.execute(
        select(
            func.sum(CreditTransaction.amount).label('total_credit_transactions')
        ).where(
            CreditTransaction.account_id == account_id,
            CreditTransaction.timestamp >= start_date
        )
    )
    credit_stats = credit_result.first()
    
    summary = {
        'account_id': account_id,
        'period_days': period_days,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'usage': {
            'total_records': usage_stats.total_usage_records or 0,
            'total_amount': float(usage_stats.total_usage_amount or 0),
            'total_cost_credits': usage_stats.total_cost_credits or 0
        },
        'conversations': {
            'total_count': conv_stats.total_conversations or 0,
            'total_duration_seconds': conv_stats.total_duration_seconds or 0,
            'total_tokens': conv_stats.total_tokens or 0
        },
        'credits': {
            'total_transactions': float(credit_stats.total_credit_transactions or 0)
        }
    }
    
    logger.log_business_event(
        'account_usage_summary_generated',
        {
            'account_id': account_id,
            'period_days': period_days,
            'summary': summary
        }
    )
    
    return summary


async def log_account_activity(
    db: AsyncSession,
    account_id: str,
    activity_type: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log account activity for audit purposes"""
    
    activity_data = {
        'account_id': account_id,
        'activity_type': activity_type,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.log_business_event('account_activity', activity_data)


# Utility functions for common operations
async def ensure_account_context_for_user(db: AsyncSession, user: User) -> str:
    """Ensure account context is set for a user and return account_id"""
    account_id = await ensure_user_has_account_id(db, user)
    set_account_context(account_id, str(user.id))
    return account_id


def get_account_id_from_context() -> Optional[str]:
    """Get account ID from current context"""
    from ..core.logging import get_account_context
    context = get_account_context()
    return context.get('account_id')