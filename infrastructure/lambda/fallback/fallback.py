"""
Fallback Lambda Function for Failed Webhook Processing

Handles failed webhook requests and logs them for analysis.
"""
import json
import os
import logging
import boto3
from datetime import datetime
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
analytics_table = dynamodb.Table(os.environ.get('ANALYTICS_TABLE', ''))


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Fallback handler for failed webhook processing
    
    Logs failed requests to DynamoDB for analysis and debugging.
    """
    try:
        logger.info(f"Fallback handler invoked: {json.dumps(event, default=str)}")
        
        # Extract request information
        body = event.get('body', '')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters') or {}
        
        # Parse body if it's JSON
        try:
            parsed_body = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed_body = {'raw_body': body}
        
        # Log to DynamoDB analytics table
        if analytics_table:
            log_failed_request(
                request_id=context.aws_request_id,
                headers=headers,
                body=parsed_body,
                query_params=query_params
            )
        
        # Return success response
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Fallback request processed',
                'requestId': context.aws_request_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
        logger.info("Fallback request processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Fallback handler error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'requestId': context.aws_request_id
            })
        }


def log_failed_request(request_id: str, headers: Dict, body: Dict, query_params: Dict) -> None:
    """Log failed request to DynamoDB analytics table"""
    
    try:
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'metric_id': f"fallback-{request_id}",
            'timestamp': timestamp,
            'event_type': 'webhook_fallback',
            'request_id': request_id,
            'headers': headers,
            'body': body,
            'query_params': query_params,
            'environment': os.environ.get('ENVIRONMENT', 'dev'),
            'created_at': timestamp
        }
        
        analytics_table.put_item(Item=item)
        logger.info(f"Logged fallback request to analytics: {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to log to analytics table: {str(e)}")
        # Don't fail the main request if logging fails
