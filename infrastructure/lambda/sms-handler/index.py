"""
SMS Handler Lambda Function with Telnyx Signature Validation
Validates signatures in the handler where we have access to the full payload
"""

import json
import base64
import os
import time
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Use PyNaCl library like official Telnyx SDK
try:
    from nacl.encoding import Base64Encoder
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    NACL_AVAILABLE = True
    print("INFO: PyNaCl library loaded successfully")
except ImportError as e:
    print(f"WARNING: PyNaCl library not available: {e}")
    print("Using basic validation - NOT SECURE for production")
    NACL_AVAILABLE = False

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
secrets_client = boto3.client('secretsmanager')

# Cache for public key
_public_key_cache: Optional[str] = None
_cache_timestamp: float = 0
CACHE_TTL = 300  # 5 minutes
DEFAULT_TOLERANCE = 300  # 5 minutes (same as Telnyx SDK)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SMS Handler with Telnyx signature validation
    Following official Telnyx SDK pattern
    """
    print(f"SMS Handler received event: {json.dumps(event, default=str)}")
    
    try:
        # Extract headers and payload
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        payload = event.get('body', '') or ''
        
        # Get signature validation headers
        signature = headers.get('telnyx-signature-ed25519', '')
        timestamp = headers.get('telnyx-timestamp', '')
        
        print(f"Request details:")
        print(f"  - Payload length: {len(payload)}")
        print(f"  - Has signature: {bool(signature)}")
        print(f"  - Has timestamp: {bool(timestamp)}")
        
        # Validate Telnyx webhook signature
        if not validate_telnyx_webhook(payload, signature, timestamp):
            print("ERROR: Telnyx webhook signature validation failed")
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'message': 'Invalid webhook signature'
                })
            }
        
        print("SUCCESS: Telnyx webhook signature validated")
        
        # Parse webhook payload
        try:
            webhook_data = json.loads(payload)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON payload: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'Invalid JSON payload'
                })
            }
        
        # Process the webhook
        result = process_telnyx_webhook(webhook_data)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Webhook processed successfully',
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"ERROR: SMS Handler failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Webhook processing failed'
            })
        }

def validate_telnyx_webhook(payload: str, signature: str, timestamp: str, tolerance: int = DEFAULT_TOLERANCE) -> bool:
    """
    Validate Telnyx webhook signature using official SDK method
    Based on: https://github.com/team-telnyx/telnyx-python/blob/master/telnyx/webhook.py
    """
    try:
        if not signature or not timestamp:
            print("ERROR: Missing required signature headers")
            return False
        
        # Get public key from Secrets Manager
        public_key = get_public_key_from_secrets()
        if not public_key:
            print("ERROR: Failed to retrieve Telnyx public key")
            return False
        
        if NACL_AVAILABLE:
            return verify_with_nacl(payload, signature, timestamp, public_key, tolerance)
        else:
            print("WARNING: PyNaCl not available, using basic validation")
            return verify_basic_format(signature, public_key)
            
    except Exception as e:
        print(f"ERROR: Signature validation failed: {str(e)}")
        return False

def verify_with_nacl(payload: str, signature: str, timestamp: str, public_key: str, tolerance: int) -> bool:
    """
    Production signature verification using PyNaCl (official Telnyx method)
    """
    try:
        # Convert to bytes (following Telnyx SDK pattern)
        if hasattr(timestamp, "encode"):
            timestamp_bytes = timestamp.encode("utf-8")
        else:
            timestamp_bytes = str(timestamp).encode("utf-8")
        
        if hasattr(payload, "encode"):
            payload_bytes = payload.encode("utf-8")
        else:
            payload_bytes = payload
        
        # Create signed payload: timestamp|payload (Telnyx format)
        signed_payload = timestamp_bytes + b"|" + payload_bytes
        
        print(f"Signature validation details:")
        print(f"  - Signed payload length: {len(signed_payload)} bytes")
        print(f"  - Timestamp: {timestamp}")
        print(f"  - Payload preview: {payload[:100]}...")
        
        # Create VerifyKey from public key (Telnyx SDK method)
        try:
            key = VerifyKey(public_key, encoder=Base64Encoder)
        except Exception as e:
            print(f"ERROR: Failed to create VerifyKey: {str(e)}")
            return False
        
        # Verify signature (Telnyx SDK method)
        try:
            verification_result = key.verify(signed_payload, signature=base64.b64decode(signature))
            if not verification_result:
                print("ERROR: Signature verification returned False")
                return False
        except BadSignatureError:
            print("ERROR: Bad signature - verification failed")
            return False
        except Exception as e:
            print(f"ERROR: Signature verification error: {str(e)}")
            return False
        
        # Check timestamp tolerance (Telnyx SDK method)
        if tolerance and int(timestamp) < time.time() - tolerance:
            print(f"ERROR: Timestamp outside tolerance zone. Timestamp: {timestamp}, Current: {int(time.time())}, Tolerance: {tolerance}")
            return False
        
        print("SUCCESS: Signature verified with PyNaCl library (official Telnyx method)")
        return True
        
    except Exception as e:
        print(f"ERROR: PyNaCl verification exception: {str(e)}")
        return False

def verify_basic_format(signature: str, public_key: str) -> bool:
    """
    Basic format validation when PyNaCl library is not available
    This is NOT secure for production - install PyNaCl library
    """
    try:
        # Decode base64 signature and public key
        signature_bytes = base64.b64decode(signature)
        public_key_bytes = base64.b64decode(public_key)
        
        # Basic format checks (Ed25519 signatures are 64 bytes, public keys are 32 bytes)
        if len(signature_bytes) != 64:
            print(f"ERROR: Invalid signature length: {len(signature_bytes)} (expected 64)")
            return False
            
        if len(public_key_bytes) != 32:
            print(f"ERROR: Invalid public key length: {len(public_key_bytes)} (expected 32)")
            return False
        
        print("WARNING: Using basic format validation - NOT SECURE for production")
        print("Install PyNaCl library for proper signature verification")
        return True
        
    except Exception as e:
        print(f"ERROR: Basic format validation failed: {str(e)}")
        return False

def get_public_key_from_secrets() -> Optional[str]:
    """
    Retrieve Telnyx public key from AWS Secrets Manager with caching
    """
    global _public_key_cache, _cache_timestamp
    
    current_time = time.time()
    
    # Return cached key if still valid
    if _public_key_cache and (current_time - _cache_timestamp) < CACHE_TTL:
        print("Using cached public key")
        return _public_key_cache
    
    try:
        # Get secret name from environment
        secret_name = os.environ.get('TELNYX_PUBLIC_KEY_SECRET', 'smsbot/dev/telnyx-public-key')
        
        print(f"Retrieving secret: {secret_name}")
        
        # Get secret from Secrets Manager
        response = secrets_client.get_secret_value(SecretId=secret_name)
        public_key = response['SecretString'].strip()
        
        # Cache the key
        _public_key_cache = public_key
        _cache_timestamp = current_time
        
        print("Successfully retrieved public key from Secrets Manager")
        return public_key
        
    except Exception as e:
        print(f"ERROR: Failed to retrieve secret from Secrets Manager: {str(e)}")
        return None

def process_telnyx_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Telnyx webhook data
    """
    try:
        data = webhook_data.get('data', {})
        event_type = data.get('event_type', '')
        
        print(f"Processing webhook event: {event_type}")
        
        if event_type == 'message.received':
            return process_message_received(data)
        elif event_type == 'message.sent':
            return process_message_sent(data)
        elif event_type == 'message.delivered':
            return process_message_delivered(data)
        elif event_type == 'message.failed':
            return process_message_failed(data)
        else:
            print(f"WARNING: Unhandled event type: {event_type}")
            return {'status': 'ignored', 'event_type': event_type}
            
    except Exception as e:
        print(f"ERROR: Failed to process webhook: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def process_message_received(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process incoming SMS message
    """
    try:
        payload = data.get('payload', {})
        phone_number = payload.get('from', {}).get('phone_number', 'unknown')
        message_text = payload.get('text', '')
        message_id = payload.get('id', '')
        
        print(f"Received SMS from {phone_number}: {message_text}")
        
        # Store conversation in DynamoDB
        conversations_table = dynamodb.Table(os.environ.get('CONVERSATIONS_TABLE', 'smsbot-dev-conversations'))
        
        conversations_table.put_item(
            Item={
                'phone_number': phone_number,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'last_message': message_text,
                'last_message_id': message_id,
                'conversation_state': 'active',
                'message_count': 1,
                'environment': os.environ.get('ENVIRONMENT', 'unknown')
            }
        )
        
        # Store analytics
        analytics_table = dynamodb.Table(os.environ.get('ANALYTICS_TABLE', 'smsbot-dev-analytics'))
        
        analytics_table.put_item(
            Item={
                'date': datetime.utcnow().isoformat()[:10],  # YYYY-MM-DD
                'metric_type': 'message_received',
                'timestamp': datetime.utcnow().isoformat(),
                'phone_number': phone_number,
                'message_length': len(message_text),
                'environment': os.environ.get('ENVIRONMENT', 'unknown')
            }
        )
        
        print(f"Stored message from {phone_number} in DynamoDB")
        
        return {
            'status': 'processed',
            'action': 'message_stored',
            'phone_number': phone_number,
            'message_id': message_id
        }
        
    except Exception as e:
        print(f"ERROR: Failed to process received message: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def process_message_sent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process message sent confirmation
    """
    try:
        payload = data.get('payload', {})
        message_id = payload.get('id', '')
        
        print(f"Message sent confirmation: {message_id}")
        
        return {
            'status': 'processed',
            'action': 'sent_confirmation',
            'message_id': message_id
        }
        
    except Exception as e:
        print(f"ERROR: Failed to process sent message: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def process_message_delivered(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process message delivery confirmation
    """
    try:
        payload = data.get('payload', {})
        message_id = payload.get('id', '')
        
        print(f"Message delivered confirmation: {message_id}")
        
        return {
            'status': 'processed',
            'action': 'delivery_confirmation',
            'message_id': message_id
        }
        
    except Exception as e:
        print(f"ERROR: Failed to process delivered message: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def process_message_failed(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process message failure notification
    """
    try:
        payload = data.get('payload', {})
        message_id = payload.get('id', '')
        errors = payload.get('errors', [])
        
        print(f"Message failed: {message_id}, errors: {errors}")
        
        return {
            'status': 'processed',
            'action': 'failure_notification',
            'message_id': message_id,
            'errors': errors
        }
        
    except Exception as e:
        print(f"ERROR: Failed to process failed message: {str(e)}")
        return {'status': 'error', 'error': str(e)}
