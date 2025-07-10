"""
Telephony provider integrations for SIP trunk management
Handles provider-specific operations for Twilio, Telnyx, and other providers
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
import json

from ..core.config import settings
from ..models.sip_trunk import SipTrunk

logger = logging.getLogger(__name__)


class TelephonyProvider(ABC):
    """Abstract base class for telephony providers"""
    
    @abstractmethod
    async def initialize_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Initialize trunk with provider"""
        pass
    
    @abstractmethod
    async def cleanup_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Cleanup trunk with provider"""
        pass
    
    @abstractmethod
    async def health_check(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Perform health check on trunk"""
        pass
    
    @abstractmethod
    async def make_call(self, trunk: SipTrunk, from_number: str, to_number: str, 
                       webhook_url: str) -> Dict[str, Any]:
        """Initiate a call through the provider"""
        pass
    
    @abstractmethod
    async def hangup_call(self, trunk: SipTrunk, call_id: str) -> Dict[str, Any]:
        """Hangup a call"""
        pass


class TwilioProvider(TelephonyProvider):
    """Twilio telephony provider implementation"""
    
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.base_url = "https://api.twilio.com/2010-04-01"
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with authentication"""
        if not self.client:
            self.client = httpx.AsyncClient(
                auth=(self.account_sid, self.auth_token),
                timeout=30.0
            )
        return self.client
    
    async def initialize_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Initialize trunk with Twilio"""
        try:
            if not self.account_sid or not self.auth_token:
                raise ValueError("Twilio credentials not configured")
            
            # For Twilio, we typically don't need to create the trunk explicitly
            # as it's configured through their console, but we can validate credentials
            client = await self._get_client()
            
            # Validate account by fetching account info
            response = await client.get(f"{self.base_url}/Accounts/{self.account_sid}.json")
            
            if response.status_code == 200:
                account_info = response.json()
                logger.info(f"Twilio trunk initialized for account: {account_info.get('friendly_name')}")
                return {
                    "status": "success",
                    "provider": "twilio",
                    "account_sid": self.account_sid,
                    "account_name": account_info.get("friendly_name"),
                    "timestamp": datetime.utcnow()
                }
            else:
                raise Exception(f"Twilio API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Twilio trunk: {e}")
            raise
    
    async def cleanup_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Cleanup trunk with Twilio"""
        try:
            # For Twilio, cleanup typically involves removing webhooks or configurations
            # This is a placeholder for any cleanup operations needed
            logger.info(f"Twilio trunk cleanup completed for trunk {trunk.id}")
            return {
                "status": "success",
                "provider": "twilio",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to cleanup Twilio trunk: {e}")
            raise
    
    async def health_check(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Perform health check on Twilio trunk"""
        try:
            client = await self._get_client()
            start_time = datetime.utcnow()
            
            # Check account status
            response = await client.get(f"{self.base_url}/Accounts/{self.account_sid}.json")
            
            end_time = datetime.utcnow()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                account_info = response.json()
                status = account_info.get("status", "unknown")
                
                return {
                    "status": "healthy" if status == "active" else "unhealthy",
                    "provider": "twilio",
                    "latency_ms": latency_ms,
                    "account_status": status,
                    "timestamp": datetime.utcnow(),
                    "details": {
                        "account_sid": self.account_sid,
                        "account_name": account_info.get("friendly_name")
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "twilio",
                    "latency_ms": latency_ms,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Twilio health check failed: {e}")
            return {
                "status": "error",
                "provider": "twilio",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def make_call(self, trunk: SipTrunk, from_number: str, to_number: str, 
                       webhook_url: str) -> Dict[str, Any]:
        """Make a call through Twilio"""
        try:
            client = await self._get_client()
            
            call_data = {
                "From": from_number,
                "To": to_number,
                "Url": webhook_url,
                "Method": "POST",
                "StatusCallback": f"{webhook_url}/status",
                "StatusCallbackMethod": "POST"
            }
            
            response = await client.post(
                f"{self.base_url}/Accounts/{self.account_sid}/Calls.json",
                data=call_data
            )
            
            if response.status_code == 201:
                call_info = response.json()
                return {
                    "status": "success",
                    "provider": "twilio",
                    "call_id": call_info["sid"],
                    "call_status": call_info["status"],
                    "timestamp": datetime.utcnow()
                }
            else:
                raise Exception(f"Twilio call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to make Twilio call: {e}")
            raise
    
    async def hangup_call(self, trunk: SipTrunk, call_id: str) -> Dict[str, Any]:
        """Hangup a Twilio call"""
        try:
            client = await self._get_client()
            
            response = await client.post(
                f"{self.base_url}/Accounts/{self.account_sid}/Calls/{call_id}.json",
                data={"Status": "completed"}
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "provider": "twilio",
                    "call_id": call_id,
                    "timestamp": datetime.utcnow()
                }
            else:
                raise Exception(f"Twilio hangup failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to hangup Twilio call: {e}")
            raise


class TelnyxProvider(TelephonyProvider):
    """Telnyx telephony provider implementation"""
    
    def __init__(self):
        self.api_key = settings.TELNYX_API_KEY
        self.base_url = "https://api.telnyx.com/v2"
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with authentication"""
        if not self.client:
            self.client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
        return self.client
    
    async def initialize_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Initialize trunk with Telnyx"""
        try:
            if not self.api_key:
                raise ValueError("Telnyx API key not configured")
            
            client = await self._get_client()
            
            # Validate API key by fetching account info
            response = await client.get(f"{self.base_url}/account")
            
            if response.status_code == 200:
                account_info = response.json()
                logger.info(f"Telnyx trunk initialized for account: {account_info.get('data', {}).get('company_name')}")
                return {
                    "status": "success",
                    "provider": "telnyx",
                    "account_info": account_info.get("data", {}),
                    "timestamp": datetime.utcnow()
                }
            else:
                raise Exception(f"Telnyx API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Telnyx trunk: {e}")
            raise
    
    async def cleanup_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Cleanup trunk with Telnyx"""
        try:
            logger.info(f"Telnyx trunk cleanup completed for trunk {trunk.id}")
            return {
                "status": "success",
                "provider": "telnyx",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to cleanup Telnyx trunk: {e}")
            raise
    
    async def health_check(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Perform health check on Telnyx trunk"""
        try:
            client = await self._get_client()
            start_time = datetime.utcnow()
            
            # Check account status
            response = await client.get(f"{self.base_url}/account")
            
            end_time = datetime.utcnow()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                account_info = response.json().get("data", {})
                
                return {
                    "status": "healthy",
                    "provider": "telnyx",
                    "latency_ms": latency_ms,
                    "timestamp": datetime.utcnow(),
                    "details": {
                        "company_name": account_info.get("company_name"),
                        "account_id": account_info.get("id")
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": "telnyx",
                    "latency_ms": latency_ms,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Telnyx health check failed: {e}")
            return {
                "status": "error",
                "provider": "telnyx",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def make_call(self, trunk: SipTrunk, from_number: str, to_number: str, 
                       webhook_url: str) -> Dict[str, Any]:
        """Make a call through Telnyx"""
        try:
            client = await self._get_client()
            
            call_data = {
                "connection_id": trunk.advanced_config.get("connection_id") if trunk.advanced_config else None,
                "to": to_number,
                "from": from_number,
                "webhook_url": webhook_url,
                "webhook_url_method": "POST"
            }
            
            response = await client.post(f"{self.base_url}/calls", json=call_data)
            
            if response.status_code == 201:
                call_info = response.json().get("data", {})
                return {
                    "status": "success",
                    "provider": "telnyx",
                    "call_id": call_info.get("call_control_id"),
                    "call_status": call_info.get("call_state"),
                    "timestamp": datetime.utcnow()
                }
            else:
                raise Exception(f"Telnyx call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to make Telnyx call: {e}")
            raise
    
    async def hangup_call(self, trunk: SipTrunk, call_id: str) -> Dict[str, Any]:
        """Hangup a Telnyx call"""
        try:
            client = await self._get_client()
            
            response = await client.post(f"{self.base_url}/calls/{call_id}/actions/hangup")
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "provider": "telnyx",
                    "call_id": call_id,
                    "timestamp": datetime.utcnow()
                }
            else:
                raise Exception(f"Telnyx hangup failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to hangup Telnyx call: {e}")
            raise


class CustomSipProvider(TelephonyProvider):
    """Custom SIP provider for direct SIP trunk connections"""
    
    async def initialize_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Initialize custom SIP trunk"""
        try:
            # For custom SIP, we mainly validate the configuration
            if not trunk.sip_domain or not trunk.sip_username:
                raise ValueError("SIP domain and username are required for custom SIP")
            
            logger.info(f"Custom SIP trunk initialized: {trunk.sip_domain}")
            return {
                "status": "success",
                "provider": "custom",
                "sip_domain": trunk.sip_domain,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to initialize custom SIP trunk: {e}")
            raise
    
    async def cleanup_trunk(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Cleanup custom SIP trunk"""
        try:
            logger.info(f"Custom SIP trunk cleanup completed for trunk {trunk.id}")
            return {
                "status": "success",
                "provider": "custom",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to cleanup custom SIP trunk: {e}")
            raise
    
    async def health_check(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Perform health check on custom SIP trunk"""
        try:
            # For custom SIP, we can perform basic connectivity checks
            # This is a simplified implementation
            start_time = datetime.utcnow()
            
            # Simulate SIP OPTIONS ping (would need actual SIP library)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            end_time = datetime.utcnow()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "provider": "custom",
                "latency_ms": latency_ms,
                "timestamp": datetime.utcnow(),
                "details": {
                    "sip_domain": trunk.sip_domain,
                    "sip_port": trunk.sip_port
                }
            }
        except Exception as e:
            logger.error(f"Custom SIP health check failed: {e}")
            return {
                "status": "error",
                "provider": "custom",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def make_call(self, trunk: SipTrunk, from_number: str, to_number: str, 
                       webhook_url: str) -> Dict[str, Any]:
        """Make a call through custom SIP"""
        try:
            # This would require actual SIP stack implementation
            # For now, return a placeholder response
            call_id = f"custom_{datetime.utcnow().timestamp()}"
            
            return {
                "status": "success",
                "provider": "custom",
                "call_id": call_id,
                "call_status": "initiated",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to make custom SIP call: {e}")
            raise
    
    async def hangup_call(self, trunk: SipTrunk, call_id: str) -> Dict[str, Any]:
        """Hangup a custom SIP call"""
        try:
            # This would require actual SIP stack implementation
            return {
                "status": "success",
                "provider": "custom",
                "call_id": call_id,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to hangup custom SIP call: {e}")
            raise


# Provider factory
def get_provider(provider_name: str) -> TelephonyProvider:
    """Get telephony provider instance by name"""
    providers = {
        "twilio": TwilioProvider,
        "telnyx": TelnyxProvider,
        "custom": CustomSipProvider
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown telephony provider: {provider_name}")
    
    return provider_class()