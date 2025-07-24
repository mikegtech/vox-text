"""
Telnyx Webhook Fallback/Dead Letter Queue Handler
Handles failed webhook deliveries and retry logic
"""

import json
import boto3
import os
import time
from datetime import datetime, timezone

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    """
    Handle fallback webhook events from Telnyx
    This endpoint receives events that failed primary processing
    """
    print(f"Fallback handler received event: {json.dumps(event, default=str)}")
    
    try:
        # Get request details
        body = event.get('body', '')
        headers = event.get('headers', {})
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        
        # Parse webhook payload
        if body:
            try:
                webhook_data = json.loads(body)
            except json.JSONDecodeError:
                webhook_data = {'raw_body': body}
        else:
            webhook_data = {}
        
        # Store fallback event for analysis
        store_fallback_event(webhook_data, headers, source_ip)
        
        # Attempt to process the event if it's a valid Telnyx webhook
        if is_valid_telnyx_event(webhook_data):
            result = attempt_fallback_processing(webhook_data)
            if result['success']:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'message': 'Fallback processing successful',
                        'processed': True,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
        
        # If we can't process it, acknowledge receipt but log for manual review
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Fallback event received and logged',
                'processed': False,
                'requires_manual_review': True,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"ERROR in fallback handler: {str(e)}")
        
        # Even if processing fails, return 200 to prevent Telnyx retries
        # Log the error for manual investigation
        log_fallback_error(str(e), event)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Fallback handler error - logged for review',
                'error': True,
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def store_fallback_event(webhook_data, headers, source_ip):
    """Store fallback event in DynamoDB for analysis"""
    try:
        # Get analytics table
        analytics_table = dynamodb.Table(os.environ.get('ANALYTICS_TABLE', 'smsbot-dev-analytics'))
        
        # Store fallback event
        analytics_table.put_item(
            Item={
                'date': datetime.utcnow().isoformat()[:10],  # YYYY-MM-DD
                'metric_type': 'fallback_event',
                'timestamp': datetime.utcnow().isoformat(),
                'source_ip': source_ip,
                'headers': json.dumps(dict(headers)),
                'webhook_data': json.dumps(webhook_data),
                'environment': os.environ.get('ENVIRONMENT', 'unknown'),
                'requires_review': True
            }
        )
        
        print("Fallback event stored in analytics table")
        
    except Exception as e:
        print(f"ERROR storing fallback event: {str(e)}")

def is_valid_telnyx_event(webhook_data):
    """Check if this looks like a valid Telnyx webhook event"""
    try:
        # Check for Telnyx webhook structure
        if isinstance(webhook_data, dict):
            data = webhook_data.get('data', {})
            event_type = data.get('event_type', '')
            
            # Common Telnyx event types
            telnyx_events = [
                'message.received',
                'message.sent', 
                'message.delivered',
                'message.failed'
            ]
            
            return event_type in telnyx_events
            
    except Exception as e:
        print(f"ERROR validating Telnyx event: {str(e)}")
    
    return False

def attempt_fallback_processing(webhook_data):
    """Attempt to process the webhook event in fallback mode"""
    try:
        data = webhook_data.get('data', {})
        event_type = data.get('event_type', '')
        
        if event_type == 'message.received':
            # Extract message details
            payload = data.get('payload', {})
            phone_number = payload.get('from', {}).get('phone_number', 'unknown')
            message_body = payload.get('text', '')
            
            # Store in conversations table (simplified)
            conversations_table = dynamodb.Table(os.environ.get('CONVERSATIONS_TABLE', 'smsbot-dev-conversations'))
            
            conversations_table.put_item(
                Item={
                    'phone_number': phone_number,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'last_message': message_body,
                    'conversation_state': 'fallback_processed',
                    'message_count': 1,
                    'environment': os.environ.get('ENVIRONMENT', 'unknown'),
                    'source': 'telnyx_fallback'
                }
            )
            
            # Send simple acknowledgment (no bot response in fallback mode)
            print(f"Fallback processing completed for message from {phone_number}")
            
            return {'success': True, 'action': 'stored_message'}
            
    except Exception as e:
        print(f"ERROR in fallback processing: {str(e)}")
        return {'success': False, 'error': str(e)}
    
    return {'success': False, 'reason': 'unsupported_event_type'}

def log_fallback_error(error_message, event):
    """Log fallback handler errors for investigation"""
    try:
        analytics_table = dynamodb.Table(os.environ.get('ANALYTICS_TABLE', 'smsbot-dev-analytics'))
        
        analytics_table.put_item(
            Item={
                'date': datetime.utcnow().isoformat()[:10],
                'metric_type': 'fallback_error',
                'timestamp': datetime.utcnow().isoformat(),
                'error_message': error_message,
                'event_data': json.dumps(event, default=str),
                'environment': os.environ.get('ENVIRONMENT', 'unknown'),
                'requires_investigation': True
            }
        )
        
    except Exception as e:
        print(f"ERROR logging fallback error: {str(e)}")

# Health check for fallback endpoint
def health_check():
    """Simple health check for fallback endpoint"""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'status': 'healthy',
            'service': 'telnyx-fallback-handler',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.environ.get('ENVIRONMENT', 'unknown')
        })
    }

# For testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'body': json.dumps({
            'data': {
                'event_type': 'message.received',
                'payload': {
                    'from': {'phone_number': '+1234567890'},
                    'text': 'Test fallback message'
                }
            }
        }),
        'headers': {'content-type': 'application/json'},
        'requestContext': {'identity': {'sourceIp': '127.0.0.1'}}
    }
    
    # Set test environment
    os.environ['CONVERSATIONS_TABLE'] = 'test-conversations'
    os.environ['ANALYTICS_TABLE'] = 'test-analytics'
    os.environ['ENVIRONMENT'] = 'test'
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {json.dumps(result, indent=2)}")
