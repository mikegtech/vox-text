# 🚀 Quick Start Guide - AWS SSO Deployment

## ✅ Your AWS SSO Setup is Ready!

Your `boss` profile is configured and active:
- **Account ID**: 099427795947
- **Region**: us-east-1
- **Profile**: boss

## 🎯 Deploy in 3 Simple Steps

### Step 1: Setup Environment
```bash
cd infrastructure

# Set up AWS environment (run this in each new terminal session)
source ./scripts/setup-aws-env.sh boss
```

### Step 2: Deploy to Development
```bash
# Quick deployment to dev environment
./deploy-with-boss.sh dev your-company

# This will:
# ✅ Validate your AWS SSO session
# ✅ Bootstrap CDK (first time only)
# ✅ Deploy all SMS bot infrastructure
# ✅ Apply proper naming and tagging
```

### Step 3: Verify Deployment
After deployment, check the outputs for:
- Lambda function ARN
- DynamoDB table names
- SNS topic ARNs
- CloudWatch dashboard URL

## 🔧 Available Commands

### Environment Setup
```bash
# Check if SSO session is valid
aws sts get-caller-identity --profile boss

# Login if session expired
aws sso login --profile boss

# Set environment variables
source ./scripts/setup-aws-env.sh boss
```

### Deployment Commands
```bash
# Deploy to different environments
./deploy-with-boss.sh dev your-company          # Development
./deploy-with-boss.sh staging your-company      # Staging  
./deploy-with-boss.sh prod your-company         # Production (requires confirmation)

# With custom tenant
./deploy-with-boss.sh dev acme-corp client-a
```

### CDK Commands
```bash
# Synthesize CloudFormation template
npx cdk synth --profile boss --context environment=dev --context company=your-company

# Show differences
npx cdk diff --profile boss --context environment=dev --context company=your-company

# Deploy manually
npx cdk deploy --profile boss --context environment=dev --context company=your-company
```

### Validation and Testing
```bash
# Validate naming and tagging
npx ts-node scripts/validate-naming.ts

# Build and test
npm run build
npm run test
```

## 📊 What Gets Deployed

### Resources Created (Development)
```
smsbot-dev-infrastructure (Stack)
├── smsbot-dev-messaging-role-sns-logs (IAM Role)
├── smsbot-dev-compute-role-lambda-execution (IAM Role)  
├── smsbot-dev-conversations (DynamoDB Table)
├── smsbot-dev-analytics (DynamoDB Table)
├── smsbot-dev-inbound-sms (SNS Topic)
├── smsbot-dev-delivery-status (SNS Topic)
├── smsbot-dev-messaging-sms-handler (Lambda Function)
└── smsbot-dev-operations (CloudWatch Dashboard)
```

### Tags Applied to All Resources
```json
{
  "Project": "SMSBot",
  "Company": "your-company", 
  "Tenant": "dev-tenant",
  "Environment": "dev",
  "Service": "messaging|compute|storage|monitoring|security",
  "Owner": "infrastructure-team",
  "CostCenter": "engineering-dev",
  "CreatedBy": "cdk",
  "ManagedBy": "infrastructure-team",
  "OffHoursShutdown": "enabled|disabled"
}
```

## 💰 Cost Optimization

### Development Environment
- **Lambda**: `OffHoursShutdown: enabled` (60-80% savings)
- **Memory**: 256MB (cost-optimized)
- **Log Retention**: 7 days
- **No Reserved Concurrency**: Pay per use

### Production Environment  
- **All Services**: `OffHoursShutdown: disabled` (always-on)
- **Memory**: 1024MB (performance-optimized)
- **Log Retention**: 90 days
- **Data Protection**: Deletion protection enabled

## 🔍 Monitoring

### CloudWatch Dashboard
Access your dashboard at:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=smsbot-dev-operations
```

### Key Metrics
- SMS messages published (SNS)
- Lambda invocations and errors
- Lambda duration and memory usage
- DynamoDB read/write operations

## 🆘 Troubleshooting

### Common Issues

**1. SSO Session Expired**
```bash
aws sso login --profile boss
source ./scripts/setup-aws-env.sh boss
```

**2. CDK Bootstrap Required**
```bash
npx cdk bootstrap --profile boss
```

**3. Resource Name Conflicts**
- Check for existing resources with same names
- Verify environment context is correct

**4. Permission Issues**
- Ensure your SSO role has necessary permissions
- Check CloudFormation events for detailed errors

### Getting Help
1. Run validation: `npx ts-node scripts/validate-naming.ts`
2. Check synthesis: `npx cdk synth --profile boss --context environment=dev`
3. Review CloudFormation console for deployment details

## 🎉 You're Ready to Deploy!

Your SMS Bot infrastructure is configured with:
- ✅ Enterprise naming conventions
- ✅ Comprehensive tagging strategy  
- ✅ Multi-tenant support
- ✅ Cost optimization features
- ✅ AWS SSO integration

Run this command to get started:
```bash
cd infrastructure
source ./scripts/setup-aws-env.sh boss
./deploy-with-boss.sh dev your-company
```
