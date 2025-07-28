#!/bin/bash

# SMS Bot Infrastructure Deployment Script (Python CDK)
# Usage: ./scripts/deploy.sh [environment] [company] [tenant] [aws-profile]

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

echo -e "${BLUE}🚀 SMS Bot Infrastructure Deployment${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Company: ${GREEN}$COMPANY${NC}"
echo -e "Tenant: ${GREEN}${TENANT:-${ENVIRONMENT}-tenant}${NC}"
echo -e "AWS Profile: ${GREEN}$AWS_PROFILE${NC}"
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

echo -e "AWS Account: ${GREEN}$AWS_ACCOUNT${NC}"
echo -e "AWS Region: ${GREEN}$AWS_REGION${NC}"
echo ""

# Set up environment variables for CDK
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT
export CDK_DEFAULT_REGION=$AWS_REGION
export AWS_DEFAULT_REGION=$AWS_REGION

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Check if m3_aws_standards is installed
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
if ! python3 -c "import m3_aws_standards" 2>/dev/null; then
    echo -e "${YELLOW}Installing m3_aws_standards package...${NC}"
    ~/.local/bin/pip install -e ./shared-standards
fi

# Validate structure
echo -e "${YELLOW}🔍 Validating infrastructure structure...${NC}"
if ! python3 test_structure.py; then
    echo -e "${RED}❌ Structure validation failed${NC}"
    exit 1
fi

# Bootstrap CDK if needed (only for first deployment)
if [ "$ENVIRONMENT" = "dev" ] || [ ! -f ".cdk-bootstrapped-$AWS_PROFILE" ]; then
    echo -e "${YELLOW}🥾 Bootstrapping CDK for profile $AWS_PROFILE...${NC}"
    cdk bootstrap \
        --profile $AWS_PROFILE \
        --context environment=$ENVIRONMENT \
        --context company=$COMPANY \
        ${TENANT:+--context tenant=$TENANT}
    touch .cdk-bootstrapped-$AWS_PROFILE
fi

# Synthesize CloudFormation template
echo -e "${YELLOW}🏗️  Synthesizing CloudFormation template...${NC}"
python3 app.py \
    --context environment=$ENVIRONMENT \
    --context company=$COMPANY \
    ${TENANT:+--context tenant=$TENANT}

# Show diff if stack exists
echo -e "${YELLOW}📊 Checking for changes...${NC}"
if cdk diff \
    --profile $AWS_PROFILE \
    --context environment=$ENVIRONMENT \
    --context company=$COMPANY \
    ${TENANT:+--context tenant=$TENANT} > /dev/null 2>&1; then
    cdk diff \
        --profile $AWS_PROFILE \
        --context environment=$ENVIRONMENT \
        --context company=$COMPANY \
        ${TENANT:+--context tenant=$TENANT}
fi

# Confirm deployment for production
if [ "$ENVIRONMENT" = "prod" ]; then
    echo -e "${RED}⚠️  PRODUCTION DEPLOYMENT${NC}"
    echo -e "${YELLOW}This will deploy to production environment.${NC}"
    echo -e "${YELLOW}AWS Account: $AWS_ACCOUNT${NC}"
    echo -e "${YELLOW}AWS Profile: $AWS_PROFILE${NC}"
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled.${NC}"
        exit 0
    fi
fi

# Deploy the stack
echo -e "${YELLOW}🚀 Deploying infrastructure...${NC}"
cdk deploy \
    --profile $AWS_PROFILE \
    --context environment=$ENVIRONMENT \
    --context company=$COMPANY \
    ${TENANT:+--context tenant=$TENANT} \
    --require-approval never \
    --outputs-file outputs-$ENVIRONMENT-$AWS_PROFILE.json

# Check deployment status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    
    # Display outputs
    if [ -f "outputs-$ENVIRONMENT-$AWS_PROFILE.json" ]; then
        echo -e "${BLUE}📋 Stack Outputs:${NC}"
        cat outputs-$ENVIRONMENT-$AWS_PROFILE.json | jq -r 'to_entries[] | "\(.key): \(.value)"' 2>/dev/null || cat outputs-$ENVIRONMENT-$AWS_PROFILE.json
        echo ""
    fi
    
    # Display next steps
    echo -e "${BLUE}🎯 Next Steps:${NC}"
    echo -e "1. Configure SNS SMS settings in AWS Console"
    echo -e "2. Test Lambda function with sample SMS"
    echo -e "3. Monitor CloudWatch dashboard"
    echo -e "4. Set up billing alerts"
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        echo -e "5. ${YELLOW}Remember: Dev resources have OffHoursShutdown enabled${NC}"
    fi
    
    echo -e "${BLUE}🔗 Useful Links:${NC}"
    echo -e "AWS Console: https://console.aws.amazon.com/"
    echo -e "CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:name=smsbot-$ENVIRONMENT-monitoring-dashboard-operations"
    
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi
