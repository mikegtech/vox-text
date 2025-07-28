#!/usr/bin/env python3
"""
Example Python CDK stack using the shared standards library
"""
import aws_cdk as cdk
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_dynamodb as dynamodb

# Import your shared standards
from m3_aws_standards import (
    StandardizedStack,
    StandardizedLambda,
    StandardizedTable,
    StandardizedTopic,
    NamingConvention,
    TaggingStrategy,
    ServiceType
)


class MyPythonStack(StandardizedStack):
    """Example stack using standardized constructs"""
    
    def __init__(self, scope: cdk.App, construct_id: str, **kwargs):
        super().__init__(
            scope,
            construct_id,
            project="my-python-app",
            environment="dev",
            company="your-company",
            service="messaging",
            tenant="client-a",
            **kwargs
        )
        
        # Create a Lambda function with automatic naming and tagging
        lambda_function = StandardizedLambda(
            self,
            "MessageHandler",
            identifier="sms-handler",
            naming=self.naming,
            tagging=self.tagging,
            lambda_service=ServiceType.MESSAGING,
            code=_lambda.Code.from_asset("lambda"),
            handler="index.handler"
        )
        
        # Create a DynamoDB table with automatic naming and tagging
        conversations_table = StandardizedTable(
            self,
            "ConversationsTable", 
            identifier="conversations",
            naming=self.naming,
            tagging=self.tagging,
            partition_key=dynamodb.Attribute(
                name="conversation_id",
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # Create an SNS topic with automatic naming and tagging
        inbound_topic = StandardizedTopic(
            self,
            "InboundTopic",
            identifier="inbound-sms", 
            naming=self.naming,
            tagging=self.tagging
        )
        
        # Grant permissions
        conversations_table.table.grant_read_write_data(lambda_function.function)
        inbound_topic.topic.grant_publish(lambda_function.function)


# Example usage
app = cdk.App()

# You can also use the utilities directly without the constructs
naming = NamingConvention(
    project="inventory-system",
    environment="prod", 
    company="your-company"
)

tagging = TaggingStrategy(
    project="inventory-system",
    environment="prod",
    company="your-company", 
    service="api",
    owner="backend-team"
)

# Create stack with direct utilities
class DirectUtilityStack(cdk.Stack):
    def __init__(self, scope: cdk.App, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Use naming convention directly
        lambda_name = naming.lambda_function("inventory-processor")
        table_name = naming.dynamo_table("products")
        
        # Create resources with generated names
        lambda_fn = _lambda.Function(
            self,
            "InventoryProcessor",
            function_name=lambda_name,
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="index.handler"
        )
        
        products_table = dynamodb.Table(
            self,
            "ProductsTable",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="product_id",
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # Apply tags manually
        tagging.apply_to(lambda_fn)
        tagging.apply_to(products_table)


# Create both example stacks
MyPythonStack(app, "MyPythonStack")
DirectUtilityStack(app, "DirectUtilityStack")

app.synth()
