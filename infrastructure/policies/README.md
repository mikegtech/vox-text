# AWS IAM Policies

This folder contains IAM policies used by the SMS Bot infrastructure.

## API Gateway CloudWatch Logging Setup

### Problem
API Gateway requires a CloudWatch Logs role to be configured at the AWS account level before it can enable logging on API Gateway stages. This is a one-time account-level setup.

### Error Message
```
Resource handler returned message: "CloudWatch Logs role ARN must be set in account settings to enable logging (Service: ApiGateway, Status Code: 400, Request ID: ...)"
```

### Quick Fix
Run the automated setup script:
```bash
./scripts/setup-apigateway-cloudwatch.sh boss
```

### Manual Setup (if needed)

#### Files in this directory:
- `apigateway-cloudwatch-trust-policy.json` - Trust policy for the CloudWatch logging role

#### Manual Commands:
```bash
# Create the IAM role
aws iam create-role \
  --role-name APIGatewayCloudWatchLogsRole \
  --assume-role-policy-document file://policies/apigateway-cloudwatch-trust-policy.json \
  --profile boss

# Attach the managed policy for CloudWatch logs
aws iam attach-role-policy \
  --role-name APIGatewayCloudWatchLogsRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs \
  --profile boss

# Get the role ARN
ROLE_ARN=$(aws iam get-role \
  --role-name APIGatewayCloudWatchLogsRole \
  --query 'Role.Arn' \
  --output text \
  --profile boss)

# Set the CloudWatch role in API Gateway account settings
aws apigateway update-account \
  --patch-operations op='replace',path='/cloudwatchRoleArn',value="$ROLE_ARN" \
  --profile boss
```

### Verification
After setup, verify the configuration:
```bash
aws apigateway get-account --profile boss
```

The response should include:
```json
{
  "cloudwatchRoleArn": "arn:aws:iam::ACCOUNT-ID:role/APIGatewayCloudWatchLogsRole",
  ...
}
```

### Notes
- This is a **one-time account-level setup**
- The role uses the AWS managed policy `AmazonAPIGatewayPushToCloudWatchLogs`
- Once configured, all API Gateway stages in the account can enable CloudWatch logging
- This setup is required for the Telnyx webhook API Gateway in the SMS Bot infrastructure
- The automated script `./scripts/setup-apigateway-cloudwatch.sh` handles this entire process
