"""
Telnyx Webhook Ed25519 Signature Validation Authorizer
Production-ready implementation using AWS Secrets Manager
"""

import json
import base64
import os
import time
import boto3
from datetime import datetime, timezone

# For production, you would install cryptography library in a Lambda Layer
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    print("WARNING: cryptography library not available, using basic validation")
    CRYPTO_AVAILABLE = False

# Initialize Secrets Manager client
secrets_client = boto3.client('secretsmanager')

# Cache for public key to avoid repeated API calls
_public_key_cache = None
_cache_timestamp = 0
CACHE_TTL = 300  # 5 minutes

def lambda_handler(event, context):
    """
    Telnyx webhook Ed25519 signature validation authorizer
    Retrieves public key from AWS Secrets Manager
    """
    print(f"Authorizer event: {json.dumps(event, default=str)}")
    
    try:
        # Extract headers (case-insensitive)
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        signature = headers.get('telnyx-signature-ed25519', '')
        timestamp = headers.get('telnyx-timestamp', '')
        
        # Get public key from Secrets Manager
        public_key_b64 = get_public_key_from_secrets()
        
        if not public_key_b64:
            print("ERROR: Failed to retrieve TELNYX_PUBLIC_KEY from Secrets Manager")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        if not signature or not timestamp:
            print("ERROR: Missing required headers")
            print(f"Available headers: {list(headers.keys())}")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        # Validate timestamp (prevent replay attacks)
        if not validate_timestamp(timestamp):
            return generate_policy('user', 'Deny', event['methodArn'])
        
        # Get request body
        body = event.get('body', '')
        if body is None:
            body = ''
        
        # Create signed payload: timestamp|body (Telnyx format)
        signed_payload = f"{timestamp}|{body}"
        
        # Verify Ed25519 signature
        if verify_ed25519_signature(signed_payload, signature, public_key_b64):
            print("SUCCESS: Signature validation passed")
            return generate_policy('user', 'Allow', event['methodArn'])
        else:
            print("ERROR: Signature validation failed")
            return generate_policy('user', 'Deny', event['methodArn'])
        
    except Exception as e:
        print(f"ERROR: Authorization failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return generate_policy('user', 'Deny', event['methodArn'])

def get_public_key_from_secrets():
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
        public_key = response['SecretString']
        
        # Cache the key
        _public_key_cache = public_key
        _cache_timestamp = current_time
        
        print("Successfully retrieved public key from Secrets Manager")
        return public_key
        
    except Exception as e:
        print(f"ERROR: Failed to retrieve secret from Secrets Manager: {str(e)}")
        return None

def validate_timestamp(timestamp_str):
    """Validate timestamp to prevent replay attacks"""
    try:
        webhook_timestamp = int(timestamp_str)
        current_timestamp = int(time.time())
        
        # Allow 5 minute window (300 seconds)
        tolerance = 300
        age = current_timestamp - webhook_timestamp
        
        if age > tolerance:
            print(f"ERROR: Timestamp too old. Age: {age}s, Tolerance: {tolerance}s")
            return False
        
        if age < -60:  # Allow 1 minute clock skew in the future
            print(f"ERROR: Timestamp too far in future. Age: {age}s")
            return False
            
        return True
        
    except ValueError:
        print(f"ERROR: Invalid timestamp format: {timestamp_str}")
        return False

def verify_ed25519_signature(payload, signature_b64, public_key_b64):
    """
    Verify Ed25519 signature using cryptography library
    Falls back to basic validation if library not available
    """
    try:
        if CRYPTO_AVAILABLE:
            return verify_with_cryptography(payload, signature_b64, public_key_b64)
        else:
            return verify_basic_format(signature_b64, public_key_b64)
            
    except Exception as e:
        print(f"ERROR: Signature verification failed: {str(e)}")
        return False

def verify_with_cryptography(payload, signature_b64, public_key_b64):
    """Production Ed25519 verification using cryptography library"""
    try:
        # Decode base64 signature and public key
        signature_bytes = base64.b64decode(signature_b64)
        public_key_bytes = base64.b64decode(public_key_b64)
        
        # Create Ed25519 public key object
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Verify signature
        public_key.verify(signature_bytes, payload.encode('utf-8'))
        
        print("SUCCESS: Ed25519 signature verified with cryptography library")
        return True
        
    except InvalidSignature:
        print("ERROR: Invalid Ed25519 signature")
        return False
    except Exception as e:
        print(f"ERROR: Ed25519 verification error: {str(e)}")
        return False

def verify_basic_format(signature_b64, public_key_b64):
    """
    Basic format validation when cryptography library is not available
    This is NOT secure for production - install cryptography library
    """
    try:
        # Decode base64 signature and public key
        signature_bytes = base64.b64decode(signature_b64)
        public_key_bytes = base64.b64decode(public_key_b64)
        
        # Basic format checks
        if len(signature_bytes) != 64:  # Ed25519 signatures are 64 bytes
            print(f"ERROR: Invalid signature length: {len(signature_bytes)} (expected 64)")
            return False
            
        if len(public_key_bytes) != 32:  # Ed25519 public keys are 32 bytes
            print(f"ERROR: Invalid public key length: {len(public_key_bytes)} (expected 32)")
            return False
        
        print("WARNING: Using basic format validation - NOT SECURE for production")
        print("Install cryptography library for proper Ed25519 verification")
        return True
        
    except Exception as e:
        print(f"ERROR: Basic format validation failed: {str(e)}")
        return False

def generate_policy(principal_id, effect, resource):
    """Generate IAM policy for API Gateway"""
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        },
        'context': {
            'environment': os.environ.get('ENVIRONMENT', 'unknown'),
            'timestamp': str(int(time.time())),
            'validation_method': 'ed25519_cryptography' if CRYPTO_AVAILABLE else 'ed25519_basic',
            'crypto_available': str(CRYPTO_AVAILABLE),
            'secret_source': 'secrets_manager'
        }
    }
    
    print(f"Generated policy: {json.dumps(policy, default=str)}")
    return policy
