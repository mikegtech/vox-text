"""
SMS Bot Infrastructure Stack

This stack creates all the AWS resources needed for the SMS Bot system
using our shared naming and tagging standards.
"""
from typing import Optional
import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_kms as kms,
    RemovalPolicy,
    Duration
)
from constructs import Construct

from m3_aws_standards import (
    StandardizedStack,
    StandardizedLambda,
    StandardizedTable,
    StandardizedTopic,
    ServiceType
)
from config.environments import EnvironmentConfig, get_removal_policy
from .ecs_fargate_construct import ECSFargateConstruct
from .api_gateway_construct import ApiGatewayConstruct


class SMSBotStack(StandardizedStack):
    """
    Main SMS Bot infrastructure stack
    
    Creates all necessary AWS resources for the SMS Bot system including:
    - SNS topics for inbound SMS and delivery status
    - Lambda functions for message processing
    - DynamoDB tables for conversation storage
    - IAM roles and policies
    - CloudWatch monitoring and dashboards
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project: str,
        environment: str,
        company: str,
        service: ServiceType,
        env_config: EnvironmentConfig,
        tenant: Optional[str] = None,
        owner: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            scope,
            construct_id,
            project=project,
            environment=environment,
            company=company,
            service=service,
            tenant=tenant,
            owner=owner,
            **kwargs
        )
        
        self.env_config = env_config
        self.removal_policy = RemovalPolicy.RETAIN if get_removal_policy(environment) == 'RETAIN' else RemovalPolicy.DESTROY
        
        # Create KMS keys for encryption
        self._create_kms_keys()
        
        # Create all infrastructure components
        self._create_iam_roles()
        self._create_sns_topics()
        self._create_dynamodb_tables()
        self._create_lambda_functions()
        self._create_api_gateway()
        self._create_ecs_fargate()
        self._create_monitoring()
        
        # Output important information
        self._create_outputs()
    
    def _create_kms_keys(self) -> None:
        """Create KMS keys for encryption"""
        
        # Main SMS Bot KMS key for general encryption
        self.sms_bot_key = kms.Key(
            self,
            "SMSBotKey",
            alias=self.naming.resource(ServiceType.SECURITY, "key", "smsbot"),
            description=f"SMS Bot encryption key for {self.env_config.environment} environment",
            enable_key_rotation=True,
            removal_policy=self.removal_policy
        )
        
        # SNS-specific KMS key (optional - can use main key)
        self.sns_key = kms.Key(
            self,
            "SNSKey", 
            alias=self.naming.resource(ServiceType.SECURITY, "key", "sns"),
            description=f"SNS encryption key for {self.env_config.environment} environment",
            enable_key_rotation=True,
            removal_policy=self.removal_policy
        )
        
        # DynamoDB-specific KMS key (optional - can use main key)
        self.dynamodb_key = kms.Key(
            self,
            "DynamoDBKey",
            alias=self.naming.resource(ServiceType.SECURITY, "key", "dynamodb"),
            description=f"DynamoDB encryption key for {self.env_config.environment} environment", 
            enable_key_rotation=True,
            removal_policy=self.removal_policy
        )
        
        # CloudWatch Logs KMS key
        self.logs_key = kms.Key(
            self,
            "LogsKey",
            alias=self.naming.resource(ServiceType.SECURITY, "key", "logs"),
            description=f"CloudWatch Logs encryption key for {self.env_config.environment} environment",
            enable_key_rotation=True,
            removal_policy=self.removal_policy
        )
        
        # Grant CloudWatch Logs service permission to use the key
        self.logs_key.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowCloudWatchLogs",
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ServicePrincipal(f"logs.{self.region}.amazonaws.com")
                ],
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey"
                ],
                resources=["*"],
                conditions={
                    "ArnEquals": {
                        "kms:EncryptionContext:aws:logs:arn": f"arn:aws:logs:{self.region}:{self.account}:log-group:*"
                    }
                }
            )
        )
        
        # Apply tags to all KMS keys
        for key in [self.sms_bot_key, self.sns_key, self.dynamodb_key, self.logs_key]:
            self.tagging.apply_to(key)
    
    def _create_iam_roles(self) -> None:
        """Create IAM roles for SMS Bot services"""
        
        # SNS logging role
        self.sns_logging_role = iam.Role(
            self,
            "SNSLoggingRole",
            role_name=self.naming.iam_role("sns-logging", ServiceType.SECURITY),
            assumed_by=iam.ServicePrincipal("sns.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonSNSRole")
            ]
        )
        
        # Lambda execution role
        self.lambda_execution_role = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name=self.naming.iam_role("lambda-execution", ServiceType.COMPUTE),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Apply tags to roles
        self.tagging.apply_to(self.sns_logging_role)
        self.tagging.apply_to(self.lambda_execution_role)
    
    def _create_sns_topics(self) -> None:
        """Create SNS topics for SMS messaging"""
        
        # Inbound SMS topic with KMS encryption
        self.inbound_sms_topic = StandardizedTopic(
            self,
            "InboundSMSTopic",
            identifier="inbound-sms",
            naming=self.naming,
            tagging=self.tagging,
            display_name="SMS Bot Inbound Messages",
            master_key=self.sns_key
        )
        
        # Delivery status topic with KMS encryption
        self.delivery_status_topic = StandardizedTopic(
            self,
            "DeliveryStatusTopic", 
            identifier="delivery-status",
            naming=self.naming,
            tagging=self.tagging,
            display_name="SMS Bot Delivery Status",
            master_key=self.sns_key
        )
        
        # Configure SNS logging
        self._configure_sns_logging()
    
    def _configure_sns_logging(self) -> None:
        """Configure SNS delivery status logging"""
        
        # Create log group for SNS delivery logs with KMS encryption
        self.sns_log_group = logs.LogGroup(
            self,
            "SNSDeliveryLogGroup",
            log_group_name=self.naming.log_group("messaging", "sns"),
            retention=logs.RetentionDays(f"DAYS_{self.env_config.monitoring_config.log_retention_days}"),
            encryption_key=self.logs_key,
            removal_policy=self.removal_policy
        )
        
        # Apply tags to log group
        self.tagging.apply_to(self.sns_log_group)
    
    def _create_dynamodb_tables(self) -> None:
        """Create DynamoDB tables for data storage"""
        
        # Conversations table with KMS encryption
        self.conversations_table = StandardizedTable(
            self,
            "ConversationsTable",
            identifier="conversations",
            naming=self.naming,
            tagging=self.tagging,
            partition_key=dynamodb.Attribute(
                name="conversation_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=self.env_config.dynamo_config.point_in_time_recovery,
            deletion_protection=self.env_config.dynamo_config.deletion_protection,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            removal_policy=self.removal_policy
        )
        
        # Analytics table for message metrics with KMS encryption
        self.analytics_table = StandardizedTable(
            self,
            "AnalyticsTable",
            identifier="analytics",
            naming=self.naming,
            tagging=self.tagging,
            partition_key=dynamodb.Attribute(
                name="metric_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=self.env_config.dynamo_config.point_in_time_recovery,
            deletion_protection=self.env_config.dynamo_config.deletion_protection,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.dynamodb_key,
            removal_policy=self.removal_policy
        )
    
    def _create_lambda_functions(self) -> None:
        """Create Lambda functions for SMS processing"""
        
        # SMS message handler
        self.sms_handler = StandardizedLambda(
            self,
            "SMSHandler",
            identifier="sms-handler",
            naming=self.naming,
            tagging=self.tagging,
            lambda_service=ServiceType.MESSAGING,
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset("lambda"),
            handler="sms_handler.handler",
            timeout=Duration.seconds(self.env_config.lambda_config.timeout),
            memory_size=self.env_config.lambda_config.memory_size,
            reserved_concurrent_executions=self.env_config.lambda_config.reserved_concurrency,
            role=self.lambda_execution_role,
            environment={
                "CONVERSATIONS_TABLE": self.conversations_table.table.table_name,
                "ANALYTICS_TABLE": self.analytics_table.table.table_name,
                "INBOUND_TOPIC_ARN": self.inbound_sms_topic.topic.topic_arn,
                "ENVIRONMENT": self.env_config.environment,
                "SMS_SENDER_ID": self.env_config.sms_config.default_sender_id or "SMSBOT"
            }
        )
        
        # Grant permissions to Lambda
        self.conversations_table.table.grant_read_write_data(self.sms_handler.function)
        self.analytics_table.table.grant_read_write_data(self.sms_handler.function)
        self.inbound_sms_topic.topic.grant_publish(self.sms_handler.function)
        self.delivery_status_topic.topic.grant_publish(self.sms_handler.function)
        
        # Grant KMS permissions to Lambda
        self.dynamodb_key.grant_encrypt_decrypt(self.sms_handler.function)
        self.sns_key.grant_encrypt_decrypt(self.sms_handler.function)
        
        # Subscribe Lambda to SNS topics
        self.inbound_sms_topic.topic.add_subscription(
            sns.LambdaSubscription(self.sms_handler.function)
        )
    
    def _create_api_gateway(self) -> None:
        """Create API Gateway for HTTP/REST endpoints (for Traefik routing)"""
        
        self.api_gateway = ApiGatewayConstruct(
            self,
            "TelnyxWebhookApi",
            naming=self.naming,
            tagging=self.tagging,
            sms_handler_function=self.sms_handler.function,
            environment=self.env_config.environment,
            conversations_table_name=self.conversations_table.table.table_name,
            analytics_table_name=self.analytics_table.table.table_name
        )
        
        # Grant API Gateway Lambda functions access to DynamoDB and KMS
        self.conversations_table.table.grant_read_write_data(self.api_gateway.authorizer_function)
        self.analytics_table.table.grant_read_write_data(self.api_gateway.fallback_function)
        self.dynamodb_key.grant_encrypt_decrypt(self.api_gateway.authorizer_function)
        self.dynamodb_key.grant_encrypt_decrypt(self.api_gateway.fallback_function)
    
    def _create_ecs_fargate(self) -> None:
        """Create ECS Fargate service for webhook endpoints"""
        
        self.ecs_fargate = ECSFargateConstruct(
            self,
            "SMSBotECS",
            naming=self.naming,
            tagging=self.tagging,
            environment=self.env_config.environment,
            conversations_table_name=self.conversations_table.table.table_name,
            analytics_table_name=self.analytics_table.table.table_name,
            inbound_sns_topic_arn=self.inbound_sms_topic.topic.topic_arn,
            delivery_sns_topic_arn=self.delivery_status_topic.topic.topic_arn,
            kms_key_arn=self.sms_bot_key.key_arn
        )
    
    def _create_monitoring(self) -> None:
        """Create CloudWatch monitoring and dashboards"""
        
        if not self.env_config.monitoring_config.create_alarms:
            return
        
        # Create CloudWatch dashboard
        self.dashboard = cloudwatch.Dashboard(
            self,
            "SMSBotDashboard",
            dashboard_name=self.naming.resource(ServiceType.MONITORING, "dashboard", "operations")
        )
        
        # Lambda metrics
        lambda_error_metric = self.sms_handler.function.metric_errors(
            period=Duration.minutes(5)
        )
        
        lambda_duration_metric = self.sms_handler.function.metric_duration(
            period=Duration.minutes(5)
        )
        
        # DynamoDB metrics
        conversations_read_metric = self.conversations_table.table.metric_consumed_read_capacity_units(
            period=Duration.minutes(5)
        )
        
        # Add widgets to dashboard
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Errors",
                left=[lambda_error_metric],
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="Lambda Duration",
                left=[lambda_duration_metric],
                width=12,
                height=6
            ),
            cloudwatch.GraphWidget(
                title="DynamoDB Read Capacity",
                left=[conversations_read_metric],
                width=12,
                height=6
            )
        )
        
        # Create alarms for production
        if self.env_config.environment == 'prod':
            self._create_alarms()
        
        # Apply tags to dashboard
        self.tagging.apply_to(self.dashboard)
    
    def _create_alarms(self) -> None:
        """Create CloudWatch alarms for production monitoring"""
        
        # Lambda error alarm
        lambda_error_alarm = cloudwatch.Alarm(
            self,
            "LambdaErrorAlarm",
            alarm_name=self.naming.resource(ServiceType.MONITORING, "alarm", "lambda-errors"),
            metric=self.sms_handler.function.metric_errors(
                period=Duration.minutes(5)
            ),
            threshold=5,
            evaluation_periods=2,
            alarm_description="SMS Handler Lambda function errors"
        )
        
        # DynamoDB throttle alarm
        dynamo_throttle_alarm = cloudwatch.Alarm(
            self,
            "DynamoThrottleAlarm",
            alarm_name=self.naming.resource(ServiceType.MONITORING, "alarm", "dynamo-throttles"),
            metric=self.conversations_table.table.metric_throttled_requests(
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            alarm_description="DynamoDB throttling detected"
        )
        
        # Apply tags to alarms
        self.tagging.apply_to(lambda_error_alarm)
        self.tagging.apply_to(dynamo_throttle_alarm)
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for important resources"""
        
        cdk.CfnOutput(
            self,
            "InboundSMSTopicArn",
            value=self.inbound_sms_topic.topic.topic_arn,
            description="ARN of the inbound SMS topic",
            export_name=f"{self.stack_name}-InboundSMSTopicArn"
        )
        
        cdk.CfnOutput(
            self,
            "ConversationsTableName",
            value=self.conversations_table.table.table_name,
            description="Name of the conversations DynamoDB table",
            export_name=f"{self.stack_name}-ConversationsTableName"
        )
        
        cdk.CfnOutput(
            self,
            "SMSHandlerFunctionName",
            value=self.sms_handler.function.function_name,
            description="Name of the SMS handler Lambda function",
            export_name=f"{self.stack_name}-SMSHandlerFunctionName"
        )
        
        # KMS Key outputs
        cdk.CfnOutput(
            self,
            "SMSBotKMSKeyId",
            value=self.sms_bot_key.key_id,
            description="ID of the main SMS Bot KMS key",
            export_name=f"{self.stack_name}-SMSBotKMSKeyId"
        )
        
        cdk.CfnOutput(
            self,
            "SMSBotKMSKeyArn",
            value=self.sms_bot_key.key_arn,
            description="ARN of the main SMS Bot KMS key",
            export_name=f"{self.stack_name}-SMSBotKMSKeyArn"
        )
        
        cdk.CfnOutput(
            self,
            "DynamoDBKMSKeyId",
            value=self.dynamodb_key.key_id,
            description="ID of the DynamoDB KMS key",
            export_name=f"{self.stack_name}-DynamoDBKMSKeyId"
        )
        
        cdk.CfnOutput(
            self,
            "SNSKMSKeyId",
            value=self.sns_key.key_id,
            description="ID of the SNS KMS key",
            export_name=f"{self.stack_name}-SNSKMSKeyId"
        )
        
        # API Gateway outputs (for Traefik routing)
        cdk.CfnOutput(
            self,
            "ApiGatewayUrl",
            value=self.api_gateway.api.url,
            description="Public API Gateway URL for Traefik routing",
            export_name=f"{self.stack_name}-ApiGatewayUrl"
        )
        
        cdk.CfnOutput(
            self,
            "WebhookEndpoint",
            value=self.api_gateway.webhook_url,
            description="Telnyx SMS webhook endpoint URL (for Traefik)",
            export_name=f"{self.stack_name}-WebhookEndpoint"
        )
        
        cdk.CfnOutput(
            self,
            "FallbackEndpoint",
            value=self.api_gateway.fallback_url,
            description="Telnyx fallback webhook endpoint URL (for Traefik)",
            export_name=f"{self.stack_name}-FallbackEndpoint"
        )
        
        cdk.CfnOutput(
            self,
            "HealthCheckEndpoint",
            value=self.api_gateway.health_url,
            description="API health check endpoint (for Traefik)",
            export_name=f"{self.stack_name}-HealthCheckEndpoint"
        )
        
        cdk.CfnOutput(
            self,
            "AuthorizerFunctionArn",
            value=self.api_gateway.authorizer_function.function_arn,
            description="ARN of the API Gateway authorizer Lambda function",
            export_name=f"{self.stack_name}-AuthorizerFunctionArn"
        )
        
        # ECS Fargate outputs (for containerized services)
        cdk.CfnOutput(
            self,
            "ECSClusterName",
            value=self.ecs_fargate.cluster.cluster_name,
            description="Name of the ECS cluster",
            export_name=f"{self.stack_name}-ECSClusterName"
        )
        
        cdk.CfnOutput(
            self,
            "ECSServiceName",
            value=self.ecs_fargate.service.service_name,
            description="Name of the ECS service",
            export_name=f"{self.stack_name}-ECSServiceName"
        )
        
        cdk.CfnOutput(
            self,
            "ServiceDiscoveryURL",
            value=self.ecs_fargate.service_url,
            description="Internal service discovery URL for ECS service",
            export_name=f"{self.stack_name}-ServiceDiscoveryURL"
        )
        
        cdk.CfnOutput(
            self,
            "ECSHealthCheckURL",
            value=self.ecs_fargate.health_url,
            description="Internal ECS health check URL",
            export_name=f"{self.stack_name}-ECSHealthCheckURL"
        )
        
        cdk.CfnOutput(
            self,
            "TelnyxSecretArn",
            value=self.ecs_fargate.telnyx_secret.secret_arn,
            description="ARN of the Telnyx configuration secret",
            export_name=f"{self.stack_name}-TelnyxSecretArn"
        )
        
        cdk.CfnOutput(
            self,
            "AppSecretArn",
            value=self.ecs_fargate.app_secret.secret_arn,
            description="ARN of the application configuration secret",
            export_name=f"{self.stack_name}-AppSecretArn"
        )
        
        if hasattr(self, 'dashboard'):
            cdk.CfnOutput(
                self,
                "DashboardURL",
                value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboard.dashboard_name}",
                description="URL to the CloudWatch dashboard",
                export_name=f"{self.stack_name}-DashboardURL"
            )
