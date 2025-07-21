# AWS Account Preparation PRD - SMS Bot Infrastructure

## Overview

This document outlines the complete AWS account preparation required for deploying a cost-optimized SMS bot infrastructure. The setup enables receiving and sending SMS messages at $0.00645 per message, with serverless processing via Lambda, conversation state management in DynamoDB, and comprehensive monitoring through CloudWatch.

This foundation supports high-volume bot SMS operations while maintaining security, scalability, and cost efficiency. All configurations follow AWS best practices and prepare the account for both immediate MVP deployment and future scaling.

## Core Features

### 1. SMS Infrastructure (Amazon SNS)
- **SMS Sending Capability**: Configured for transactional messages with optimal delivery
- **Monthly Spend Controls**: Protective limits to prevent unexpected charges
- **Delivery Tracking**: Full success/failure logging to CloudWatch
- **Two-Way SMS**: Inbound message routing to Lambda processors
- **Message Attributes**: Support for sender IDs and message types

### 2. Serverless Compute (AWS Lambda)
- **Message Processing Functions**: Handle inbound SMS and generate responses
- **Event-Driven Architecture**: Automatic triggering from SNS events
- **Stateless Processing**: Scalable design for high-volume operations
- **Error Handling**: Dead letter queues and retry logic
- **Monitoring Integration**: Detailed metrics and logs

### 3. Data Persistence (Amazon DynamoDB)
- **Conversation Tracking**: Store message history and context
- **User State Management**: Maintain bot conversation flow
- **Scalable Storage**: On-demand pricing for cost efficiency
- **Quick Lookups**: Phone number-based primary key
- **Audit Trail**: Complete message history retention

### 4. Security & Access (IAM)
- **Least Privilege Access**: Minimal permissions for each service
- **Service Roles**: Dedicated roles for SNS, Lambda, and logging
- **Secure Secrets**: Credentials management for future integrations
- **Cross-Service Permissions**: Proper trust relationships

### 5. Monitoring & Observability (CloudWatch)
- **SMS Delivery Logs**: Track every message sent/received
- **Lambda Metrics**: Performance and error monitoring
- **Cost Tracking**: Detailed billing breakdowns
- **Custom Dashboards**: Real-time operational views
- **Alerting**: Proactive issue detection

## User Experience

### User Personas

**DevOps Engineer**:
- Responsible for initial AWS setup
- Needs clear documentation and scripts
- Values automation and repeatability

**Bot Developer**:
- Writes Lambda functions for bot logic
- Needs proper permissions and tools
- Requires testing capabilities

**Operations Manager**:
- Monitors costs and performance
- Needs dashboards and alerts
- Reviews security compliance

### Key User Flows

**Initial Setup Flow**:
1. Run preparation scripts
2. Verify service activations
3. Test basic SMS functionality
4. Confirm logging works

**Development Flow**:
1. Write Lambda function
2. Deploy with proper permissions
3. Test with SNS integration
4. Monitor in CloudWatch

**Monitoring Flow**:
1. Check CloudWatch dashboard
2. Review SMS delivery rates
3. Analyze cost trends
4. Respond to alerts

## Technical Architecture

### System Components

**AWS Services Required**:
```
Amazon SNS
├── SMS Channel
├── Topics
└── Subscriptions

AWS Lambda
├── Function Execution
├── Event Sources
└── Layers (optional)

Amazon DynamoDB
├── Tables
├── Indexes
└── Streams (future)

AWS IAM
├── Roles
├── Policies
└── Trust Relationships

Amazon CloudWatch
├── Log Groups
├── Metrics
├── Dashboards
└── Alarms
```

### Data Models

**IAM Role Structure**:
```json
{
  "sns-sms-logs-role": {
    "TrustPolicy": "sns.amazonaws.com",
    "Permissions": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
  },
  "lambda-sns-execution-role": {
    "TrustPolicy": "lambda.amazonaws.com",
    "Permissions": ["sns:Publish", "dynamodb:*", "logs:*"]
  }
}
```

