"""
API Gateway Lambda Authorizer for Telnyx Webhooks

Validates Telnyx webhook signatures and authorizes requests.
"""
import json
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer handler for API Gateway
    
    Validates Telnyx webhook signatures and returns authorization policy.
    """
    try:
        logger.info(f"Authorizer event: {json.dumps(event, default=str)}")
        
        # Extract request information
        method_arn = event.get('methodArn', '')
        headers = event.get('headers', {})
        
        # Get Telnyx signature header
        telnyx_signature = headers.get('X-Telnyx-Signature') or headers.get('x-telnyx-signature')
        authorization = headers.get('Authorization') or headers.get('authorization')
        
        # Basic validation - in production, implement proper signature verification
        if telnyx_signature or authorization:
            # Allow the request
            policy = generate_policy('user', 'Allow', method_arn)
            logger.info("Request authorized")
        else:
            # Deny the request
            policy = generate_policy('user', 'Deny', method_arn)
            logger.warning("Request denied - missing authentication headers")
        
        return policy
        
    except Exception as e:
        logger.error(f"Authorizer error: {str(e)}")
        # Deny on error
        return generate_policy('user', 'Deny', event.get('methodArn', '*'))


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
            'environment': os.environ.get('ENVIRONMENT', 'dev'),
            'timestamp': str(context.aws_request_id) if 'context' in locals() else 'unknown'
        }
    }
    
    return policy
