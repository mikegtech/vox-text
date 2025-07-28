#!/usr/bin/env python3
"""
Test script to verify the new infrastructure structure works
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

# Test imports
try:
    from m3_aws_standards import NamingConvention, TaggingStrategy, ServiceType
    print("✅ m3_aws_standards import successful")
except ImportError as e:
    print(f"❌ m3_aws_standards import failed: {e}")
    sys.exit(1)

try:
    from config.environments import get_environment_config, validate_environment_config
    print("✅ config.environments import successful")
except ImportError as e:
    print(f"❌ config.environments import failed: {e}")
    sys.exit(1)

try:
    from stacks.sms_bot_stack import SMSBotStack
    print("✅ stacks.sms_bot_stack import successful")
except ImportError as e:
    print(f"❌ stacks.sms_bot_stack import failed: {e}")
    sys.exit(1)

# Test configuration
try:
    config = get_environment_config('dev')
    validate_environment_config(config)
    print("✅ Environment configuration working")
except Exception as e:
    print(f"❌ Environment configuration failed: {e}")
    sys.exit(1)

# Test naming and tagging
try:
    naming = NamingConvention("smsbot", "dev", "test-company")
    lambda_name = naming.lambda_function("sms-handler", ServiceType.MESSAGING)
    table_name = naming.dynamo_table("conversations")
    
    print(f"✅ Naming convention working:")
    print(f"   Lambda: {lambda_name}")
    print(f"   Table: {table_name}")
except Exception as e:
    print(f"❌ Naming convention failed: {e}")
    sys.exit(1)

try:
    tagging = TaggingStrategy("smsbot", "dev", "test-company", "messaging")
    tags = tagging.get_all_tags()
    
    print(f"✅ Tagging strategy working:")
    print(f"   Generated {len(tags)} tags")
    for key, value in list(tags.items())[:3]:  # Show first 3 tags
        print(f"   {key}: {value}")
    print("   ...")
except Exception as e:
    print(f"❌ Tagging strategy failed: {e}")
    sys.exit(1)

print("\n🎉 All structure tests passed!")
print("\n📋 New Infrastructure Structure:")
print("├── app.py                    # Main CDK entry point")
print("├── stacks/")
print("│   └── sms_bot_stack.py     # SMS Bot infrastructure stack")
print("├── config/")
print("│   └── environments.py      # Environment configurations")
print("├── shared-standards/")
print("│   └── m3_aws_standards/    # Shared naming & tagging library")
print("└── deploy.py                # Python deployment script")
print("\n✨ Ready to deploy with: ./deploy.py dev test-company")
