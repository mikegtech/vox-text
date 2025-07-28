"""
Standardized CDK constructs with built-in naming and tagging
"""
from typing import Optional, Dict, Any
from aws_cdk import (
    Stack, StackProps, Aspects,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sqs as sqs
)
from constructs import Construct
from .naming import NamingConvention, ServiceType
from .tagging import TaggingStrategy


class StandardizedStack(Stack):
    """Standardized Stack with automatic naming and tagging"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project: str,
        environment: str,
        company: str,
        service: str,
        tenant: Optional[str] = None,
        owner: Optional[str] = None,
        cost_center: Optional[str] = None,
        off_hours_shutdown: Optional[bool] = None,
        custom_tags: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        # Create naming convention
        naming = NamingConvention(project, environment, company, tenant)
        
        # Use standardized stack name if not provided
        if 'stack_name' not in kwargs:
            kwargs['stack_name'] = naming.resource(service, 'stack', construct_id)
        
        super().__init__(scope, construct_id, **kwargs)
        
        self.naming = naming
        self.tagging = TaggingStrategy(
            project=project,
            environment=environment,
            company=company,
            service=service,
            tenant=tenant,
            owner=owner,
            cost_center=cost_center,
            off_hours_shutdown=off_hours_shutdown,
            custom_tags=custom_tags
        )
        
        # Apply tagging to the stack itself instead of using aspect for now
        self.tagging.apply_to(self)


class StandardizedLambda(Construct):
    """Standardized Lambda Function with built-in naming and tagging"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        identifier: str,
        naming: NamingConvention,
        tagging: TaggingStrategy,
        lambda_service: ServiceType = ServiceType.COMPUTE,
        **kwargs
    ):
        super().__init__(scope, construct_id)
        
        # Generate function name
        function_name = naming.lambda_function(identifier, lambda_service)
        
        # Apply environment-specific defaults
        memory_size = self._get_memory_size(naming.environment)
        
        # Create Lambda function
        self.function = _lambda.Function(
            self,
            "Function",
            function_name=function_name,
            memory_size=memory_size,
            runtime=kwargs.get('runtime', _lambda.Runtime.PYTHON_3_11),
            **{k: v for k, v in kwargs.items() if k != 'runtime'}
        )
        
        # Apply tags
        tagging.apply_to(self)
    
    def _get_memory_size(self, environment: str) -> int:
        """Get memory size based on environment"""
        memory_map = {
            'dev': 256,
            'staging': 512,
            'prod': 1024
        }
        return memory_map.get(environment, 256)


class StandardizedTable(Construct):
    """Standardized DynamoDB Table with built-in naming and tagging"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        identifier: str,
        naming: NamingConvention,
        tagging: TaggingStrategy,
        **kwargs
    ):
        super().__init__(scope, construct_id)
        
        # Generate table name
        table_name = naming.dynamo_table(identifier)
        
        # Apply environment-specific defaults
        point_in_time_recovery = self._get_point_in_time_recovery(naming.environment)
        deletion_protection = self._get_deletion_protection(naming.environment)
        
        # Create DynamoDB table
        self.table = dynamodb.Table(
            self,
            "Table",
            table_name=table_name,
            point_in_time_recovery=point_in_time_recovery,
            deletion_protection=deletion_protection,
            **kwargs
        )
        
        # Apply tags
        tagging.apply_to(self)
    
    def _get_point_in_time_recovery(self, environment: str) -> bool:
        """Enable point-in-time recovery for staging and prod"""
        return environment in ['prod', 'staging']
    
    def _get_deletion_protection(self, environment: str) -> bool:
        """Enable deletion protection for prod"""
        return environment == 'prod'


class StandardizedTopic(Construct):
    """Standardized SNS Topic with built-in naming and tagging"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        identifier: str,
        naming: NamingConvention,
        tagging: TaggingStrategy,
        **kwargs
    ):
        super().__init__(scope, construct_id)
        
        # Generate topic name
        topic_name = naming.sns_topic(identifier)
        
        # Create SNS topic
        self.topic = sns.Topic(
            self,
            "Topic",
            topic_name=topic_name,
            **kwargs
        )
        
        # Apply tags
        tagging.apply_to(self)


class StandardizedQueue(Construct):
    """Standardized SQS Queue with built-in naming and tagging"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        identifier: str,
        naming: NamingConvention,
        tagging: TaggingStrategy,
        **kwargs
    ):
        super().__init__(scope, construct_id)
        
        # Generate queue name
        queue_name = naming.sqs_queue(identifier)
        
        # Create SQS queue
        self.queue = sqs.Queue(
            self,
            "Queue",
            queue_name=queue_name,
            **kwargs
        )
        
        # Apply tags
        tagging.apply_to(self)
