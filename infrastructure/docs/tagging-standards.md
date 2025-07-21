# AWS Resource Tagging Standards - SMS Bot Project

## Overview

This document defines the standardized tagging strategy for all AWS resources in the SMS Bot infrastructure. Consistent tagging enables cost allocation, security governance, operational management, and compliance tracking across all environments.

## Tagging Strategy

### Core Principles

1. **Consistency**: All resources must follow the same tagging schema
2. **Automation**: Tags should be applied programmatically via CDK
3. **Governance**: Mandatory tags enforced through policies
4. **Cost Management**: Enable detailed cost tracking and allocation
5. **Security**: Support access control and compliance requirements

### Tag Categories

#### 1. Mandatory Tags (Required on ALL resources)
These tags are required on every AWS resource without exception:

```json
{
  "Project": "SMSBot",
  "Company": "company-name",
  "Tenant": "tenant-identifier",
  "Environment": "dev|staging|prod",
  "Service": "messaging|compute|storage|monitoring|security|network",
  "Owner": "team-name",
  "CostCenter": "cost-center-code",
  "CreatedBy": "cdk|manual|terraform",
  "ManagedBy": "infrastructure-team",
  "OffHoursShutdown": "enabled|disabled"
}
```

#### 2. Operational Tags (Recommended)
These tags support day-to-day operations:

```json
{
  "Application": "sms-bot",
  "Component": "api|processor|storage|monitoring",
  "Version": "v1.0.0",
  "DeploymentId": "deployment-identifier",
  "LastModified": "2024-01-15T10:30:00Z"
}
```

#### 3. Security Tags (Required for sensitive resources)
These tags support security and compliance:

```json
{
  "DataClassification": "public|internal|confidential|restricted",
  "Compliance": "required|not-required",
  "BackupRequired": "true|false",
  "EncryptionRequired": "true|false"
}
```

#### 4. Cost Management Tags
These tags enable detailed cost tracking:

```json
{
  "BillingCode": "billing-code",
  "BusinessUnit": "engineering|product|sales",
  "CostAllocation": "development|production|shared",
  "Budget": "budget-name"
}
```

## Environment-Specific Tagging

### Development Environment
```json
{
  "Project": "SMSBot",
  "Company": "your-company",
  "Tenant": "dev-tenant",
  "Environment": "dev",
  "Service": "messaging",
  "Owner": "infrastructure-team",
  "CostCenter": "engineering-dev",
  "CreatedBy": "cdk",
  "ManagedBy": "infrastructure-team",
  "OffHoursShutdown": "enabled",
  "DataClassification": "internal",
  "BackupRequired": "false"
}
```

### Staging Environment
```json
{
  "Project": "SMSBot",
  "Company": "your-company",
  "Tenant": "staging-tenant",
  "Environment": "staging",
  "Service": "messaging",
  "Owner": "infrastructure-team",
  "CostCenter": "engineering-staging",
  "CreatedBy": "cdk",
  "ManagedBy": "infrastructure-team",
  "OffHoursShutdown": "disabled",
  "DataClassification": "internal",
  "BackupRequired": "true",
  "Compliance": "required"
}
```

### Production Environment
```json
{
  "Project": "SMSBot",
  "Company": "your-company",
  "Tenant": "prod-tenant",
  "Environment": "prod",
  "Service": "messaging",
  "Owner": "infrastructure-team",
  "CostCenter": "engineering-prod",
  "CreatedBy": "cdk",
  "ManagedBy": "infrastructure-team",
  "OffHoursShutdown": "disabled",
  "DataClassification": "confidential",
  "BackupRequired": "true",
  "Compliance": "required",
  "EncryptionRequired": "true"
}
```

## Off-Hours Shutdown Strategy

### Cost Optimization Through Scheduling

The `OffHoursShutdown` tag enables automatic resource management for cost savings:

- **enabled**: Resource can be shut down during off-hours (8 PM - 8 AM, weekends)
- **disabled**: Resource must run 24/7 (production services, databases, monitoring)

### Resources Eligible for Off-Hours Shutdown

