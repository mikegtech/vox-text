"""
Standardized naming convention for AWS resources
"""
from enum import Enum
from typing import Optional
import re


class ServiceType(Enum):
    """Service categories for consistent naming"""
    MESSAGING = "messaging"
    COMPUTE = "compute"
    STORAGE = "storage"
    MONITORING = "monitoring"
    SECURITY = "security"
    NETWORKING = "networking"
    API = "api"


class NamingConvention:
    """
    Standardized naming convention utility
    
    Generates consistent resource names following the pattern:
    {project}-{environment}-{service}-{resource-type}-{identifier}
    """
    
    def __init__(self, project: str, environment: str, company: str, tenant: Optional[str] = None):
        self.project = project
        self.environment = environment
        self.company = company
        self.tenant = tenant
        self._validate_config()
    
    def resource(self, service: str, resource_type: str, identifier: Optional[str] = None) -> str:
        """Generate a resource name following the standard pattern"""
        parts = [self.project, self.environment, service, resource_type]
        if identifier:
            parts.append(identifier)
        return "-".join(parts).lower()
    
    def lambda_function(self, identifier: str, service: ServiceType = ServiceType.COMPUTE) -> str:
        """Generate Lambda function name"""
        return self.resource(service.value, "lambda", identifier)
    
    def dynamo_table(self, table_name: str) -> str:
        """Generate DynamoDB table name"""
        return self.resource(ServiceType.STORAGE.value, "table", table_name)
    
    def sns_topic(self, topic_name: str) -> str:
        """Generate SNS topic name"""
        return self.resource(ServiceType.MESSAGING.value, "topic", topic_name)
    
    def sqs_queue(self, queue_name: str) -> str:
        """Generate SQS queue name"""
        return self.resource(ServiceType.MESSAGING.value, "queue", queue_name)
    
    def iam_role(self, role_name: str, service: ServiceType = ServiceType.SECURITY) -> str:
        """Generate IAM role name"""
        return self.resource(service.value, "role", role_name)
    
    def s3_bucket(self, bucket_name: str) -> str:
        """Generate S3 bucket name (globally unique)"""
        import random
        import string
        base = self.resource(ServiceType.STORAGE.value, "bucket", bucket_name)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{base}-{self.company}-{suffix}"
    
    def log_group(self, service: str, resource_type: str) -> str:
        """Generate CloudWatch log group name"""
        return f"/aws/{resource_type}/{self.resource(service, resource_type)}"
    
    def api_gateway(self, api_name: str) -> str:
        """Generate API Gateway name"""
        return self.resource(ServiceType.API.value, "gateway", api_name)
    
    def get_prefix(self) -> str:
        """Get the base prefix for all resources"""
        return f"{self.project}-{self.environment}"
    
    def _validate_config(self):
        """Validate naming configuration"""
        if not self.project:
            raise ValueError("Project name is required")
        if not self.environment:
            raise ValueError("Environment is required")
        if not self.company:
            raise ValueError("Company name is required")
        
        name_pattern = re.compile(r'^[a-zA-Z0-9-]+$')
        if not name_pattern.match(self.project):
            raise ValueError("Project name can only contain alphanumeric characters and hyphens")
        if not name_pattern.match(self.environment):
            raise ValueError("Environment can only contain alphanumeric characters and hyphens")
