#!/bin/bash

# SMS Bot Infrastructure Deployment Script (Python CDK)
# Usage: ./deploy-python.sh <environment> <company> [tenant]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ Usage: $0 <environment> <company> [tenant]${NC}"
    echo -e "${YELLOW}   environment: dev, staging, or prod${NC}"
    echo -e "${YELLOW}   company: your company name${NC}"
    echo -e "${YELLOW}   tenant: optional tenant identifier${NC}"
    exit 1
fi

ENVIRONMENT=$1
COMPANY=$2
TENANT=${3:-""}

echo -e "${BLUE}🚀 SMS Bot Infrastructure Deployment${NC}"
echo -e "${BLUE}====================================${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Company: ${GREEN}$COMPANY${NC}"
echo -e "Tenant: ${GREEN}${TENANT:-"${ENVIRONMENT}-tenant"}${NC}"
echo ""

# Check if environment is set up
if [ -z "$AWS_PROFILE" ] || [ -z "$CDK_DEFAULT_ACCOUNT" ]; then
    echo -e "${YELLOW}⚠️  AWS environment not configured${NC}"
    echo -e "${YELLOW}🔧 Setting up AWS environment...${NC}"
    source ./scripts/setup-aws-env.sh
    echo ""
fi

# Validate environment
case $ENVIRONMENT in
    dev|staging|prod)
        echo -e "${GREEN}✅ Valid environment: $ENVIRONMENT${NC}"
        ;;
    *)
        echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
        echo -e "${YELLOW}   Supported: dev, staging, prod${NC}"
        exit 1
        ;;
esac

# Build deployment command
DEPLOY_CMD="./deploy.py $ENVIRONMENT $COMPANY"
if [ -n "$TENANT" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --tenant $TENANT"
fi

# Show diff first for production
if [ "$ENVIRONMENT" = "prod" ]; then
    echo -e "${YELLOW}🔍 Showing changes for production deployment...${NC}"
    DEPLOY_CMD="$DEPLOY_CMD --diff"
fi

echo -e "${BLUE}🔄 Running deployment command:${NC}"
echo -e "${YELLOW}$DEPLOY_CMD${NC}"
echo ""

# Execute deployment
eval $DEPLOY_CMD

echo ""
echo -e "${GREEN}🎉 Deployment script completed!${NC}"
