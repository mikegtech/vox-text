"""
Standardized tagging strategy for AWS resources
"""
from enum import Enum
from typing import Dict, Optional
from aws_cdk import Tags, Aspects, IAspect
from constructs import Construct


class Environment(Enum):
    """Environment types for different tagging strategies"""
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"


class TaggingStrategy:
    """
    Standardized tagging strategy for AWS resources
    
    Applies consistent tags across all resources for:
    - Cost allocation and tracking
    - Resource management and governance
    - Compliance and auditing
    - Operational automation
    """
    
    def __init__(
        self,
        project: str,
        environment: str,
        company: str,
        service: str,
        tenant: Optional[str] = None,
        owner: Optional[str] = None,
        cost_center: Optional[str] = None,
        off_hours_shutdown: Optional[bool] = None,
        custom_tags: Optional[Dict[str, str]] = None
    ):
        self.project = project
        self.environment = environment
        self.company = company
        self.service = service
        self.tenant = tenant
        self.owner = owner or "infrastructure-team"
        self.cost_center = cost_center or f"engineering-{environment}"
        self.off_hours_shutdown = off_hours_shutdown
        self.custom_tags = custom_tags or {}
    
    def get_mandatory_tags(self) -> Dict[str, str]:
        """Get all mandatory tags that should be applied to every resource"""
        tags = {
            # Core identification tags
            "Project": self.project,
            "Environment": self.environment,
            "Company": self.company,
            "Service": self.service,
            
            # Management tags
            "CreatedBy": "cdk",
            "ManagedBy": self.owner,
            
            # Cost allocation tags
            "CostCenter": self.cost_center,
            
            # Operational tags
            "OffHoursShutdown": self._get_off_hours_shutdown_tag(),
        }
        
        # Add tenant if specified
        if self.tenant:
            tags["Tenant"] = self.tenant
        
        # Add custom tags
        tags.update(self.custom_tags)
        
        return tags
    
    def get_environment_tags(self) -> Dict[str, str]:
        """Get environment-specific tags"""
        env_tags = {}
        
        if self.environment == Environment.DEVELOPMENT.value:
            env_tags.update({
                "BackupEnabled": "false",
                "MonitoringLevel": "basic",
                "DataRetention": "7-days"
            })
        elif self.environment == Environment.STAGING.value:
            env_tags.update({
                "BackupEnabled": "true",
                "MonitoringLevel": "standard",
                "DataRetention": "14-days"
            })
        elif self.environment == Environment.PRODUCTION.value:
            env_tags.update({
                "BackupEnabled": "true",
                "MonitoringLevel": "comprehensive",
                "DataRetention": "90-days",
                "DeletionProtection": "enabled"
            })
        
        return env_tags
    
    def get_service_tags(self) -> Dict[str, str]:
        """Get service-specific tags"""
        service_tags = {}
        
        if self.service == "compute":
            service_tags.update({
                "ResourceType": "compute",
                "ScalingPolicy": "auto" if self.environment == Environment.PRODUCTION.value else "manual"
            })
        elif self.service == "storage":
            service_tags.update({
                "ResourceType": "storage",
                "EncryptionEnabled": "true"
            })
        elif self.service == "messaging":
            service_tags.update({
                "ResourceType": "messaging",
                "MessageRetention": "14-days" if self.environment == Environment.PRODUCTION.value else "7-days"
            })
        elif self.service == "monitoring":
            service_tags.update({
                "ResourceType": "monitoring",
                "AlertingEnabled": "true" if self.environment == Environment.PRODUCTION.value else "false"
            })
        
        return service_tags
    
    def get_all_tags(self) -> Dict[str, str]:
        """Get all tags (mandatory + environment + service)"""
        all_tags = {}
        all_tags.update(self.get_mandatory_tags())
        all_tags.update(self.get_environment_tags())
        all_tags.update(self.get_service_tags())
        return all_tags
    
    def apply_to(self, construct: Construct) -> None:
        """Apply tags to a construct"""
        all_tags = self.get_all_tags()
        for key, value in all_tags.items():
            Tags.of(construct).add(key, value)
    
    def create_aspect(self) -> 'CompanyTaggingAspect':
        """Create an aspect that applies these tags to all resources in a scope"""
        return CompanyTaggingAspect(self.get_all_tags())
    
    def _get_off_hours_shutdown_tag(self) -> str:
        """Determine off-hours shutdown setting"""
        if self.off_hours_shutdown is not None:
            return "enabled" if self.off_hours_shutdown else "disabled"
        
        # Default behavior based on environment and service
        if (self.environment == Environment.DEVELOPMENT.value and 
            self.service in ["compute", "api"]):
            return "enabled"
        
        return "disabled"


class CompanyTaggingAspect(IAspect):
    """CDK Aspect that applies company-wide tagging standards"""
    
    def __init__(self, tags: Dict[str, str]):
        self.tags = tags
    
    def visit(self, node: Construct) -> None:
        """Apply tags to all taggable resources"""
        for key, value in self.tags.items():
            Tags.of(node).add(key, value)
