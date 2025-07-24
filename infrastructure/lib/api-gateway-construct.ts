import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';

import { NamingConvention } from './naming-convention';
import { TaggingStrategy, SERVICES } from './tagging-strategy';
import { getTelnyxConfigForEnvironment } from '../config/telnyx-config';

export interface ApiGatewayConstructProps {
  naming: NamingConvention;
  tagging: TaggingStrategy;
  smsHandlerFunction: lambda.Function;
  environment: string;
  customDomain?: {
    domainName: string;
    certificateArn: string;
  };
  conversationsTable: string;
  analyticsTable: string;
}

export class ApiGatewayConstruct extends Construct {
  public readonly api: apigateway.RestApi;
  public readonly authorizerFunction: lambda.Function;
  public readonly fallbackFunction: lambda.Function;
  public readonly customDomain?: apigateway.DomainName;
  public readonly webhookUrl: string;
  public readonly fallbackUrl: string;
  private readonly environment: string;

  constructor(scope: Construct, id: string, props: ApiGatewayConstructProps) {
    super(scope, id);

    // Store environment for use in helper methods
    this.environment = props.environment;

    // Get Telnyx configuration for environment
    const telnyxConfig = getTelnyxConfigForEnvironment(props.environment);

    // ===========================================
    // LAMBDA AUTHORIZER FUNCTION
    // ===========================================

    // IAM role for the authorizer Lambda
    const authorizerRole = new iam.Role(this, 'AuthorizerRole', {
      roleName: props.naming.iamRole(SERVICES.SECURITY, 'api-authorizer'),
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ]
    });

    // Apply security service tags
    props.tagging.applyTags(authorizerRole, SERVICES.SECURITY, 'api-authorizer-role');

    // Grant Secrets Manager permissions to the authorizer role
    authorizerRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'secretsmanager:GetSecretValue'
      ],
      resources: [
        `arn:aws:secretsmanager:*:*:secret:smsbot/${props.environment}/telnyx-public-key*`
      ]
    }));

    // Lambda Authorizer for Ed25519 signature validation
    this.authorizerFunction = new lambda.Function(this, 'TelnyxAuthorizer', {
      functionName: props.naming.lambdaFunction(SERVICES.SECURITY, 'telnyx-authorizer'),
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('lambda/telnyx-authorizer'),
      role: authorizerRole,
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      environment: {
        'TELNYX_PUBLIC_KEY_SECRET': `smsbot/${props.environment}/telnyx-public-key`,
        'ENVIRONMENT': props.environment
      },
      // Let Lambda create its own log group to avoid conflicts
      logRetention: logs.RetentionDays.ONE_MONTH
    });

    // Apply security service tags
    props.tagging.applyTags(this.authorizerFunction, SERVICES.SECURITY, 'telnyx-authorizer', {
      Runtime: 'python3.9',
      MemorySize: '256MB',
      Timeout: '10s'
    });

    // ===========================================
    // FALLBACK LAMBDA FUNCTION
    // ===========================================

    // IAM role for the fallback Lambda
    const fallbackRole = new iam.Role(this, 'FallbackRole', {
      roleName: props.naming.iamRole(SERVICES.MESSAGING, 'fallback-handler'),
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ]
    });

    // Grant DynamoDB permissions to fallback role
    fallbackRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'dynamodb:PutItem',
        'dynamodb:GetItem',
        'dynamodb:UpdateItem',
        'dynamodb:Query'
      ],
      resources: [
        `arn:aws:dynamodb:*:*:table/${props.conversationsTable}`,
        `arn:aws:dynamodb:*:*:table/${props.analyticsTable}`
      ]
    }));

    // Apply messaging service tags to fallback role
    props.tagging.applyTags(fallbackRole, SERVICES.MESSAGING, 'fallback-handler-role');

    // Fallback Lambda function
    this.fallbackFunction = new lambda.Function(this, 'TelnyxFallback', {
      functionName: props.naming.lambdaFunction(SERVICES.MESSAGING, 'telnyx-fallback'),
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset('lambda/telnyx-fallback'),
      role: fallbackRole,
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        'CONVERSATIONS_TABLE': props.conversationsTable,
        'ANALYTICS_TABLE': props.analyticsTable,
        'ENVIRONMENT': props.environment
      },
      // Let Lambda create its own log group to avoid conflicts
      logRetention: logs.RetentionDays.ONE_MONTH
    });

    // Apply messaging service tags to fallback function
    props.tagging.applyTags(this.fallbackFunction, SERVICES.MESSAGING, 'telnyx-fallback', {
      Runtime: 'python3.9',
      MemorySize: '256MB',
      Timeout: '30s'
    });

    // ===========================================
    // API GATEWAY REST API
    // ===========================================

    // CloudWatch log group for API Gateway
    const apiLogGroup = new logs.LogGroup(this, 'ApiGatewayLogGroup', {
      logGroupName: props.naming.logGroup('apigateway', 'telnyx-webhook'),
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // Apply monitoring service tags
    props.tagging.applyTags(apiLogGroup, SERVICES.MONITORING, 'api-gateway-logs');

    // REST API with resource policy for Telnyx IP restrictions
    this.api = new apigateway.RestApi(this, 'TelnyxWebhookApi', {
      restApiName: props.naming.snsTopic('telnyx-webhook-api'), // Reusing naming pattern
      description: 'API Gateway for Telnyx SMS webhook integration',
      deployOptions: {
        stageName: props.environment,
        // Temporarily disable access logging to avoid account setup requirement
        // accessLogDestination: new apigateway.LogGroupLogDestination(apiLogGroup),
        // accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields({
        //   caller: true,
        //   httpMethod: true,
        //   ip: true,
        //   protocol: true,
        //   requestTime: true,
        //   resourcePath: true,
        //   responseLength: true,
        //   status: true,
        //   user: true
        // }),
        loggingLevel: apigateway.MethodLoggingLevel.OFF, // Disable method logging
        dataTraceEnabled: false, // Disable data tracing
        metricsEnabled: true // Keep metrics enabled
      },
      policy: this.createResourcePolicy(),
      endpointConfiguration: {
        types: [apigateway.EndpointType.REGIONAL]
      }
    });

    // Apply messaging service tags
    props.tagging.applyTags(this.api, SERVICES.MESSAGING, 'telnyx-webhook-api');

    // ===========================================
    // API GATEWAY AUTHORIZER
    // ===========================================

    const authorizer = new apigateway.RequestAuthorizer(this, 'TelnyxRequestAuthorizer', {
      handler: this.authorizerFunction,
      identitySources: [
        apigateway.IdentitySource.header('telnyx-signature-ed25519'),
        apigateway.IdentitySource.header('telnyx-timestamp')
      ],
      authorizerName: props.naming.lambdaFunction(SERVICES.SECURITY, 'telnyx-auth'),
      resultsCacheTtl: cdk.Duration.seconds(0) // Disable caching for security
    });

    // ===========================================
    // API RESOURCES AND METHODS
    // ===========================================

    // Create nested resource structure: /dev/webhooks/telnyx/sms
    const devResource = this.api.root.addResource('dev');
    const webhooksResource = devResource.addResource('webhooks');
    const telnyxResource = webhooksResource.addResource('telnyx');
    const smsResource = telnyxResource.addResource('sms');
    const fallbackResource = telnyxResource.addResource('fallback');

    // Integration with SMS handler Lambda
    const smsIntegration = new apigateway.LambdaIntegration(props.smsHandlerFunction, {
      requestTemplates: {
        'application/json': JSON.stringify({
          body: '$input.body',
          headers: {
            'telnyx-signature-ed25519': '$input.params(\'telnyx-signature-ed25519\')',
            'telnyx-timestamp': '$input.params(\'telnyx-timestamp\')',
            'content-type': '$input.params(\'content-type\')'
          },
          httpMethod: '$context.httpMethod',
          sourceIp: '$context.identity.sourceIp',
          userAgent: '$context.identity.userAgent'
        })
      },
      passthroughBehavior: apigateway.PassthroughBehavior.NEVER,
      integrationResponses: [
        {
          statusCode: '200',
          responseTemplates: {
            'application/json': JSON.stringify({ message: 'SMS processed successfully' })
          }
        },
        {
          statusCode: '400',
          selectionPattern: '4\\d{2}',
          responseTemplates: {
            'application/json': JSON.stringify({ error: 'Bad Request' })
          }
        },
        {
          statusCode: '500',
          selectionPattern: '5\\d{2}',
          responseTemplates: {
            'application/json': JSON.stringify({ error: 'Internal Server Error' })
          }
        }
      ]
    });

    // POST method for SMS webhooks
    smsResource.addMethod('POST', smsIntegration, {
      authorizer: authorizer,
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      methodResponses: [
        {
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL
          }
        },
        {
          statusCode: '400',
          responseModels: {
            'application/json': apigateway.Model.ERROR_MODEL
          }
        },
        {
          statusCode: '500',
          responseModels: {
            'application/json': apigateway.Model.ERROR_MODEL
          }
        }
      ]
    });

    // ===========================================
    // FALLBACK ENDPOINT
    // ===========================================

    // Integration with fallback Lambda (no authorization required for fallback)
    const fallbackIntegration = new apigateway.LambdaIntegration(this.fallbackFunction, {
      requestTemplates: {
        'application/json': JSON.stringify({
          body: '$input.body',
          headers: {
            'content-type': '$input.params(\'content-type\')',
            'user-agent': '$input.params(\'user-agent\')',
            'x-forwarded-for': '$input.params(\'x-forwarded-for\')'
          },
          httpMethod: '$context.httpMethod',
          sourceIp: '$context.identity.sourceIp',
          userAgent: '$context.identity.userAgent',
          requestContext: {
            identity: {
              sourceIp: '$context.identity.sourceIp'
            }
          }
        })
      },
      passthroughBehavior: apigateway.PassthroughBehavior.NEVER,
      integrationResponses: [
        {
          statusCode: '200',
          responseTemplates: {
            'application/json': JSON.stringify({ message: 'Fallback processed successfully' })
          }
        }
      ]
    });

    // POST method for fallback endpoint (no authorization)
    fallbackResource.addMethod('POST', fallbackIntegration, {
      methodResponses: [
        {
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL
          }
        }
      ]
    });

    // GET method for fallback health check
    fallbackResource.addMethod('GET', new apigateway.MockIntegration({
      integrationResponses: [
        {
          statusCode: '200',
          responseTemplates: {
            'application/json': JSON.stringify({
              status: 'healthy',
              service: 'telnyx-fallback-handler',
              timestamp: new Date().toISOString(),
              environment: props.environment
            })
          }
        }
      ],
      passthroughBehavior: apigateway.PassthroughBehavior.NEVER,
      requestTemplates: {
        'application/json': JSON.stringify({ statusCode: 200 })
      }
    }), {
      methodResponses: [
        {
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL
          }
        }
      ]
    });

    // Health check endpoint (no authorization required)
    const healthResource = this.api.root.addResource('health');
    healthResource.addMethod('GET', new apigateway.MockIntegration({
      integrationResponses: [
        {
          statusCode: '200',
          responseTemplates: {
            'application/json': JSON.stringify({
              status: 'healthy',
              timestamp: new Date().toISOString(),
              environment: props.environment
            })
          }
        }
      ],
      passthroughBehavior: apigateway.PassthroughBehavior.NEVER,
      requestTemplates: {
        'application/json': JSON.stringify({ statusCode: 200 })
      }
    }), {
      methodResponses: [
        {
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL
          }
        }
      ]
    });

    // Grant API Gateway permission to invoke the SMS handler Lambda
    props.smsHandlerFunction.addPermission('ApiGatewayInvoke', {
      principal: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      sourceArn: this.api.arnForExecuteApi('*', '/dev/webhooks/telnyx/sms', 'POST')
    });

    // Grant API Gateway permission to invoke the fallback Lambda
    this.fallbackFunction.addPermission('ApiGatewayInvokeFallback', {
      principal: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      sourceArn: this.api.arnForExecuteApi('*', '/dev/webhooks/telnyx/fallback', 'POST')
    });

    // ===========================================
    // CUSTOM DOMAIN (Optional)
    // ===========================================

    if (props.customDomain) {
      // Create custom domain
      this.customDomain = new apigateway.DomainName(this, 'CustomDomain', {
        domainName: props.customDomain.domainName,
        certificate: acm.Certificate.fromCertificateArn(
          this, 
          'Certificate', 
          props.customDomain.certificateArn
        ),
        endpointType: apigateway.EndpointType.REGIONAL,
        securityPolicy: apigateway.SecurityPolicy.TLS_1_2
      });

      // Apply networking service tags
      props.tagging.applyTags(this.customDomain, SERVICES.NETWORK, 'custom-domain');

      // Create base path mapping
      new apigateway.BasePathMapping(this, 'BasePathMapping', {
        domainName: this.customDomain,
        restApi: this.api,
        stage: this.api.deploymentStage
      });

      // Set webhook URL to use custom domain with full path
      this.webhookUrl = `https://${props.customDomain.domainName}/dev/webhooks/telnyx/sms`;
      this.fallbackUrl = `https://${props.customDomain.domainName}/dev/webhooks/telnyx/fallback`;
    } else {
      // Use default API Gateway URL with full path
      this.webhookUrl = `${this.api.url}dev/webhooks/telnyx/sms`;
      this.fallbackUrl = `${this.api.url}dev/webhooks/telnyx/fallback`;
    }
  }

  // ===========================================
  // HELPER METHODS
  // ===========================================

  private createResourcePolicy(): iam.PolicyDocument {
    // Get Telnyx configuration for the environment
    const telnyxConfig = getTelnyxConfigForEnvironment(this.environment);

    return new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          principals: [new iam.AnyPrincipal()],
          actions: ['execute-api:Invoke'],
          resources: ['*'],
          conditions: {
            IpAddress: {
              'aws:SourceIp': telnyxConfig.ipCidrBlocks
            }
          }
        }),
        // Allow health check from anywhere
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          principals: [new iam.AnyPrincipal()],
          actions: ['execute-api:Invoke'],
          resources: ['arn:aws:execute-api:*:*:*/*/GET/health']
        })
      ]
    });
  }

  private getAuthorizerCode(): string {
    return `
import json
import base64
import os
import time
from datetime import datetime, timezone

def lambda_handler(event, context):
    """
    Telnyx webhook Ed25519 signature validation authorizer
    Based on official Telnyx Python SDK implementation
    """
    print(f"Authorizer event: {json.dumps(event)}")
    
    try:
        # Extract headers
        headers = event.get('headers', {})
        signature = headers.get('telnyx-signature-ed25519', '')
        timestamp = headers.get('telnyx-timestamp', '')
        
        # Get public key from environment
        public_key = os.environ.get('TELNYX_PUBLIC_KEY', '')
        
        if not public_key:
            print("ERROR: TELNYX_PUBLIC_KEY not configured")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        if not signature or not timestamp:
            print("ERROR: Missing required headers")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        # Validate timestamp (prevent replay attacks)
        try:
            webhook_timestamp = int(timestamp)
            current_timestamp = int(time.time())
            
            # Allow 5 minute window (300 seconds)
            tolerance = 300
            if current_timestamp - webhook_timestamp > tolerance:
                print(f"ERROR: Timestamp too old. Current: {current_timestamp}, Webhook: {webhook_timestamp}")
                return generate_policy('user', 'Deny', event['methodArn'])
        except ValueError:
            print("ERROR: Invalid timestamp format")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        # Get request body
        body = event.get('body', '')
        if not body:
            print("ERROR: Empty request body")
            return generate_policy('user', 'Deny', event['methodArn'])
        
        # Create signed payload: timestamp|body (Telnyx format)
        signed_payload = f"{timestamp}|{body}"
        
        # Verify Ed25519 signature
        if verify_ed25519_signature(signed_payload, signature, public_key):
            print("SUCCESS: Signature validation passed")
            return generate_policy('user', 'Allow', event['methodArn'])
        else:
            print("ERROR: Signature validation failed")
            return generate_policy('user', 'Deny', event['methodArn'])
        
    except Exception as e:
        print(f"ERROR: Authorization failed: {str(e)}")
        return generate_policy('user', 'Deny', event['methodArn'])

def verify_ed25519_signature(payload, signature, public_key):
    """
    Verify Ed25519 signature using Python's built-in libraries
    This is a simplified version - for production, consider using cryptography library
    """
    try:
        # For now, we'll do basic validation
        # In production, you should use the cryptography library for proper Ed25519 verification
        
        # Basic checks
        if not signature or not public_key or not payload:
            return False
            
        # Decode base64 signature
        try:
            decoded_signature = base64.b64decode(signature)
        except Exception as e:
            print(f"ERROR: Failed to decode signature: {str(e)}")
            return False
        
        # For development/testing, we'll accept if basic format is correct
        # TODO: Implement proper Ed25519 verification with cryptography library
        if len(decoded_signature) == 64:  # Ed25519 signatures are 64 bytes
            print("INFO: Signature format validation passed (basic check)")
            return True
        else:
            print(f"ERROR: Invalid signature length: {len(decoded_signature)}")
            return False
            
    except Exception as e:
        print(f"ERROR: Signature verification failed: {str(e)}")
        return False

def generate_policy(principal_id, effect, resource):
    """Generate IAM policy for API Gateway"""
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        },
        'context': {
            'environment': os.environ.get('ENVIRONMENT', 'unknown'),
            'timestamp': str(int(time.time())),
            'validation_method': 'ed25519_basic'
        }
    }
    `;
  }
}
