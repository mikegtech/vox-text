# AWS Resource Naming Convention - SMS Bot Project

## Overview

This document defines the standardized naming convention for all AWS resources in the SMS Bot infrastructure project. Consistent naming improves resource management, cost tracking, security, and operational efficiency.

## General Naming Pattern

```
{project}-{environment}-{service}-{resource-type}-{identifier}
```

### Components:
- **project**: `smsbot` (lowercase, no spaces)
- **environment**: `dev`, `staging`, `prod`
- **service**: Functional area (e.g., `messaging`, `storage`, `compute`)
- **resource-type**: AWS service abbreviation
- **identifier**: Specific resource identifier (optional)

## Resource-Specific Naming Standards

### IAM Resources

**Roles:**
```
smsbot-{env}-{service}-role-{purpose}
```
Examples:
- `smsbot-prod-messaging-role-sns-logs`
- `smsbot-prod-compute-role-lambda-execution`

**Policies:**
```
smsbot-{env}-{service}-policy-{purpose}
```
Examples:
- `smsbot-prod-messaging-policy-sns-publish`
- `smsbot-prod-storage-policy-dynamodb-access`

### Lambda Functions

**Function Names:**
```
smsbot-{env}-{service}-{function-purpose}
```
Examples:
- `smsbot-prod-messaging-sms-handler`
- `smsbot-prod-analytics-data-processor`

### DynamoDB Tables

**Table Names:**
```
smsbot-{env}-{data-type}
```
Examples:
- `smsbot-prod-conversations`
- `smsbot-prod-analytics`
- `smsbot-dev-user-sessions`

### SNS Topics

**Topic Names:**
```
smsbot-{env}-{message-type}
```
Examples:
- `smsbot-prod-inbound-sms`
- `smsbot-prod-delivery-status`
- `smsbot-dev-test-messages`

### CloudWatch Resources

**Log Groups:**
```
/aws/{service}/smsbot-{env}-{component}
```
Examples:
- `/aws/lambda/smsbot-prod-sms-handler`
- `/aws/sns/smsbot-prod-delivery-logs`

**Dashboards:**
```
smsbot-{env}-{dashboard-purpose}
```
Examples:
- `smsbot-prod-operations`
- `smsbot-dev-debugging`

### S3 Buckets (if needed)

**Bucket Names:**
```
smsbot-{env}-{purpose}-{account-id}-{region}
```
Examples:
- `smsbot-prod-artifacts-123456789012-us-east-1`
- `smsbot-dev-logs-123456789012-us-west-2`

## Environment Abbreviations

- **Development**: `dev`
- **Staging**: `staging`
- **Production**: `prod`

## Service Categories

- **messaging**: SNS, SQS, SMS-related resources
- **compute**: Lambda functions, compute resources
- **storage**: DynamoDB, S3, data storage
- **monitoring**: CloudWatch, logging, metrics
- **security**: IAM, secrets, security resources
- **network**: VPC, subnets, networking (if used)

## Tagging Strategy

All resources should include these mandatory tags:

```json
{
  "Project": "SMSBot",
  "Environment": "prod|staging|dev",
  "Service": "messaging|compute|storage|monitoring|security",
  "Owner": "team-name",
  "CostCenter": "engineering",
  "CreatedBy": "cdk",
  "ManagedBy": "infrastructure-team"
}
```

## Examples by Resource Type

### Complete Resource Naming Examples

```yaml
# IAM Roles
smsbot-prod-messaging-role-sns-logs
smsbot-prod-compute-role-lambda-execution
smsbot-dev-security-role-secrets-access

# Lambda Functions
smsbot-prod-messaging-sms-handler
smsbot-prod-compute-message-processor
smsbot-dev-messaging-test-handler

# DynamoDB Tables
smsbot-prod-conversations
smsbot-prod-analytics
smsbot-staging-user-sessions

# SNS Topics
smsbot-prod-inbound-sms
smsbot-prod-delivery-status
smsbot-dev-test-notifications

# CloudWatch Log Groups
/aws/lambda/smsbot-prod-sms-handler
/aws/sns/smsbot-prod-delivery-logs

# CloudWatch Dashboards
smsbot-prod-operations
smsbot-dev-debugging
```

## Validation Rules

1. **Length Limits**: Respect AWS service limits (e.g., Lambda function names ≤ 64 chars)
2. **Character Restrictions**: Use only alphanumeric characters and hyphens
3. **Case Sensitivity**: Use lowercase for consistency
4. **No Spaces**: Replace spaces with hyphens
5. **Uniqueness**: Ensure global uniqueness where required (S3 buckets)

## CDK Implementation

### Stack Naming
```typescript
const stackName = `smsbot-${environment}-infrastructure`;
```

### Resource Naming Helper
```typescript
class NamingConvention {
  constructor(
    private project: string = 'smsbot',
    private environment: string
  ) {}

  // IAM Role naming
  iamRole(service: string, purpose: string): string {
    return `${this.project}-${this.environment}-${service}-role-${purpose}`;
  }

  // Lambda function naming
  lambdaFunction(service: string, purpose: string): string {
    return `${this.project}-${this.environment}-${service}-${purpose}`;
  }

  // DynamoDB table naming
  dynamoTable(dataType: string): string {
    return `${this.project}-${this.environment}-${dataType}`;
  }

  // SNS topic naming
  snsTopic(messageType: string): string {
    return `${this.project}-${this.environment}-${messageType}`;
  }

  // CloudWatch log group naming
  logGroup(service: string, component: string): string {
    return `/aws/${service}/${this.project}-${this.environment}-${component}`;
  }

  // Dashboard naming
  dashboard(purpose: string): string {
    return `${this.project}-${this.environment}-${purpose}`;
  }

  // Standard tags
  standardTags(service: string): { [key: string]: string } {
    return {
      Project: 'SMSBot',
      Environment: this.environment,
      Service: service,
      Owner: 'infrastructure-team',
      CostCenter: 'engineering',
      CreatedBy: 'cdk',
      ManagedBy: 'infrastructure-team'
    };
  }
}
```

## Migration Strategy

If existing resources don't follow this convention:

1. **New Resources**: Apply naming convention immediately
2. **Existing Resources**: Plan migration during maintenance windows
3. **Aliases**: Use aliases where supported during transition
4. **Documentation**: Update all references to old names

## Compliance Checklist

- [ ] All resource names follow the standard pattern
- [ ] Environment is clearly identified in names
- [ ] Service category is included
- [ ] Names are within AWS character limits
- [ ] Standard tags are applied to all resources
- [ ] Names are documented in infrastructure code
- [ ] Team has reviewed and approved naming convention

## Benefits

1. **Cost Tracking**: Easy filtering by project/environment/service
2. **Security**: Clear identification of resource ownership
3. **Operations**: Simplified resource management and troubleshooting
4. **Compliance**: Consistent tagging for governance
5. **Automation**: Predictable naming for scripts and tools
