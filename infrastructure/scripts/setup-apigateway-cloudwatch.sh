#!/bin/bash

# Setup API Gateway CloudWatch Logging Role
# This is a one-time account-level setup required for API Gateway logging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default profile
PROFILE=${1:-boss}

echo -e "${BLUE}🔧 Setting up API Gateway CloudWatch Logging${NC}"
echo -e "${BLUE}=============================================${NC}"
echo -e "AWS Profile: ${GREEN}${PROFILE}${NC}"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity --profile $PROFILE >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured or profile '$PROFILE' not found${NC}"
    echo -e "${YELLOW}💡 Run: aws sso login --profile $PROFILE${NC}"
    exit 1
fi

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --profile $PROFILE --query Account --output text)
echo -e "Account ID: ${GREEN}${ACCOUNT_ID}${NC}"

# Check if role already exists
ROLE_NAME="APIGatewayCloudWatchLogsRole"
if aws iam get-role --role-name $ROLE_NAME --profile $PROFILE >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Role $ROLE_NAME already exists${NC}"
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --profile $PROFILE --query 'Role.Arn' --output text)
else
    echo -e "${BLUE}📝 Creating IAM role: $ROLE_NAME${NC}"
    
    # Create the role
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://policies/apigateway-cloudwatch-trust-policy.json \
        --profile $PROFILE
    
    echo -e "${GREEN}✅ Role created successfully${NC}"
    
    # Attach the managed policy
    echo -e "${BLUE}📎 Attaching CloudWatch logs policy${NC}"
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs \
        --profile $PROFILE
    
    echo -e "${GREEN}✅ Policy attached successfully${NC}"
    
    # Get the role ARN
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --profile $PROFILE --query 'Role.Arn' --output text)
fi

echo -e "Role ARN: ${GREEN}${ROLE_ARN}${NC}"

# Check current API Gateway account settings
echo -e "${BLUE}🔍 Checking current API Gateway account settings${NC}"
CURRENT_ROLE=$(aws apigateway get-account --profile $PROFILE --query 'cloudwatchRoleArn' --output text 2>/dev/null || echo "None")

if [ "$CURRENT_ROLE" = "None" ] || [ "$CURRENT_ROLE" = "null" ]; then
    echo -e "${YELLOW}⚠️  No CloudWatch role currently set in API Gateway${NC}"
    
    echo -e "${BLUE}🔧 Setting CloudWatch role in API Gateway account settings${NC}"
    aws apigateway update-account \
        --patch-operations op='replace',path='/cloudwatchRoleArn',value="$ROLE_ARN" \
        --profile $PROFILE
    
    echo -e "${GREEN}✅ CloudWatch role set successfully${NC}"
else
    echo -e "${GREEN}✅ CloudWatch role already configured: $CURRENT_ROLE${NC}"
fi

# Verify the setup
echo -e "${BLUE}🔍 Verifying setup${NC}"
FINAL_ROLE=$(aws apigateway get-account --profile $PROFILE --query 'cloudwatchRoleArn' --output text)
echo -e "Final CloudWatch Role ARN: ${GREEN}${FINAL_ROLE}${NC}"

echo ""
echo -e "${GREEN}🎉 API Gateway CloudWatch logging setup complete!${NC}"
echo -e "${BLUE}💡 You can now deploy your CDK stack with API Gateway logging enabled${NC}"