**Development Environment:**
- Lambda functions (can be scaled to zero)
- EC2 instances (if used)
- RDS instances (non-production databases)
- ECS services (development workloads)

**Staging Environment:**
- Selected compute resources
- Non-critical services
- Development tools and utilities

**Production Environment:**
- Generally disabled for all resources
- Exception: Batch processing jobs, reporting services

### Implementation Notes

1. **Lambda Functions**: Automatically scale to zero when not in use
2. **Always-On Resources**: Databases, monitoring, security services
3. **Automation**: Use AWS Instance Scheduler or custom Lambda functions
4. **Notifications**: Alert teams before shutdown/startup cycles

## Tag Validation Rules

### Mandatory Tag Validation
```typescript
const MANDATORY_TAGS = [
  'Project',
  'Company',
  'Tenant',
  'Environment', 
  'Service',
  'Owner',
  'CostCenter',
  'CreatedBy',
  'ManagedBy',
  'OffHoursShutdown'
];
```

### Tag Value Constraints
```typescript
const TAG_CONSTRAINTS = {
  'Environment': ['dev', 'staging', 'prod'],
  'Service': ['messaging', 'compute', 'storage', 'monitoring', 'security', 'network'],
  'CreatedBy': ['cdk', 'manual', 'terraform'],
  'OffHoursShutdown': ['enabled', 'disabled'],
  'DataClassification': ['public', 'internal', 'confidential', 'restricted'],
  'BackupRequired': ['true', 'false'],
  'Compliance': ['required', 'not-required']
};
```

## Cost Allocation Strategy

### Multi-Tenant Cost Tracking
```json
{
  "Company": "your-company",
  "Tenant": "client-a",
  "CostCenter": "engineering-prod",
  "BillingCode": "ENG-SMS-CLIENT-A",
  "CostAllocation": "production"
}
```

### Off-Hours Cost Savings
- **Development**: 60-80% cost reduction with off-hours shutdown
- **Staging**: 40-60% cost reduction for eligible resources
- **Production**: Minimal impact, focus on right-sizing

## Implementation Examples

### CDK Tag Application
```typescript
// Stack-level mandatory tags
const mandatoryTags = {
  Project: 'SMSBot',
  Company: 'your-company',
  Tenant: environment === 'prod' ? 'prod-tenant' : 'dev-tenant',
  Environment: environment,
  CreatedBy: 'cdk',
  ManagedBy: 'infrastructure-team'
};

// Apply to all resources in stack
Object.entries(mandatoryTags).forEach(([key, value]) => {
  cdk.Tags.of(this).add(key, value);
});

// Service-specific tags
cdk.Tags.of(lambdaFunction).add('Service', 'compute');
cdk.Tags.of(lambdaFunction).add('OffHoursShutdown', environment === 'dev' ? 'enabled' : 'disabled');
```

### Resource-Specific Tagging
```typescript
// Lambda function - can be shut down in dev
lambdaFunction.tags.setTag('OffHoursShutdown', 'enabled');

// DynamoDB table - always on
dynamoTable.tags.setTag('OffHoursShutdown', 'disabled');

// SNS topic - always on for messaging
snsTopic.tags.setTag('OffHoursShutdown', 'disabled');
```

## Best Practices

### Do's
✅ Apply mandatory tags to all resources
✅ Use `OffHoursShutdown: enabled` for dev resources
✅ Keep `OffHoursShutdown: disabled` for critical services
✅ Include Company and Tenant for multi-tenant tracking
✅ Validate tags before resource creation
✅ Use automation for consistent tagging

### Don'ts
❌ Don't enable off-hours shutdown for databases in production
❌ Don't use sensitive information in tag values
❌ Don't create tags manually in console
❌ Don't ignore tag validation errors
❌ Don't enable shutdown for monitoring/security resources

## Conclusion

This simplified tagging strategy focuses on essential tags for resource management, cost optimization, and multi-tenant tracking. The `OffHoursShutdown` tag enables significant cost savings in development environments while maintaining production reliability.
