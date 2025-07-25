#!/bin/bash

# SMS Bot Infrastructure Deployment with Proper Lambda Packaging
# Usage: ./deploy-with-packaging.sh [environment] [company] [domain-name] [certificate-arn] [aws-profile]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
COMPANY=${2:-movearound}
DOMAIN_NAME=${3:-api.movearound.co}
CERTIFICATE_ARN=${4:-arn:aws:acm:us-east-1:099427795947:certificate/8db7a123-5b4b-4090-83b5-37aed328f3b7}
AWS_PROFILE=${5:-boss}

echo -e "${BLUE}🚀 SMS Bot Infrastructure Deployment with Lambda Packaging${NC}"
echo -e "${BLUE}=========================================================${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Company: ${GREEN}$COMPANY${NC}"
echo -e "Custom Domain: ${GREEN}$DOMAIN_NAME${NC}"
echo -e "Certificate ARN: ${GREEN}$CERTIFICATE_ARN${NC}"
echo -e "AWS Profile: ${GREEN}$AWS_PROFILE${NC}"
echo ""

# Set AWS profile environment variable
export AWS_PROFILE=$AWS_PROFILE

# Step 1: Install uv if not available
echo -e "${YELLOW}🔧 Checking uv installation...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}📥 Installing uv package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo -e "${GREEN}✅ uv is available${NC}"

# Step 2: Package Lambda functions
echo -e "${YELLOW}📦 Packaging Lambda functions with dependencies...${NC}"

# Package authorizer function
echo -e "${BLUE}📦 Packaging telnyx-authorizer...${NC}"
./scripts/package-lambda.sh telnyx-authorizer

# Package SMS handler function
echo -e "${BLUE}📦 Packaging sms-handler...${NC}"
./scripts/package-lambda.sh sms-handler

# Package fallback function
echo -e "${BLUE}📦 Packaging telnyx-fallback...${NC}"
./scripts/package-lambda.sh telnyx-fallback

echo -e "${GREEN}✅ All Lambda functions packaged successfully${NC}"

# Step 3: Install CDK dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing CDK dependencies...${NC}"
    npm install
fi

# Step 4: Build TypeScript
echo -e "${YELLOW}🔨 Building TypeScript...${NC}"
npm run build

# Step 5: Validate certificate
echo -e "${YELLOW}🔍 Validating SSL certificate...${NC}"
if ! aws acm describe-certificate --certificate-arn "$CERTIFICATE_ARN" > /dev/null 2>&1; then
    echo -e "${RED}❌ Certificate not found: $CERTIFICATE_ARN${NC}"
    echo -e "${YELLOW}Please ensure the certificate exists and is in the correct region${NC}"
    exit 1
fi

CERT_STATUS=$(aws acm describe-certificate --certificate-arn "$CERTIFICATE_ARN" --query 'Certificate.Status' --output text)
if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo -e "${YELLOW}⚠️  Certificate status: $CERT_STATUS${NC}"
    if [ "$CERT_STATUS" = "PENDING_VALIDATION" ]; then
        echo -e "${YELLOW}Please complete DNS validation for the certificate${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Certificate validated successfully${NC}"

# Step 6: Deploy with packaged Lambda functions
echo -e "${YELLOW}🚀 Deploying infrastructure with packaged Lambda functions...${NC}"
npx cdk deploy \
    --profile $AWS_PROFILE \
    --context environment=$ENVIRONMENT \
    --context company=$COMPANY \
    --context customDomainName=$DOMAIN_NAME \
    --context certificateArn=$CERTIFICATE_ARN \
    --require-approval never \
    --outputs-file outputs-$ENVIRONMENT-$AWS_PROFILE-packaged.json

# Check deployment status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    
    # Display outputs
    if [ -f "outputs-$ENVIRONMENT-$AWS_PROFILE-packaged.json" ]; then
        echo -e "${BLUE}📋 Stack Outputs:${NC}"
        cat outputs-$ENVIRONMENT-$AWS_PROFILE-packaged.json | jq -r 'to_entries[] | "\(.key): \(.value)"' 2>/dev/null || cat outputs-$ENVIRONMENT-$AWS_PROFILE-packaged.json
        echo ""
    fi
    
    # Display package information
    echo -e "${BLUE}📦 Lambda Package Information:${NC}"
    if [ -f "lambda-packages/telnyx-authorizer-deployment.zip" ]; then
        AUTHORIZER_SIZE=$(du -h lambda-packages/telnyx-authorizer-deployment.zip | cut -f1)
        echo -e "  - Authorizer: ${GREEN}$AUTHORIZER_SIZE${NC}"
    fi
    if [ -f "lambda-packages/sms-handler-deployment.zip" ]; then
        SMS_HANDLER_SIZE=$(du -h lambda-packages/sms-handler-deployment.zip | cut -f1)
        echo -e "  - SMS Handler: ${GREEN}$SMS_HANDLER_SIZE${NC}"
    fi
    if [ -f "lambda-packages/telnyx-fallback-deployment.zip" ]; then
        FALLBACK_SIZE=$(du -h lambda-packages/telnyx-fallback-deployment.zip | cut -f1)
        echo -e "  - Fallback: ${GREEN}$FALLBACK_SIZE${NC}"
    fi
    
    # Display next steps
    echo ""
    echo -e "${BLUE}🎯 Next Steps:${NC}"
    echo -e "1. Add Telnyx public key to Secrets Manager"
    echo -e "2. Configure Telnyx webhook URL: ${YELLOW}https://$DOMAIN_NAME/dev/webhooks/telnyx/sms${NC}"
    echo -e "3. Test webhook with real SMS messages"
    echo -e "4. Monitor logs: ${YELLOW}aws logs tail /aws/lambda/smsbot-$ENVIRONMENT-security-telnyx-authorizer --follow --profile $AWS_PROFILE${NC}"
    
    echo ""
    echo -e "${GREEN}🎉 Your SMS Bot is now deployed with proper dependency management!${NC}"
    echo -e "${BLUE}📋 Dependencies included: PyNaCl, boto3, botocore${NC}"
    
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi
