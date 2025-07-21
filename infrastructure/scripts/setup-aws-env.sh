#!/bin/bash

# AWS Environment Setup Script for SMS Bot Infrastructure
# Usage: source ./scripts/setup-aws-env.sh [profile-name]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default profile
AWS_PROFILE_NAME=${1:-boss}

echo -e "${BLUE}🔧 Setting up AWS Environment${NC}"
echo -e "${BLUE}=============================${NC}"

# Set AWS profile
export AWS_PROFILE=$AWS_PROFILE_NAME
echo -e "AWS Profile: ${GREEN}$AWS_PROFILE${NC}"

# Check if profile exists
if ! aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
    echo -e "${RED}❌ AWS profile '$AWS_PROFILE' not found${NC}"
    echo -e "${YELLOW}Available profiles:${NC}"
    aws configure list-profiles
    echo -e "${YELLOW}Please configure your profile first${NC}"
    return 1
fi

# Check if SSO session is valid
echo -e "${YELLOW}🔐 Checking AWS SSO session...${NC}"
if aws sts get-caller-identity --profile $AWS_PROFILE > /dev/null 2>&1; then
    # Get account and region info
    AWS_ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
    AWS_REGION=$(aws configure get region --profile $AWS_PROFILE || echo "us-east-1")
    
    echo -e "${GREEN}✅ AWS SSO session is valid${NC}"
    echo -e "Account ID: ${GREEN}$AWS_ACCOUNT${NC}"
    echo -e "Region: ${GREEN}$AWS_REGION${NC}"
    
    # Export additional environment variables
    export AWS_ACCOUNT_ID=$AWS_ACCOUNT
    export AWS_DEFAULT_REGION=$AWS_REGION
    export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT
    export CDK_DEFAULT_REGION=$AWS_REGION
    
    echo ""
    echo -e "${BLUE}🌍 Environment Variables Set:${NC}"
    echo -e "AWS_PROFILE=${GREEN}$AWS_PROFILE${NC}"
    echo -e "AWS_ACCOUNT_ID=${GREEN}$AWS_ACCOUNT_ID${NC}"
    echo -e "AWS_DEFAULT_REGION=${GREEN}$AWS_DEFAULT_REGION${NC}"
    echo -e "CDK_DEFAULT_ACCOUNT=${GREEN}$CDK_DEFAULT_ACCOUNT${NC}"
    echo -e "CDK_DEFAULT_REGION=${GREEN}$CDK_DEFAULT_REGION${NC}"
    
else
    echo -e "${YELLOW}⚠️  AWS SSO session expired or not logged in${NC}"
    echo -e "${YELLOW}🔄 Attempting to login to AWS SSO...${NC}"
    
    if aws sso login --profile $AWS_PROFILE; then
        # Get account and region info after successful login
        AWS_ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
        AWS_REGION=$(aws configure get region --profile $AWS_PROFILE || echo "us-east-1")
        
        echo -e "${GREEN}✅ Successfully logged in to AWS SSO${NC}"
        echo -e "Account ID: ${GREEN}$AWS_ACCOUNT${NC}"
        echo -e "Region: ${GREEN}$AWS_REGION${NC}"
        
        # Export environment variables
        export AWS_ACCOUNT_ID=$AWS_ACCOUNT
        export AWS_DEFAULT_REGION=$AWS_REGION
        export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT
        export CDK_DEFAULT_REGION=$AWS_REGION
        
        echo ""
        echo -e "${BLUE}🌍 Environment Variables Set:${NC}"
        echo -e "AWS_PROFILE=${GREEN}$AWS_PROFILE${NC}"
        echo -e "AWS_ACCOUNT_ID=${GREEN}$AWS_ACCOUNT_ID${NC}"
        echo -e "AWS_DEFAULT_REGION=${GREEN}$AWS_DEFAULT_REGION${NC}"
        echo -e "CDK_DEFAULT_ACCOUNT=${GREEN}$CDK_DEFAULT_ACCOUNT${NC}"
        echo -e "CDK_DEFAULT_REGION=${GREEN}$CDK_DEFAULT_REGION${NC}"
    else
        echo -e "${RED}❌ Failed to login to AWS SSO${NC}"
        echo -e "${YELLOW}Please run manually: aws sso login --profile $AWS_PROFILE${NC}"
        return 1
    fi
fi

echo ""
echo -e "${GREEN}🎉 AWS environment setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Available Commands:${NC}"
echo -e "Deploy to dev:     ${YELLOW}./scripts/deploy.sh dev your-company${NC}"
echo -e "Deploy to prod:    ${YELLOW}./scripts/deploy.sh prod your-company${NC}"
echo -e "CDK synth:         ${YELLOW}npx cdk synth --context environment=dev${NC}"
echo -e "CDK diff:          ${YELLOW}npx cdk diff --context environment=dev${NC}"
echo ""
echo -e "${BLUE}💡 Tip: This script sets environment variables for your current shell session${NC}"
