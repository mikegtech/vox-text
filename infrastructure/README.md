# SMS Bot Infrastructure - CDK Project

This CDK project creates the complete AWS infrastructure for the SMS Bot system as defined in the [PRD document](../.taskmaster/docs/aws-account-prep-prd.md).

## 🏗️ Architecture Overview

The infrastructure includes:
- **IAM Roles**: Service roles for SNS logging and Lambda execution
- **SNS Topics**: Inbound SMS and delivery status topics
- **Lambda Functions**: SMS message processing
- **DynamoDB Tables**: Conversation and analytics storage
- **CloudWatch**: Logging, monitoring, and dashboards

## 📋 Prerequisites

- Node.js 18+ and npm
- AWS CLI configured with appropriate credentials
- CDK CLI installed (`npm install -g aws-cdk`)
- Appropriate AWS permissions for resource creation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd infrastructure
npm install
```

### 2. Setup AWS Environment (SSO)
```bash
# Set up your AWS environment with the 'boss' profile
source ./scripts/setup-aws-env.sh boss

# Or if your SSO session is expired, login first:
aws sso login --profile boss
source ./scripts/setup-aws-env.sh boss
```

### 3. Validate Configuration
```bash
# Run validation script
npx ts-node scripts/validate-naming.ts
```

### 4. Deploy to Development
```bash
# Quick deployment with boss profile
./deploy-with-boss.sh dev your-company

# Or use the full deployment script
./scripts/deploy.sh dev your-company dev-tenant boss
```

### 5. Deploy to Other Environments
```bash
# Deploy to staging
./deploy-with-boss.sh staging your-company staging-client

# Deploy to production (requires confirmation)
./deploy-with-boss.sh prod your-company prod-client
```

## 🏷️ Naming Convention

All resources follow the standardized naming pattern:
```
{project}-{environment}-{service}-{resource-type}-{identifier}
```

### Examples:
- **Lambda Function**: `smsbot-prod-messaging-sms-handler`
- **DynamoDB Table**: `smsbot-prod-conversations`
- **SNS Topic**: `smsbot-prod-inbound-sms`
- **IAM Role**: `smsbot-prod-compute-role-lambda-execution`

## 🏷️ Tagging Strategy

### Mandatory Tags (Applied to ALL resources):
```json
{
  "Project": "SMSBot",
  "Company": "your-company",
  "Tenant": "tenant-identifier",
  "Environment": "dev|staging|prod",
  "Service": "messaging|compute|storage|monitoring|security",
  "Owner": "infrastructure-team",
  "CostCenter": "engineering-{env}",
  "CreatedBy": "cdk",
  "ManagedBy": "infrastructure-team",
  "OffHoursShutdown": "enabled|disabled"
}
```

### Cost Optimization:
- **Development**: Compute resources tagged with `OffHoursShutdown: enabled` (60-80% savings)
- **Production**: Critical services tagged with `OffHoursShutdown: disabled`

## 🌍 Environment Configuration

### Development Environment
- **SMS Spend Limit**: $10/month
- **Lambda Memory**: 256MB
- **Log Retention**: 7 days
- **Off-Hours Shutdown**: Enabled for compute
- **Backup**: Disabled for cost optimization

### Staging Environment
- **SMS Spend Limit**: $50/month
- **Lambda Memory**: 512MB
- **Log Retention**: 14 days
- **Off-Hours Shutdown**: Disabled
- **Backup**: Enabled

### Production Environment
- **SMS Spend Limit**: $1000/month
- **Lambda Memory**: 1024MB
- **Log Retention**: 90 days
- **Off-Hours Shutdown**: Disabled
- **Backup**: Enabled with deletion protection

## 🔐 AWS SSO Configuration

This project is configured to work with AWS SSO profiles. The deployment scripts default to using the `boss` profile.

### Setup AWS SSO Profile
```bash
# Configure your SSO profile (if not already done)
aws configure sso --profile boss

# Login to AWS SSO
aws sso login --profile boss

# Set up environment variables
source ./scripts/setup-aws-env.sh boss
```

### Available AWS Commands
```bash
# Quick deployment with boss profile
./deploy-with-boss.sh dev your-company

# Manual deployment with specific profile
./scripts/deploy.sh dev your-company tenant boss