**DynamoDB Schema**:
```json
{
  "TableName": "BotConversations",
  "PrimaryKey": {
    "PartitionKey": "phone_number (String)"
  },
  "Attributes": {
    "phone_number": "String",
    "created_at": "String (ISO 8601)",
    "updated_at": "String (ISO 8601)",
    "message_count": "Number",
    "conversation_state": "String",
    "last_message": "String",
    "last_response": "String",
    "user_context": "Map"
  }
}
```

### APIs and Integrations

**Internal AWS Integrations**:
- SNS → Lambda (Event trigger)
- Lambda → DynamoDB (State storage)
- Lambda → SNS (Send SMS)
- All services → CloudWatch (Logging)

**External Preparations**:
- Webhook endpoints (API Gateway)
- Third-party API credentials (Secrets Manager)
- IP whitelisting (Security Groups)

### Infrastructure Requirements

**Service Limits to Check/Increase**:
- SNS SMS: 100 TPS default
- Lambda concurrent executions: 1000 default
- DynamoDB: On-demand (no limits)
- CloudWatch Logs: 5GB free tier

**Cost Estimates**:
- SNS: $0.00645 per SMS
- Lambda: Free tier (1M requests)
- DynamoDB: ~$0.25/GB/month
- CloudWatch: ~$0.50/GB/month logs

## Development Roadmap

### Phase 1: IAM Foundation (2 hours)

**Create Service Roles**:
```bash
# SNS SMS Logging Role
aws iam create-role --role-name sns-sms-logs \
  --assume-role-policy-document file://sns-trust-policy.json

# Lambda Execution Role  
aws iam create-role --role-name lambda-sns-execution \
  --assume-role-policy-document file://lambda-trust-policy.json
```

**Attach Policies**:
```bash
# SNS Logs Policy
aws iam put-role-policy --role-name sns-sms-logs \
  --policy-name sns-logs-policy \
  --policy-document file://sns-logs-policy.json

# Lambda Full Policy
aws iam attach-role-policy --role-name lambda-sns-execution \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

**Deliverables**:
- All IAM roles created
- Policies attached
- Trust relationships verified
- Documentation updated

### Phase 2: SNS Configuration (1 hour)

**Enable SMS Service**:
```bash
aws sns set-sms-attributes \
  --attributes '{
    "DefaultSMSType": "Transactional",
    "MonthlySpendLimit": "100",
    "DeliveryStatusIAMRole": "arn:aws:iam::ACCOUNT:role/sns-sms-logs",
    "DeliveryStatusSuccessSamplingRate": "100",
    "DefaultSenderID": "AIBOT"
  }'
```

**Create Topics**:
```bash
# Inbound SMS topic
aws sns create-topic --name bot-sms-inbound

# Delivery status topic
aws sns create-topic --name sms-delivery-status
```

**Deliverables**:
- SMS enabled in region
- Spend limits configured
- Topics created
- Delivery logging active

### Phase 3: DynamoDB Setup (30 minutes)

**Create Tables**:
```bash
# Main conversation table
aws dynamodb create-table \
  --table-name BotConversations \
  --attribute-definitions \
    AttributeName=phone_number,AttributeType=S \
  --key-schema \
    AttributeName=phone_number,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Project,Value=SMSBot Key=Environment,Value=Production

# Future: Analytics table
aws dynamodb create-table \
  --table-name BotAnalytics \
  --attribute-definitions \
    AttributeName=date,AttributeType=S \
    AttributeName=metric_type,AttributeType=S \
  --key-schema \
    AttributeName=date,KeyType=HASH \
    AttributeName=metric_type,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

**Deliverables**:
- Tables created
- Indexes configured
- Backup settings enabled
- Access permissions set

### Phase 4: Lambda Preparation (1 hour)

**Create Function Placeholder**:
```bash
# Create deployment package
echo 'def lambda_handler(event, context): return {"statusCode": 200}' > index.py
zip function.zip index.py

# Create function
aws lambda create-function \
  --function-name BotSMSHandler \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT:role/lambda-sns-execution \
  --handler index.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables={ENV=production}
```

**Configure Triggers**:
```bash
# Add SNS trigger
aws sns subscribe \
  --topic-arn arn:aws:sns:region:account:bot-sms-inbound \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:region:account:function:BotSMSHandler

# Add permissions
aws lambda add-permission \
  --function-name BotSMSHandler \
  --statement-id sns-invoke \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:region:account:bot-sms-inbound
```

**Deliverables**:
- Lambda function created
- SNS trigger configured
- Permissions established
- Environment variables set

### Phase 5: Monitoring Setup (1 hour)

**Create Log Groups**:
```bash
# SMS delivery logs
aws logs create-log-group --log-group-name /aws/sns/sms-delivery

# Lambda logs (auto-created)
aws logs put-retention-policy \
  --log-group-name /aws/lambda/BotSMSHandler \
  --retention-in-days 30
```

**Create CloudWatch Dashboard**:
```json
{
  "DashboardName": "SMS-Bot-Operations",
  "DashboardBody": {
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/SNS", "NumberOfMessagesPublished"],
            ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
            ["AWS/Lambda", "Errors", {"stat": "Sum"}],
            ["AWS/Lambda", "Duration", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "SMS Bot Metrics"
        }
      }
    ]
  }
}
```

**Deliverables**:
- Log groups created
- Retention policies set
- Dashboard configured
- Basic alarms created

## Logical Dependency Chain

1. **IAM Roles** (Must be first)
   - Required by all other services
   - Trust relationships needed before service activation

2. **CloudWatch Log Groups** (Early setup)
   - Needed for SNS delivery logs
   - Must exist before enabling SMS logging

3. **SNS Configuration** (Depends on IAM)
   - Requires logging role
   - Must be active before Lambda triggers

4. **DynamoDB Tables** (Independent)
   - Can be created in parallel
   - Needed before Lambda testing

5. **Lambda Functions** (Depends on IAM, SNS)
   - Requires execution role
   - Needs SNS topics for triggers

6. **Monitoring** (Final step)
   - Requires all services active
   - Dashboards need metrics flowing

## Risks and Mitigations

### Technical Challenges

**Risk**: SMS spending spike
- **Impact**: Unexpected AWS bill
- **Mitigation**: Set MonthlySpendLimit, add billing alerts

**Risk**: Lambda cold starts
- **Impact**: Slow bot responses
- **Mitigation**: Set appropriate memory, consider provisioned concurrency

**Risk**: DynamoDB throttling
- **Impact**: Failed state updates
- **Mitigation**: Use on-demand billing, implement exponential backoff

### Security Considerations

**Access Control**:
- Never use admin credentials
- Create dedicated CI/CD user
- Enable MFA on console access
- Rotate access keys regularly

**Data Protection**:
- Encrypt DynamoDB at rest
- Use SSL for all API calls
- Mask phone numbers in logs
- Implement data retention policies

### Resource Constraints

**AWS Service Limits**:
- Check SNS SMS limits for region
- Request increases before launch
- Monitor Lambda concurrent executions
- Watch CloudWatch log storage

**Budget Controls**:
- Set up AWS Budgets alerts
- Use cost allocation tags
- Monitor daily spending
- Implement circuit breakers

## Appendix

### Required Files

**sns-trust-policy.json**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "sns.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
```

**lambda-trust-policy.json**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "lambda.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
```

**sns-logs-policy.json**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ],
    "Resource": "arn:aws:logs:*:*:*"
  }]
}
```

### Validation Checklist

**Post-Setup Verification**:
- [ ] IAM roles appear in console
- [ ] SNS SMS attributes saved
- [ ] DynamoDB tables active
- [ ] Lambda function deployed
- [ ] CloudWatch logs flowing
- [ ] Dashboard showing metrics
- [ ] Test SMS sends successfully
- [ ] Costs tracking properly

### Cost Optimization Tips

1. **Use Transactional SMS type** (better delivery, same price)
2. **Set reasonable spend limits** ($100/month initially)
3. **Enable detailed billing** for per-number tracking
4. **Use on-demand DynamoDB** (no idle costs)
5. **Set log retention** to 30 days (reduce storage costs)