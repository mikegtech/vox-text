"""
Environment-specific configuration for SMS Bot infrastructure
"""
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass


@dataclass
class SMSConfig:
    """SMS service configuration"""
    monthly_spend_limit: int
    default_sms_type: Literal['Promotional', 'Transactional']
    delivery_status_sampling_rate: int
    default_sender_id: Optional[str] = None


@dataclass
class LambdaConfig:
    """Lambda function configuration"""
    timeout: int
    memory_size: int
    reserved_concurrency: Optional[int] = None


@dataclass
class DynamoConfig:
    """DynamoDB configuration"""
    point_in_time_recovery: bool
    deletion_protection: bool


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    log_retention_days: int
    enable_detailed_monitoring: bool
    create_alarms: bool


@dataclass
class EnvironmentConfig:
    """Complete environment configuration"""
    environment: str
    region: str
    company: str
    tenant: str
    sms_config: SMSConfig
    lambda_config: LambdaConfig
    dynamo_config: DynamoConfig
    monitoring_config: MonitoringConfig
    tags: Dict[str, str]


# ===========================================
# DEVELOPMENT ENVIRONMENT
# ===========================================

DEVELOPMENT_CONFIG = EnvironmentConfig(
    environment='dev',
    region='us-east-1',
    company='your-company',
    tenant='dev-tenant',
    sms_config=SMSConfig(
        monthly_spend_limit=10,  # $10 for development
        default_sms_type='Transactional',
        delivery_status_sampling_rate=100,
        default_sender_id='DEVBOT'
    ),
    lambda_config=LambdaConfig(
        timeout=30,
        memory_size=256,
        # No reserved concurrency for dev
    ),
    dynamo_config=DynamoConfig(
        point_in_time_recovery=False,  # Cost optimization for dev
        deletion_protection=False
    ),
    monitoring_config=MonitoringConfig(
        log_retention_days=7,  # Short retention for dev
        enable_detailed_monitoring=False,
        create_alarms=False
    ),
    tags={
        'Environment': 'Development',
        'CostCenter': 'engineering-dev'
    }
)

# ===========================================
# STAGING ENVIRONMENT
# ===========================================

STAGING_CONFIG = EnvironmentConfig(
    environment='staging',
    region='us-east-1',
    company='your-company',
    tenant='staging-tenant',
    sms_config=SMSConfig(
        monthly_spend_limit=50,  # $50 for staging
        default_sms_type='Transactional',
        delivery_status_sampling_rate=100,
        default_sender_id='STGBOT'
    ),
    lambda_config=LambdaConfig(
        timeout=30,
        memory_size=512,
        reserved_concurrency=10  # Limited concurrency for staging
    ),
    dynamo_config=DynamoConfig(
        point_in_time_recovery=True,
        deletion_protection=False
    ),
    monitoring_config=MonitoringConfig(
        log_retention_days=14,
        enable_detailed_monitoring=True,
        create_alarms=True
    ),
    tags={
        'Environment': 'Staging',
        'CostCenter': 'engineering-staging',
        'BackupRequired': 'true'
    }
)

# ===========================================
# PRODUCTION ENVIRONMENT
# ===========================================

PRODUCTION_CONFIG = EnvironmentConfig(
    environment='prod',
    region='us-east-1',
    company='your-company',
    tenant='prod-tenant',
    sms_config=SMSConfig(
        monthly_spend_limit=1000,  # $1000 for production
        default_sms_type='Transactional',
        delivery_status_sampling_rate=100,
        default_sender_id='AIBOT'
    ),
    lambda_config=LambdaConfig(
        timeout=30,
        memory_size=1024,
        reserved_concurrency=100  # Higher concurrency for production
    ),
    dynamo_config=DynamoConfig(
        point_in_time_recovery=True,
        deletion_protection=True  # Protect production data
    ),
    monitoring_config=MonitoringConfig(
        log_retention_days=90,  # Longer retention for production
        enable_detailed_monitoring=True,
        create_alarms=True
    ),
    tags={
        'Environment': 'Production',
        'CostCenter': 'engineering-prod',
        'BackupRequired': 'true',
        'Compliance': 'required',
        'DataClassification': 'confidential'
    }
)

# ===========================================
# CONFIGURATION FACTORY
# ===========================================

def get_environment_config(environment: str) -> EnvironmentConfig:
    """Get configuration for the specified environment"""
    env_lower = environment.lower()
    
    if env_lower in ['dev', 'development']:
        return DEVELOPMENT_CONFIG
    elif env_lower in ['staging', 'stage']:
        return STAGING_CONFIG
    elif env_lower in ['prod', 'production']:
        return PRODUCTION_CONFIG
    else:
        raise ValueError(f"Unknown environment: {environment}. Supported: dev, staging, prod")


# ===========================================
# VALIDATION
# ===========================================

def validate_environment_config(config: EnvironmentConfig) -> None:
    """Validate environment configuration"""
    
    # Validate SMS spend limits
    if config.sms_config.monthly_spend_limit <= 0:
        raise ValueError('SMS monthly spend limit must be greater than 0')

    # Validate Lambda configuration
    if config.lambda_config.timeout < 1 or config.lambda_config.timeout > 900:
        raise ValueError('Lambda timeout must be between 1 and 900 seconds')

    if config.lambda_config.memory_size < 128 or config.lambda_config.memory_size > 10240:
        raise ValueError('Lambda memory size must be between 128 and 10240 MB')

    # Validate log retention
    valid_retention_days = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]
    if config.monitoring_config.log_retention_days not in valid_retention_days:
        raise ValueError(f"Invalid log retention days: {config.monitoring_config.log_retention_days}")

    print(f"✅ Environment configuration validated for: {config.environment}")


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def get_available_environments() -> list[str]:
    """Get all available environments"""
    return ['dev', 'staging', 'prod']


def is_production(environment: str) -> bool:
    """Check if environment is production"""
    return environment.lower() in ['prod', 'production']


def get_removal_policy(environment: str) -> str:
    """Get environment-specific resource removal policy"""
    if is_production(environment):
        return 'RETAIN'  # Protect production resources
    return 'DESTROY'  # Allow cleanup for dev/staging
