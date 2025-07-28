"""
API Gateway Construct for SMS Bot

Creates a private API Gateway in the default VPC without custom domain or certificates.
Handles Telnyx webhook endpoints with proper authentication and routing.
"""
from typing import Optional, Dict, Any
import aws_cdk as cdk
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_logs as logs,
    Duration
)
from constructs import Construct

from m3_aws_standards import NamingConvention, TaggingStrategy, ServiceType


class ApiGatewayConstruct(Construct):
    """
    API Gateway construct for SMS Bot webhooks
    
    Creates a public REST API with:
    - Telnyx webhook endpoints
    - Lambda authorizer for security
    - Proper logging and monitoring
    - No VPC costs (public regional API)
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        naming: NamingConvention,
        tagging: TaggingStrategy,
        sms_handler_function: _lambda.Function,
        environment: str,
        conversations_table_name: str,
        analytics_table_name: str,
        **kwargs
    ):
        super().__init__(scope, construct_id)
        
        self.naming = naming
        self.tagging = tagging
        self.environment = environment
        self.sms_handler_function = sms_handler_function
        self.conversations_table_name = conversations_table_name
        self.analytics_table_name = analytics_table_name
        
        # Create API Gateway components
        self._create_authorizer_function()
        self._create_fallback_function()
        self._create_api_gateway()
        self._create_resources_and_methods()
        
        # Set up URLs (no custom domain)
        self.webhook_url = f"{self.api.url}webhooks/telnyx/sms"
        self.fallback_url = f"{self.api.url}webhooks/telnyx/fallback"
        self.health_url = f"{self.api.url}health"
    
    def _create_authorizer_function(self) -> None:
        """Create Lambda authorizer function for API Gateway"""
        
        # IAM role for authorizer
        authorizer_role = iam.Role(
            self,
            "AuthorizerRole",
            role_name=self.naming.iam_role("api-authorizer", ServiceType.SECURITY),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Authorizer Lambda function
        self.authorizer_function = _lambda.Function(
            self,
            "AuthorizerFunction",
            function_name=self.naming.lambda_function("api-authorizer", ServiceType.SECURITY),
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="authorizer.handler",
            code=_lambda.Code.from_asset("lambda/authorizer"),
            role=authorizer_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "ENVIRONMENT": self.environment,
                "LOG_LEVEL": "INFO" if self.environment == "prod" else "DEBUG"
            }
        )
        
        # Apply tags
        self.tagging.apply_to(self.authorizer_function)
        self.tagging.apply_to(authorizer_role)
    
    def _create_fallback_function(self) -> None:
        """Create fallback Lambda function for dead letter queue"""
        
        # IAM role for fallback function
        fallback_role = iam.Role(
            self,
            "FallbackRole",
            role_name=self.naming.iam_role("api-fallback", ServiceType.COMPUTE),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add DynamoDB permissions for logging failed requests
        fallback_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem"
                ],
                resources=[
                    f"arn:aws:dynamodb:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:table/{self.analytics_table_name}"
                ]
            )
        )
        
        # Fallback Lambda function
        self.fallback_function = _lambda.Function(
            self,
            "FallbackFunction",
            function_name=self.naming.lambda_function("api-fallback", ServiceType.COMPUTE),
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="fallback.handler",
            code=_lambda.Code.from_asset("lambda/fallback"),
            role=fallback_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "ENVIRONMENT": self.environment,
                "ANALYTICS_TABLE": self.analytics_table_name,
                "LOG_LEVEL": "INFO" if self.environment == "prod" else "DEBUG"
            }
        )
        
        # Apply tags
        self.tagging.apply_to(self.fallback_function)
        self.tagging.apply_to(fallback_role)
    
    def _create_api_gateway(self) -> None:
        """Create the main API Gateway (public, no VPC costs)"""
        
        # Create CloudWatch log group for API Gateway
        api_log_group = logs.LogGroup(
            self,
            "ApiLogGroup",
            log_group_name=self.naming.log_group("api", "gateway"),
            retention=logs.RetentionDays.DAYS_7 if self.environment == "dev" else logs.RetentionDays.DAYS_30,
            removal_policy=cdk.RemovalPolicy.DESTROY if self.environment == "dev" else cdk.RemovalPolicy.RETAIN
        )
        
        # Create the REST API (public - no VPC costs)
        self.api = apigateway.RestApi(
            self,
            "TelnyxWebhookApi",
            rest_api_name=self.naming.resource(ServiceType.NETWORK, "api", "telnyx-webhooks"),
            description=f"SMS Bot Telnyx webhook API for {self.environment} environment",
            # Public API configuration (no VPC endpoint needed)
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[apigateway.EndpointType.REGIONAL]
            ),
            # Logging configuration
            cloud_watch_role=True,
            deploy_options=apigateway.StageOptions(
                stage_name=self.environment,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                access_log_destination=apigateway.LogGroupLogDestination(api_log_group),
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True
                )
            ),
            # CORS configuration
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["*"],  # Telnyx webhook origins
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Telnyx-Signature"]
            )
        )
        
        # Apply tags
        self.tagging.apply_to(self.api)
        self.tagging.apply_to(api_log_group)
    
    def _create_resources_and_methods(self) -> None:
        """Create API resources and methods"""
        
        # Create Lambda authorizer
        authorizer = apigateway.RequestAuthorizer(
            self,
            "TelnyxAuthorizer",
            handler=self.authorizer_function,
            identity_sources=[
                apigateway.IdentitySource.header("Authorization"),
                apigateway.IdentitySource.header("X-Telnyx-Signature")
            ],
            results_cache_ttl=Duration.minutes(5)
        )
        
        # Health check endpoint (no auth required)
        health_resource = self.api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"status": "healthy", "timestamp": "$context.requestTime"}'
                        }
                    )
                ],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                )
            ]
        )
        
        # Webhooks resource
        webhooks_resource = self.api.root.add_resource("webhooks")
        telnyx_resource = webhooks_resource.add_resource("telnyx")
        
        # SMS webhook endpoint (with authorization)
        sms_resource = telnyx_resource.add_resource("sms")
        sms_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                self.sms_handler_function,
                proxy=True,
                integration_responses=[
                    apigateway.IntegrationResponse(status_code="200")
                ]
            ),
            authorizer=authorizer,
            method_responses=[
                apigateway.MethodResponse(status_code="200"),
                apigateway.MethodResponse(status_code="400"),
                apigateway.MethodResponse(status_code="401"),
                apigateway.MethodResponse(status_code="500")
            ]
        )
        
        # Fallback endpoint (with authorization)
        fallback_resource = telnyx_resource.add_resource("fallback")
        fallback_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                self.fallback_function,
                proxy=True,
                integration_responses=[
                    apigateway.IntegrationResponse(status_code="200")
                ]
            ),
            authorizer=authorizer,
            method_responses=[
                apigateway.MethodResponse(status_code="200"),
                apigateway.MethodResponse(status_code="400"),
                apigateway.MethodResponse(status_code="401"),
                apigateway.MethodResponse(status_code="500")
            ]
        )
        
        # Fallback health check (GET, no auth)
        fallback_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"status": "fallback-healthy", "timestamp": "$context.requestTime"}'
                        }
                    )
                ],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                )
            ]
        )
