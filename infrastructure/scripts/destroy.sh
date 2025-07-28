#!/bin/bash

# SMS Bot Infrastructure Destruction Script
# Usage: ./scripts/destroy.sh [environment] [company] [tenant] [aws-profile]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
COMPANY=${2:-your-company}
TENANT=${3:-}
AWS_PROFILE=${4:-boss}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo -e "${YELLOW}Valid environments: dev, staging, prod${NC}"
    exit 1
fi

echo -e "${RED}🗑️  SMS Bot Infrastructure Destruction${NC}"
echo -e "${RED}======================================${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Company: ${YELLOW}$COMPANY${NC}"
echo -e "Tenant: ${YELLOW}${TENANT:-${ENVIRONMENT}-tenant}${NC}"
echo -e "AWS Profile: ${YELLOW}$AWS_PROFILE${NC}"
echo ""

# Set AWS profile environment variable
export AWS_PROFILE=$AWS_PROFILE

# Check if AWS profile exists and is configured
if ! aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
    echo -e "${RED}❌ AWS profile '$AWS_PROFILE' not found${NC}"
    echo -e "${YELLOW}Available profiles:${NC}"
    aws configure list-profiles
    echo -e "${YELLOW}Please configure your profile or use a different one${NC}"
    exit 1
fi

# Check if AWS SSO session is valid
echo -e "${YELLOW}🔐 Checking AWS SSO session...${NC}"
if ! aws sts get-caller-identity --profile $AWS_PROFILE > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  AWS SSO session expired or not logged in${NC}"
    echo -e "${YELLOW}🔄 Attempting to login to AWS SSO...${NC}"
    
    if ! aws sso login --profile $AWS_PROFILE; then
        echo -e "${RED}❌ Failed to login to AWS SSO${NC}"
        echo -e "${YELLOW}Please run: aws sso login --profile $AWS_PROFILE${NC}"
        exit 1
    fi
fi

# Get AWS account and region info
AWS_ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
AWS_REGION=$(aws configure get region --profile $AWS_PROFILE || echo "us-east-1")

echo -e "AWS Account: ${YELLOW}$AWS_ACCOUNT${NC}"
echo -e "AWS Region: ${YELLOW}$AWS_REGION${NC}"
echo ""

# Set up environment variables for CDK
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT
export CDK_DEFAULT_REGION=$AWS_REGION
export AWS_DEFAULT_REGION=$AWS_REGION

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Extra confirmation for production
if [ "$ENVIRONMENT" = "prod" ]; then
    echo -e "${RED}⚠️  PRODUCTION STACK DESTRUCTION${NC}"
    echo -e "${RED}This will PERMANENTLY DELETE all production resources!${NC}"
    echo -e "${YELLOW}AWS Account: $AWS_ACCOUNT${NC}"
    echo -e "${YELLOW}AWS Profile: $AWS_PROFILE${NC}"
    echo ""
    echo -e "${RED}Resources that will be DELETED:${NC}"
    echo -e "- Lambda functions and their logs"
    echo -e "- DynamoDB tables and ALL DATA"
    echo -e "- SNS topics and subscriptions"
    echo -e "- IAM roles and policies"
    echo -e "- CloudWatch dashboards and alarms"
    echo ""
    read -p "Type 'DELETE PRODUCTION' to confirm: " -r
    if [[ ! $REPLY == "DELETE PRODUCTION" ]]; then
        echo -e "${YELLOW}Destruction cancelled.${NC}"
        exit 0
    fi
else
    echo -e "${YELLOW}⚠️  This will delete all $ENVIRONMENT resources${NC}"
    echo -e "${YELLOW}AWS Account: $AWS_ACCOUNT${NC}"
    echo -e "${YELLOW}AWS Profile: $AWS_PROFILE${NC}"
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Destruction cancelled.${NC}"
        exit 0
    fi
fi

# Show what will be destroyed
echo -e "${YELLOW}📊 Checking current stack resources...${NC}"
cdk diff \
    --profile $AWS_PROFILE \
    --context environment=$ENVIRONMENT \
    --context company=$COMPANY \
    ${TENANT:+--context tenant=$TENANT} || true

echo ""
echo -e "${RED}🗑️  Destroying infrastructure...${NC}"

# Destroy the stack
cdk destroy \
    --profile $AWS_PROFILE \
    --context environment=$ENVIRONMENT \
    --context company=$COMPANY \
    ${TENANT:+--context tenant=$TENANT} \
    --force

# Check destruction status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stack destroyed successfully!${NC}"
    echo ""
    
    # Clean up local files
    echo -e "${YELLOW}🧹 Cleaning up local files...${NC}"
    rm -f outputs-$ENVIRONMENT-$AWS_PROFILE.json
    rm -f cdk.out/manifest.json 2>/dev/null || true
    
    echo -e "${BLUE}📋 Cleanup Complete:${NC}"
    echo -e "- CloudFormation stack deleted"
    echo -e "- Local output files removed"
    echo -e "- CDK synthesis cache cleared"
    echo ""
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        echo -e "${RED}⚠️  Production environment destroyed${NC}"
        echo -e "${YELLOW}Remember to:${NC}"
        echo -e "1. Verify all resources are deleted in AWS Console"
        echo -e "2. Check for any remaining costs in billing"
        echo -e "3. Update team documentation"
    fi
    
else
    echo -e "${RED}❌ Stack destruction failed!${NC}"
    echo -e "${YELLOW}Some resources may still exist. Check AWS Console.${NC}"
    exit 1
fi
