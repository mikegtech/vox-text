import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';

import { NamingConvention } from './naming-convention';
import { TaggingStrategy, SERVICES } from './tagging-strategy';
import { EnvironmentConfig, getRemovalPolicy } from '../config/environments';
import { ApiGatewayConstruct } from './api-gateway-construct';

export interface InfrastructureStackProps extends cdk.StackProps {
  environment: string;
  config: EnvironmentConfig;
  company?: string;
  tenant?: string;
}

export class InfrastructureStack extends cdk.Stack {
  private readonly naming: NamingConvention;
  private readonly tagging: TaggingStrategy;
  private readonly config: EnvironmentConfig;

  constructor(scope: Construct, id: string, props: InfrastructureStackProps) {
    super(scope, id, props);

    this.config = props.config;
    
    // Initialize naming convention
    this.naming = new NamingConvention({
      project: 'smsbot',
      environment: props.environment,
      region: this.region,
      accountId: this.account
    });

    // Initialize tagging strategy
    this.tagging = new TaggingStrategy(
      props.environment,
      this.config,
      props.company || 'your-company',
      props.tenant
    );

    // Apply stack-level tags
    this.tagging.applyStackTags(this);

    // Create infrastructure resources
    this.createInfrastructure();
  }

  private createInfrastructure(): void {
    // ===========================================
    // IAM ROLES (Phase 1 - Foundation)
    // ===========================================

    // SNS SMS Logging Role
    const snsLogsRole = new iam.Role(this, 'SnsLogsRole', {
      roleName: this.naming.iamRole(SERVICES.MESSAGING, 'sns-logs'),
      assumedBy: new iam.ServicePrincipal('sns.amazonaws.com'),
      inlinePolicies: {
        [this.naming.iamPolicy(SERVICES.MESSAGING, 'sns-logs')]: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents'
              ],
              resources: ['arn:aws:logs:*:*:*']
            })
          ]
        })
      }
    });

    // Apply security service tags to IAM role
    this.tagging.applyTags(snsLogsRole, SERVICES.SECURITY, 'sns-logs-role');

    // Lambda Execution Role
    const lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
      roleName: this.naming.iamRole(SERVICES.COMPUTE, 'lambda-execution'),
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ]
    });

    // Apply security service tags to Lambda role
    this.tagging.applyTags(lambdaExecutionRole, SERVICES.SECURITY, 'lambda-execution-role');

    // ===========================================
    // CLOUDWATCH LOG GROUPS (Phase 2 - Early Setup)
    // ===========================================

    const smsDeliveryLogGroup = new logs.LogGroup(this, 'SmsDeliveryLogGroup', {
      logGroupName: this.naming.logGroup('sns', 'delivery-logs'),
      retention: this.getLogRetention(),
      removalPolicy: this.getRemovalPolicy()
    });

    // Apply monitoring service tags
    this.tagging.applyTags(smsDeliveryLogGroup, SERVICES.MONITORING, 'sms-delivery-logs');

    // ===========================================
    // DYNAMODB TABLES (Phase 3 - Data Layer)
    // ===========================================

    // Main conversation tracking table
    const conversationsTable = new dynamodb.Table(this, 'BotConversationsTable', {
      tableName: this.naming.dynamoTable('conversations'),
      partitionKey: {
        name: 'phone_number',
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: this.getRemovalPolicy(),
      pointInTimeRecovery: this.config.dynamoConfig.pointInTimeRecovery,
      deletionProtection: this.config.dynamoConfig.deletionProtection
    });

    // Apply storage service tags
    this.tagging.applyTags(conversationsTable, SERVICES.STORAGE, 'conversations-table', {
      DataType: 'user-conversations',
      AccessPattern: 'read-heavy'
    });

    // Analytics table for future use
    const analyticsTable = new dynamodb.Table(this, 'BotAnalyticsTable', {
      tableName: this.naming.dynamoTable('analytics'),
      partitionKey: {
        name: 'date',
        type: dynamodb.AttributeType.STRING
      },
      sortKey: {
        name: 'metric_type',
        type: dynamodb.AttributeType.STRING
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: this.getRemovalPolicy(),
      pointInTimeRecovery: this.config.dynamoConfig.pointInTimeRecovery,
      deletionProtection: this.config.dynamoConfig.deletionProtection
    });

    // Apply storage service tags
    this.tagging.applyTags(analyticsTable, SERVICES.STORAGE, 'analytics-table', {
      DataType: 'analytics-metrics',
      AccessPattern: 'write-heavy'
    });

    // ===========================================
    // SNS TOPICS AND CONFIGURATION (Phase 4)
    // ===========================================

    // Inbound SMS topic
    const inboundSmsTopic = new sns.Topic(this, 'InboundSmsTopic', {
      topicName: this.naming.snsTopic('inbound-sms'),
      displayName: 'SMS Bot Inbound Messages'
    });

    // Apply messaging service tags
    this.tagging.applyTags(inboundSmsTopic, SERVICES.MESSAGING, 'inbound-sms-topic', {
      MessageType: 'transactional',
      DeliveryMethod: 'sms'
    });

    // Delivery status topic
    const deliveryStatusTopic = new sns.Topic(this, 'DeliveryStatusTopic', {
      topicName: this.naming.snsTopic('delivery-status'),
      displayName: 'SMS Delivery Status'
    });

    // Apply messaging service tags
    this.tagging.applyTags(deliveryStatusTopic, SERVICES.MESSAGING, 'delivery-status-topic');

    // ===========================================
    // LAMBDA FUNCTIONS (Phase 5)
    // ===========================================

    // Main SMS processing Lambda with signature validation
    const smsHandlerFunction = new lambda.Function(this, 'BotSmsHandler', {
      functionName: this.naming.lambdaFunction(SERVICES.MESSAGING, 'sms-handler'),
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.lambda_handler',
      code: this.getSmsHandlerCode(),
      role: lambdaExecutionRole,
      timeout: cdk.Duration.seconds(this.config.lambdaConfig.timeout),
      memorySize: this.config.lambdaConfig.memorySize,
      reservedConcurrentExecutions: this.config.lambdaConfig.reservedConcurrency,
      environment: {
        'CONVERSATIONS_TABLE': conversationsTable.tableName,
        'ANALYTICS_TABLE': analyticsTable.tableName,
        'TELNYX_PUBLIC_KEY_SECRET': `smsbot/${this.config.environment}/telnyx-public-key`,
        'ENVIRONMENT': this.config.environment
      },
      // Let Lambda create its own log group to avoid conflicts
      logRetention: this.getLogRetention()
    });

    // Apply compute service tags
    this.tagging.applyTags(smsHandlerFunction, SERVICES.COMPUTE, 'sms-handler', {
      Runtime: 'python3.9',
      MemorySize: `${this.config.lambdaConfig.memorySize}MB`,
      Timeout: `${this.config.lambdaConfig.timeout}s`
    });

    // Grant Lambda permissions to access DynamoDB
    conversationsTable.grantReadWriteData(lambdaExecutionRole);
    analyticsTable.grantReadWriteData(lambdaExecutionRole);

    // Grant Lambda permissions to publish to SNS
    lambdaExecutionRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['sns:Publish'],
      resources: ['*'] // For SMS publishing
    }));

    // Grant Lambda permissions to access Secrets Manager for Telnyx public key
    lambdaExecutionRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'secretsmanager:GetSecretValue',
        'secretsmanager:DescribeSecret'
      ],
      resources: [
        `arn:aws:secretsmanager:${this.region}:${this.account}:secret:smsbot/${this.config.environment}/telnyx-public-key*`
      ]
    }));

    // Subscribe Lambda to inbound SMS topic
    inboundSmsTopic.addSubscription(new subscriptions.LambdaSubscription(smsHandlerFunction));

    // ===========================================
    // API GATEWAY FOR TELNYX WEBHOOKS (Phase 6)
    // ===========================================

    const apiGateway = new ApiGatewayConstruct(this, 'TelnyxWebhookApi', {
      naming: this.naming,
      tagging: this.tagging,
      smsHandlerFunction: smsHandlerFunction,
      environment: this.config.environment,
      customDomain: this.getCustomDomainConfig(),
      conversationsTable: conversationsTable.tableName,
      analyticsTable: analyticsTable.tableName
    });

    // ===========================================
    // CLOUDWATCH DASHBOARD (Phase 7 - Monitoring)
    // ===========================================

    const dashboard = new cloudwatch.Dashboard(this, 'SmsBotDashboard', {
      dashboardName: this.naming.dashboard('operations')
    });

    // Apply monitoring service tags
    this.tagging.applyTags(dashboard, SERVICES.MONITORING, 'operations-dashboard');

    // Add widgets to dashboard
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'SMS Bot Metrics',
        left: [
          new cloudwatch.Metric({
            namespace: 'AWS/SNS',
            metricName: 'NumberOfMessagesPublished',
            statistic: 'Sum'
          }),
          new cloudwatch.Metric({
            namespace: 'AWS/Lambda',
            metricName: 'Invocations',
            dimensionsMap: {
              FunctionName: smsHandlerFunction.functionName
            },
            statistic: 'Sum'
          })
        ],
        right: [
          new cloudwatch.Metric({
            namespace: 'AWS/Lambda',
            metricName: 'Errors',
            dimensionsMap: {
              FunctionName: smsHandlerFunction.functionName
            },
            statistic: 'Sum'
          }),
          new cloudwatch.Metric({
            namespace: 'AWS/Lambda',
            metricName: 'Duration',
            dimensionsMap: {
              FunctionName: smsHandlerFunction.functionName
            },
            statistic: 'Average'
          })
        ]
      })
    );

    // ===========================================
    // OUTPUTS
    // ===========================================

    new cdk.CfnOutput(this, 'InboundSmsTopicArn', {
      value: inboundSmsTopic.topicArn,
      description: 'ARN of the inbound SMS topic'
    });

    new cdk.CfnOutput(this, 'LambdaFunctionArn', {
      value: smsHandlerFunction.functionArn,
      description: 'ARN of the SMS handler Lambda function'
    });

    new cdk.CfnOutput(this, 'ConversationsTableName', {
      value: conversationsTable.tableName,
      description: 'Name of the conversations DynamoDB table'
    });

    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: `https://console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${dashboard.dashboardName}`,
      description: 'URL to the CloudWatch dashboard'
    });

    new cdk.CfnOutput(this, 'ApiGatewayUrl', {
      value: apiGateway.api.url,
      description: 'API Gateway URL for Telnyx webhooks'
    });

    new cdk.CfnOutput(this, 'WebhookEndpoint', {
      value: apiGateway.webhookUrl,
      description: 'Telnyx SMS webhook endpoint URL (custom domain or API Gateway)'
    });

    new cdk.CfnOutput(this, 'FallbackEndpoint', {
      value: apiGateway.fallbackUrl,
      description: 'Telnyx fallback/dead letter queue webhook endpoint URL'
    });

    new cdk.CfnOutput(this, 'HealthCheckEndpoint', {
      value: apiGateway.customDomain 
        ? `https://${apiGateway.customDomain.domainName}/health`
        : `${apiGateway.api.url}health`,
      description: 'API health check endpoint'
    });

    new cdk.CfnOutput(this, 'FallbackHealthEndpoint', {
      value: apiGateway.customDomain 
        ? `https://${apiGateway.customDomain.domainName}/dev/webhooks/telnyx/fallback`
        : `${apiGateway.api.url}dev/webhooks/telnyx/fallback`,
      description: 'Fallback endpoint health check (GET)'
    });

    if (apiGateway.customDomain) {
      new cdk.CfnOutput(this, 'CustomDomainName', {
        value: apiGateway.customDomain.domainName,
        description: 'Custom domain name for API Gateway'
      });

      new cdk.CfnOutput(this, 'DomainNameTarget', {
        value: apiGateway.customDomain.domainNameAliasDomainName,
        description: 'Target domain name for DNS CNAME record'
      });
    }

    new cdk.CfnOutput(this, 'AuthorizerFunctionArn', {
      value: apiGateway.authorizerFunction.functionArn,
      description: 'ARN of the Telnyx authorizer Lambda function'
    });

    // Output naming examples for verification
    new cdk.CfnOutput(this, 'NamingExamples', {
      value: JSON.stringify({
        lambdaFunction: smsHandlerFunction.functionName,
        conversationsTable: conversationsTable.tableName,
        inboundTopic: inboundSmsTopic.topicName,
        dashboard: dashboard.dashboardName
      }),
      description: 'Examples of generated resource names'
    });
  }

  // ===========================================
  // HELPER METHODS
  // ===========================================

  private getLogRetention(): logs.RetentionDays {
    const retentionMap: { [key: number]: logs.RetentionDays } = {
      1: logs.RetentionDays.ONE_DAY,
      3: logs.RetentionDays.THREE_DAYS,
      5: logs.RetentionDays.FIVE_DAYS,
      7: logs.RetentionDays.ONE_WEEK,
      14: logs.RetentionDays.TWO_WEEKS,
      30: logs.RetentionDays.ONE_MONTH,
      60: logs.RetentionDays.TWO_MONTHS,
      90: logs.RetentionDays.THREE_MONTHS,
      120: logs.RetentionDays.FOUR_MONTHS,
      150: logs.RetentionDays.FIVE_MONTHS,
      180: logs.RetentionDays.SIX_MONTHS,
      365: logs.RetentionDays.ONE_YEAR
    };

    return retentionMap[this.config.monitoringConfig.logRetentionDays] || logs.RetentionDays.ONE_MONTH;
  }

  private getRemovalPolicy(): cdk.RemovalPolicy {
    if (this.config.environment === 'prod') {
      return cdk.RemovalPolicy.RETAIN; // Protect production resources
    }
    return cdk.RemovalPolicy.DESTROY; // Allow cleanup for dev/staging
  }

  private getCustomDomainConfig() {
    // Get custom domain configuration from CDK context
    const customDomainName = this.node.tryGetContext('customDomainName');
    const certificateArn = this.node.tryGetContext('certificateArn');
    
    if (customDomainName && certificateArn) {
      return {
        domainName: customDomainName,
        certificateArn: certificateArn
      };
    }
    
    return undefined;
  }

  private getLambdaCode(): string {
    return `
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    SMS bot handler function
    Processes inbound SMS from both SNS and API Gateway (Telnyx)
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Initialize AWS clients
    sns = boto3.client('sns')
    dynamodb = boto3.resource('dynamodb')
    conversations_table = dynamodb.Table(os.environ['CONVERSATIONS_TABLE'])
    analytics_table = dynamodb.Table(os.environ['ANALYTICS_TABLE'])
    
    try:
        # Determine event source
        if 'Records' in event:
            # SNS event
            return handle_sns_event(event, sns, conversations_table, analytics_table)
        elif 'httpMethod' in event:
            # API Gateway event (Telnyx webhook)
            return handle_api_gateway_event(event, sns, conversations_table, analytics_table)
        else:
            print("Unknown event source")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown event source'})
            }
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        
        # Store error analytics
        try:
            analytics_table.put_item(
                Item={
                    'date': datetime.utcnow().isoformat()[:10],
                    'metric_type': 'error',
                    'timestamp': datetime.utcnow().isoformat(),
                    'error_message': str(e),
                    'event_source': 'sns' if 'Records' in event else 'api_gateway'
                }
            )
        except:
            pass  # Don't fail if analytics storage fails
            
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_sns_event(event, sns, conversations_table, analytics_table):
    """Handle SNS events (original functionality)"""
    for record in event['Records']:
        if record['EventSource'] == 'aws:sns':
            message = json.loads(record['Sns']['Message'])
            
            # Extract phone number and message content
            phone_number = message.get('originationNumber', 'unknown')
            message_body = message.get('messageBody', '')
            
            process_sms_message(phone_number, message_body, sns, conversations_table, analytics_table, 'sns')
    
    return {
        'statusCode': 200,
        'body': json.dumps('SNS message processed successfully')
    }

def handle_api_gateway_event(event, sns, conversations_table, analytics_table):
    """Handle API Gateway events (Telnyx webhooks)"""
    try:
        # Parse Telnyx webhook payload
        body = json.loads(event.get('body', '{}'))
        
        # Extract Telnyx event data
        event_type = body.get('data', {}).get('event_type', '')
        
        if event_type == 'message.received':
            # Inbound SMS from Telnyx
            payload = body.get('data', {}).get('payload', {})
            
            phone_number = payload.get('from', {}).get('phone_number', 'unknown')
            message_body = payload.get('text', '')
            
            process_sms_message(phone_number, message_body, sns, conversations_table, analytics_table, 'telnyx')
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'Telnyx webhook processed successfully'})
            }
        else:
            print(f"Unhandled Telnyx event type: {event_type}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'Event acknowledged but not processed'})
            }
            
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Invalid JSON payload'})
        }

def process_sms_message(phone_number, message_body, sns, conversations_table, analytics_table, source):
    """Process SMS message from any source"""
    timestamp = datetime.utcnow().isoformat()
    
    # Store conversation in DynamoDB
    conversations_table.put_item(
        Item={
            'phone_number': phone_number,
            'created_at': timestamp,
            'updated_at': timestamp,
            'last_message': message_body,
            'conversation_state': 'active',
            'message_count': 1,
            'environment': os.environ.get('ENVIRONMENT', 'unknown'),
            'source': source
        }
    )
    
    # Store analytics
    analytics_table.put_item(
        Item={
            'date': timestamp[:10],  # YYYY-MM-DD
            'metric_type': 'inbound_message',
            'timestamp': timestamp,
            'phone_number': phone_number,
            'message_length': len(message_body),
            'source': source
        }
    )
    
    # Generate bot response (placeholder logic)
    bot_response = f"Hello! I received your message: {message_body[:50]}..."
    
    # Send SMS response via SNS (works for both sources)
    sns.publish(
        PhoneNumber=phone_number,
        Message=bot_response,
        MessageAttributes={
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            }
        }
    )
    
    print(f"Processed message from {phone_number} via {source}")
    `;
  }

  /**
   * Get SMS handler code from packaged deployment or fallback to inline
   */
  private getSmsHandlerCode(): lambda.Code {
    const packagePath = `lambda-packages/sms-handler-deployment.zip`;
    const assetPath = `lambda/sms-handler`;
    
    // Check if packaged deployment exists
    const fs = require('fs');
    if (fs.existsSync(packagePath)) {
      console.log(`Using packaged SMS handler deployment: ${packagePath}`);
      return lambda.Code.fromAsset(packagePath);
    } else if (fs.existsSync(assetPath)) {
      console.log(`Using SMS handler source code: ${assetPath}`);
      console.log(`Warning: Dependencies may not be available. Run: ./scripts/package-lambda.sh sms-handler`);
      return lambda.Code.fromAsset(assetPath);
    } else {
      console.log(`Using inline SMS handler code (fallback)`);
      return lambda.Code.fromInline(this.getLambdaCode());
    }
  }
}
