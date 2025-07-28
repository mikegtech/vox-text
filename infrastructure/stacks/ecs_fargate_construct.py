"""
ECS Fargate Construct for SMS Bot

Creates an ECS Fargate service for handling SMS webhooks with Cloudflare Tunnel ingress.
No public load balancer needed - Cloudflare Tunnel handles ingress securely.
"""
from typing import Optional, Dict, Any, List
import aws_cdk as cdk
from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_servicediscovery as servicediscovery,
    aws_secretsmanager as secretsmanager,
    Duration
)
from constructs import Construct

from m3_aws_standards import NamingConvention, TaggingStrategy, ServiceType


class ECSFargateConstruct(Construct):
    """
    ECS Fargate construct for SMS Bot webhooks
    
    Creates an ECS Fargate service with:
    - Containerized SMS webhook handler
    - Service discovery for internal communication
    - CloudWatch logging
    - Secrets management for configuration
    - No public load balancer (Cloudflare Tunnel handles ingress)
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        naming: NamingConvention,
        tagging: TaggingStrategy,
        environment: str,
        conversations_table_name: str,
        analytics_table_name: str,
        inbound_sns_topic_arn: str,
        delivery_sns_topic_arn: str,
        kms_key_arn: str,
        **kwargs
    ):
        super().__init__(scope, construct_id)
        
        self.naming = naming
        self.tagging = tagging
        self.environment = environment
        self.conversations_table_name = conversations_table_name
        self.analytics_table_name = analytics_table_name
        self.inbound_sns_topic_arn = inbound_sns_topic_arn
        self.delivery_sns_topic_arn = delivery_sns_topic_arn
        self.kms_key_arn = kms_key_arn
        
        # Create ECS infrastructure
        self._create_vpc_and_networking()
        self._create_ecs_cluster()
        self._create_secrets()
        self._create_task_definition()
        self._create_service()
        self._create_service_discovery()
        
        # Set internal service URL for Cloudflare Tunnel
        self.service_url = f"http://{self.service_name}.{self.namespace_name}:8080"
        self.health_url = f"http://{self.service_name}.{self.namespace_name}:8080/health"
    
    def _create_vpc_and_networking(self) -> None:
        """Create VPC and networking components"""
        
        # Use default VPC (free)
        self.vpc = ec2.Vpc.from_lookup(
            self,
            "DefaultVPC",
            is_default=True
        )
        
        # Security group for ECS tasks
        self.security_group = ec2.SecurityGroup(
            self,
            "ECSSecurityGroup",
            security_group_name=self.naming.resource(ServiceType.NETWORK, "sg", "ecs-tasks"),
            vpc=self.vpc,
            description="Security group for SMS Bot ECS tasks",
            allow_all_outbound=True
        )
        
        # Allow inbound HTTP traffic on port 8080 (for Cloudflare Tunnel)
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8080),
            description="HTTP traffic for SMS Bot webhooks"
        )
        
        # Allow inbound health check traffic
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8080),
            description="Health check traffic"
        )
        
        # Apply tags
        self.tagging.apply_to(self.security_group)
    
    def _create_ecs_cluster(self) -> None:
        """Create ECS cluster"""
        
        self.cluster = ecs.Cluster(
            self,
            "SMSBotCluster",
            cluster_name=self.naming.resource(ServiceType.COMPUTE, "cluster", "smsbot"),
            vpc=self.vpc,
            enable_fargate_capacity_providers=True,
            container_insights=True if self.environment == "prod" else False
        )
        
        # Apply tags
        self.tagging.apply_to(self.cluster)
    
    def _create_secrets(self) -> None:
        """Create secrets for application configuration"""
        
        # Telnyx API configuration secret
        self.telnyx_secret = secretsmanager.Secret(
            self,
            "TelnyxSecret",
            secret_name=self.naming.resource(ServiceType.SECURITY, "secret", "telnyx"),
            description="Telnyx API configuration for SMS Bot",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": "", "webhook_secret": ""}',
                generate_string_key="placeholder",
                exclude_characters=' %+~`#$&*()|[]{}:;<>?!\'/@"\\',
                include_space=False,
                password_length=32
            )
        )
        
        # Application configuration secret
        self.app_secret = secretsmanager.Secret(
            self,
            "AppSecret",
            secret_name=self.naming.resource(ServiceType.SECURITY, "secret", "app-config"),
            description="Application configuration for SMS Bot",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"jwt_secret": "", "encryption_key": ""}',
                generate_string_key="jwt_secret",
                exclude_characters=' %+~`#$&*()|[]{}:;<>?!\'/@"\\',
                include_space=False,
                password_length=64
            )
        )
        
        # Apply tags
        self.tagging.apply_to(self.telnyx_secret)
        self.tagging.apply_to(self.app_secret)
    
    def _create_task_definition(self) -> None:
        """Create ECS task definition"""
        
        # Task execution role
        self.execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            role_name=self.naming.iam_role("ecs-execution", ServiceType.COMPUTE),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )
        
        # Task role (for application permissions)
        self.task_role = iam.Role(
            self,
            "TaskRole",
            role_name=self.naming.iam_role("ecs-task", ServiceType.COMPUTE),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        
        # Grant permissions to task role
        self.task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    f"arn:aws:dynamodb:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:table/{self.conversations_table_name}",
                    f"arn:aws:dynamodb:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:table/{self.analytics_table_name}"
                ]
            )
        )
        
        # Grant SNS permissions
        self.task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sns:Publish"
                ],
                resources=[
                    self.inbound_sns_topic_arn,
                    self.delivery_sns_topic_arn
                ]
            )
        )
        
        # Grant KMS permissions
        self.task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey"
                ],
                resources=[self.kms_key_arn]
            )
        )
        
        # Grant secrets access
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.telnyx_secret.secret_arn,
                    self.app_secret.secret_arn
                ]
            )
        )
        
        # CloudWatch log group
        self.log_group = logs.LogGroup(
            self,
            "TaskLogGroup",
            log_group_name=self.naming.log_group("ecs", "smsbot"),
            retention=logs.RetentionDays.DAYS_7 if self.environment == "dev" else logs.RetentionDays.DAYS_30,
            removal_policy=cdk.RemovalPolicy.DESTROY if self.environment == "dev" else cdk.RemovalPolicy.RETAIN
        )
        
        # Task definition
        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            family=self.naming.resource(ServiceType.COMPUTE, "task", "smsbot"),
            cpu=256 if self.environment == "dev" else 512,
            memory_limit_mib=512 if self.environment == "dev" else 1024,
            execution_role=self.execution_role,
            task_role=self.task_role
        )
        
        # Container definition
        self.container = self.task_definition.add_container(
            "SMSBotContainer",
            container_name="smsbot",
            # Use a placeholder image - you'll need to build and push your actual image
            image=ecs.ContainerImage.from_registry("nginx:alpine"),  # Replace with your image
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="smsbot",
                log_group=self.log_group
            ),
            environment={
                "ENVIRONMENT": self.environment,
                "AWS_REGION": cdk.Aws.REGION,
                "CONVERSATIONS_TABLE": self.conversations_table_name,
                "ANALYTICS_TABLE": self.analytics_table_name,
                "INBOUND_SNS_TOPIC": self.inbound_sns_topic_arn,
                "DELIVERY_SNS_TOPIC": self.delivery_sns_topic_arn,
                "PORT": "8080"
            },
            secrets={
                "TELNYX_CONFIG": ecs.Secret.from_secrets_manager(self.telnyx_secret),
                "APP_CONFIG": ecs.Secret.from_secrets_manager(self.app_secret)
            },
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60)
            )
        )
        
        # Add port mapping
        self.container.add_port_mappings(
            ecs.PortMapping(
                container_port=8080,
                protocol=ecs.Protocol.TCP
            )
        )
        
        # Apply tags
        self.tagging.apply_to(self.execution_role)
        self.tagging.apply_to(self.task_role)
        self.tagging.apply_to(self.log_group)
    
    def _create_service(self) -> None:
        """Create ECS service"""
        
        self.service_name = self.naming.resource(ServiceType.COMPUTE, "service", "smsbot")
        
        self.service = ecs.FargateService(
            self,
            "SMSBotService",
            service_name=self.service_name,
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=1 if self.environment == "dev" else 2,
            assign_public_ip=True,  # Needed for internet access in default VPC
            security_groups=[self.security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC  # Use public subnets in default VPC
            ),
            enable_logging=True,
            circuit_breaker=ecs.DeploymentCircuitBreaker(
                rollback=True
            ),
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE",
                    weight=1
                )
            ]
        )
        
        # Apply tags
        self.tagging.apply_to(self.service)
    
    def _create_service_discovery(self) -> None:
        """Create service discovery for internal communication"""
        
        # Create private DNS namespace
        self.namespace_name = f"smsbot-{self.environment}.local"
        self.namespace = servicediscovery.PrivateDnsNamespace(
            self,
            "ServiceNamespace",
            name=self.namespace_name,
            vpc=self.vpc,
            description=f"Service discovery namespace for SMS Bot {self.environment}"
        )
        
        # Create service discovery service
        self.discovery_service = self.namespace.create_service(
            "SMSBotDiscovery",
            name=self.service_name,
            dns_record_type=servicediscovery.DnsRecordType.A,
            dns_ttl=Duration.seconds(60),
            health_check_custom_config=servicediscovery.HealthCheckCustomConfig(
                failure_threshold=3
            )
        )
        
        # Associate service with service discovery
        self.service.associate_cloud_map_service(
            service=self.discovery_service
        )
        
        # Apply tags
        self.tagging.apply_to(self.namespace)