# CDK commands with profile
npx cdk synth --profile boss --context environment=dev
npx cdk deploy --profile boss --context environment=dev
```

### Environment Variables Set
When you source the setup script, these variables are configured:
- `AWS_PROFILE=boss`
- `AWS_ACCOUNT_ID=your-account-id`
- `AWS_DEFAULT_REGION=us-east-1`
- `CDK_DEFAULT_ACCOUNT=your-account-id`
- `CDK_DEFAULT_REGION=us-east-1`

## 📁 Project Structure

```
infrastructure/
├── bin/
│   └── infrastructure.ts          # CDK app entry point
├── lib/
│   ├── infrastructure-stack.ts    # Main infrastructure stack
│   ├── naming-convention.ts       # Naming utility class
│   └── tagging-strategy.ts        # Tagging utility class
├── config/
│   └── environments.ts            # Environment configurations
├── docs/
│   ├── naming-convention.md       # Naming standards
│   └── tagging-standards.md       # Tagging documentation
├── scripts/
│   ├── deploy.sh                  # Deployment script
│   └── validate-naming.ts         # Validation script
├── test/
│   └── infrastructure.test.ts     # Unit tests
├── cdk.json                       # CDK configuration
├── package.json                   # Dependencies
└── README.md                      # This file
```

## 🛠️ Available Commands

### Build and Test
```bash
npm run build          # Compile TypeScript
npm run watch          # Watch for changes
npm run test           # Run unit tests
```

### CDK Commands
```bash
# Synthesize CloudFormation template
npx cdk synth --context environment=dev

# Show differences
npx cdk diff --context environment=dev

# Deploy stack
npx cdk deploy --context environment=dev --context company=your-company

# Destroy stack
npx cdk destroy --context environment=dev
```

### Validation and Utilities
```bash
# Validate naming and tagging
npx ts-node scripts/validate-naming.ts

# Deploy with script (recommended)
./scripts/deploy.sh dev your-company tenant-name
```

## 🔧 Configuration Options

### CDK Context Variables
- `environment`: Target environment (dev/staging/prod)
- `company`: Company name for tagging
- `tenant`: Tenant identifier (optional)

### Environment Variables
- `CDK_DEFAULT_ACCOUNT`: AWS account ID
- `CDK_DEFAULT_REGION`: AWS region
- `APP_VERSION`: Application version for tagging
- `DEPLOYMENT_ID`: Deployment identifier

## 📊 Monitoring and Observability

### CloudWatch Dashboard
Access the operations dashboard at:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=smsbot-{env}-operations
```

### Key Metrics
- SMS messages published
- Lambda invocations and errors
- Lambda duration and memory usage
- DynamoDB read/write capacity

### Log Groups
- Lambda logs: `/aws/lambda/smsbot-{env}-messaging-sms-handler`
- SNS delivery logs: `/aws/sns/smsbot-{env}-delivery-logs`

## 💰 Cost Management

### Cost Allocation Tags
Resources are tagged for cost tracking by:
- Environment (dev/staging/prod)
- Service (messaging/compute/storage)
- Company and Tenant
- Cost Center

### Cost Optimization Features
1. **Off-Hours Shutdown**: Dev compute resources auto-shutdown
2. **Right-Sizing**: Environment-specific resource sizing
3. **Log Retention**: Shorter retention in dev environments
4. **On-Demand Billing**: DynamoDB pay-per-request
5. **Spend Limits**: SNS monthly spend controls

### Estimated Monthly Costs
- **Development**: $5-15 (with off-hours shutdown)
- **Staging**: $25-75
- **Production**: $100-500 (depends on SMS volume)

## 🔒 Security

### IAM Roles
- **Least Privilege**: Minimal permissions for each service
- **Service Roles**: Dedicated roles for SNS and Lambda
- **No Hardcoded Credentials**: All access via IAM roles

### Data Protection
- **Encryption**: DynamoDB encryption at rest
- **Access Logging**: CloudWatch logs for all services
- **Data Classification**: Tagged by sensitivity level

### Compliance
- **Tagging**: Compliance tags for governance
- **Backup**: Production data backup enabled
- **Monitoring**: Comprehensive logging and alerting

## 🚨 Troubleshooting

### Common Issues

**1. CDK Bootstrap Required**
```bash
npx cdk bootstrap --context environment=dev
```

**2. AWS Credentials Not Configured**
```bash
aws configure
# or
export AWS_PROFILE=your-profile
```

**3. Resource Name Conflicts**
- Check existing resources with same names
- Verify environment context is set correctly

**4. Permission Denied**
- Ensure AWS credentials have necessary permissions
- Check IAM policies for CDK deployment

### Validation Failures
```bash
# Run validation script for detailed error messages
npx ts-node scripts/validate-naming.ts
```

## 📚 Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [SMS Bot PRD](../.taskmaster/docs/aws-account-prep-prd.md)
- [Naming Convention Guide](docs/naming-convention.md)
- [Tagging Standards](docs/tagging-standards.md)

## 🤝 Contributing

1. Follow the established naming convention
2. Apply appropriate tags to all resources
3. Update documentation for any changes
4. Run validation scripts before committing
5. Test in development environment first

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the validation script output
3. Contact the infrastructure team
4. Create an issue in the project repository

---

**Note**: This infrastructure follows the SMS Bot PRD requirements and implements AWS best practices for security, cost optimization, and operational excellence.
