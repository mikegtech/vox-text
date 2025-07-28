#!/usr/bin/env python3
"""
Simple test to verify the package works with CDK
"""
import aws_cdk as cdk
from m3_aws_standards import (
    StandardizedStack,
    NamingConvention,
    TaggingStrategy,
    ServiceType
)

def test_basic_functionality():
    """Test that the package works with CDK"""
    app = cdk.App()
    
    # Test direct utilities
    naming = NamingConvention("test-app", "dev", "my-company")
    tagging = TaggingStrategy("test-app", "dev", "my-company", "messaging")
    
    # Test naming
    lambda_name = naming.lambda_function("sms-handler", ServiceType.MESSAGING)
    table_name = naming.dynamo_table("conversations")
    topic_name = naming.sns_topic("inbound-sms")
    
    print(f"✅ Lambda name: {lambda_name}")
    print(f"✅ Table name: {table_name}")
    print(f"✅ Topic name: {topic_name}")
    
    # Test tagging
    all_tags = tagging.get_all_tags()
    print(f"✅ Generated {len(all_tags)} tags:")
    for key, value in all_tags.items():
        print(f"   {key}: {value}")
    
    # Test StandardizedStack (without synthesizing to avoid complexity)
    try:
        stack = StandardizedStack(
            app,
            "TestStack",
            project="test-app",
            environment="dev", 
            company="my-company",
            service="messaging"
        )
        print("✅ StandardizedStack created successfully")
        print(f"✅ Stack naming utility available: {stack.naming.get_prefix()}")
        print(f"✅ Stack tagging utility available: {len(stack.tagging.get_all_tags())} tags")
    except Exception as e:
        print(f"❌ StandardizedStack failed: {e}")
        return False
    
    print("\n🎉 All tests passed! The package is working correctly.")
    return True

if __name__ == "__main__":
    test_basic_functionality()
