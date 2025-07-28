#!/usr/bin/env python3
"""
SMS Bot Infrastructure - CDK Application Entry Point

This is the main entry point for the SMS Bot CDK application.
It creates and configures all the necessary stacks using our shared standards.
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

import aws_cdk as cdk
from m3_aws_standards import StandardizedStack, ServiceType

# Import our stacks
from stacks.sms_bot_stack import SMSBotStack
from config.environments import get_environment_config, validate_environment_config


def get_context_value(app: cdk.App, key: str, default: str = None) -> str:
    """Get context value with fallback to environment variable"""
    value = app.node.try_get_context(key)
    if value is None:
        value = os.environ.get(key.upper(), default)
    return value


def main():
    """Main application entry point"""
    app = cdk.App()
    
    # Get configuration from context or environment variables
    environment = get_context_value(app, 'environment', 'dev')
    company = get_context_value(app, 'company', 'your-company')
    tenant = get_context_value(app, 'tenant')
    
    # Get environment-specific configuration
    try:
        config = get_environment_config(environment)
        validate_environment_config(config)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Validate required environment variables
    account_id = os.environ.get('CDK_DEFAULT_ACCOUNT') or os.environ.get('AWS_ACCOUNT_ID')
    region = os.environ.get('CDK_DEFAULT_REGION') or os.environ.get('AWS_DEFAULT_REGION') or config.region
    
    if not account_id:
        print("❌ AWS account ID not found. Please run: source ./scripts/setup-aws-env.sh")
        sys.exit(1)
    
    # Create the SMS Bot stack using our standardized approach
    sms_bot_stack = SMSBotStack(
        app,
        "SMSBotStack",
        # Standardized configuration
        project="smsbot",
        environment=environment,
        company=company,
        service=ServiceType.MESSAGING,
        tenant=tenant,
        owner="infrastructure-team",
        # Environment configuration
        env_config=config,
        # CDK environment
        env=cdk.Environment(
            account=account_id,
            region=region
        ),
        description=f"SMS Bot infrastructure for {environment} environment",
    )
    
    # Output key information
    print(f"✅ SMS Bot infrastructure configured for {environment} environment")
    print(f"📋 Stack name: {sms_bot_stack.stack_name}")
    print(f"🏢 Company: {company}")
    print(f"🏷️  Tenant: {tenant or f'{environment}-tenant'}")
    print(f"🌍 Region: {region}")
    print(f"🔧 Account: {account_id}")
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()
