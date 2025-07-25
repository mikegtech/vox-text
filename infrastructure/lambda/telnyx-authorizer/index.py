"""
Telnyx Webhook Basic Authorizer
Only validates headers and IP - signature validation moved to SMS handler
"""

import json
import os
import time
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Basic Telnyx webhook authorizer
    Validates required headers and IP restrictions only
    """
    print(f"Authorizer event: {json.dumps(event, default=str)}")
    
    try:
        # Extract headers and source IP
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        
        print(f"Request from IP: {source_ip}")
        print(f"Headers: {list(headers.keys())}")
        
        # Check for required Telnyx headers
        signature = headers.get('telnyx-signature-ed25519', '')
        timestamp = headers.get('telnyx-timestamp', '')
        
        if not signature or not timestamp:
            print("ERROR: Missing required Telnyx headers")
            print(f"  - Has signature: {bool(signature)}")
            print(f"  - Has timestamp: {bool(timestamp)}")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        # Basic timestamp validation (prevent very old requests)
        try:
            webhook_timestamp = int(timestamp)
            current_timestamp = int(time.time())
            age = current_timestamp - webhook_timestamp
            
            # Allow 1 hour window for basic validation
            if age > 3600:  # 1 hour
                print(f"ERROR: Timestamp too old. Age: {age}s")
                return generate_policy('user', 'Deny', event['methodArn'])
                
        except ValueError:
            print(f"ERROR: Invalid timestamp format: {timestamp}")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        # Validate source IP (optional - can be disabled for development)
        if not validate_source_ip(source_ip):
            print(f"WARNING: Request from non-Telnyx IP: {source_ip}")
            # Allow for development - in production you might want to deny
        
        print("SUCCESS: Basic validation passed - signature validation will happen in SMS handler")
        return generate_policy('user', 'Allow', event['methodArn'])
        
    except Exception as e:
        print(f"ERROR: Authorization failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return generate_policy('user', 'Deny', event['methodArn'])

def validate_source_ip(source_ip: str) -> bool:
    """
    Validate source IP against known Telnyx CIDR blocks
    """
    try:
        # Known Telnyx CIDR blocks (update as needed)
        telnyx_cidrs = [
            '185.86.151.0/24',
            '185.86.150.0/24', 
            '147.75.0.0/16',
            '139.178.0.0/16',
            '136.144.0.0/16'
        ]
        
        # For development, allow all IPs
        # In production, you would implement proper CIDR validation
        print(f"IP validation: {source_ip} (allowing all for development)")
        return True
        
    except Exception as e:
        print(f"ERROR: IP validation failed: {str(e)}")
        return False

def generate_policy(principal_id: str, effect: str, resource: str) -> Dict[str, Any]:
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
            'validation_method': 'basic_headers_only',
            'signature_validation': 'handled_in_sms_handler',
            'python_version': '3.12'
        }
    }
    
    print(f"Generated policy: {json.dumps(policy, default=str)}")
    return policy
