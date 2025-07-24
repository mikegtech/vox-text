#!/bin/bash

# SMS Bot Infrastructure Deployment with Custom Domain
# Usage: ./scripts/deploy-with-custom-domain.sh [environment] [company] [domain-name] [certificate-arn] [aws-profile]

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
DOMAIN_NAME=${3}
CERTIFICATE_ARN=${4}
AWS_PROFILE=${5:-boss}

# Validate required parameters
if [ -z "$DOMAIN_NAME" ] || [ -z "$CERTIFICATE_ARN" ]; then
    echo -e "${RED}❌ Missing required parameters${NC}"
    echo -e "${YELLOW}Usage: $0 [environment] [company] [domain-name] [certificate-arn] [aws-profile]${NC}"
    echo -e "${YELLOW}Example: $0 dev acme-corp sms-api.example.com arn:aws:acm:us-east-1:123456789012:certificate/abc123 boss${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 SMS Bot Infrastructure Deployment with Custom Domain${NC}"
echo -e "${BLUE}====================================================${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Company: ${GREEN}$COMPANY${NC}"
echo -e "Custom Domain: ${GREEN}$DOMAIN_NAME${NC}"
echo -e "Certificate ARN: ${GREEN}$CERTIFICATE_ARN${NC}"
echo -e "AWS Profile: ${GREEN}$AWS_PROFILE${NC}"
echo ""

# Set AWS profile environment variable
export AWS_PROFILE=$AWS_PROFILE

# Validate certificate exists
echo -e "${YELLOW}🔍 Validating SSL certificate...${NC}"
if ! aws acm describe-certificate --certificate-arn "$CERTIFICATE_ARN" > /dev/null 2>&1; then
    echo -e "${RED}❌ Certificate not found: $CERTIFICATE_ARN${NC}"
    echo -e "${YELLOW}Please ensure the certificate exists and is in the correct region${NC}"
    exit 1
fi

# Check certificate status
CERT_STATUS=$(aws acm describe-certificate --certificate-arn "$CERTIFICATE_ARN" --query 'Certificate.Status' --output text)
if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo -e "${YELLOW}⚠️  Certificate status: $CERT_STATUS${NC}"
    echo -e "${YELLOW}Certificate must be ISSUED before deployment${NC}"
    if [ "$CERT_STATUS" = "PENDING_VALIDATION" ]; then
        echo -e "${YELLOW}Please complete DNS validation for the certificate${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Certificate validated successfully${NC}"

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
fi

# Build TypeScript
echo -e "${YELLOW}🔨 Building TypeScript...${NC}"
npm run build

# Deploy with custom domain context
echo -e "${YELLOW}🚀 Deploying infrastructure with custom domain...${NC}"
npx cdk deploy \
    --profile $AWS_PROFILE \
    --context environment=$ENVIRONMENT \
    --context company=$COMPANY \
    --context customDomainName=$DOMAIN_NAME \
    --context certificateArn=$CERTIFICATE_ARN \
    --require-approval never \
    --outputs-file outputs-$ENVIRONMENT-$AWS_PROFILE-custom-domain.json

# Check deployment status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    
    # Display outputs
    if [ -f "outputs-$ENVIRONMENT-$AWS_PROFILE-custom-domain.json" ]; then
        echo -e "${BLUE}📋 Stack Outputs:${NC}"
        cat outputs-$ENVIRONMENT-$AWS_PROFILE-custom-domain.json | jq -r 'to_entries[] | "\(.key): \(.value)"' 2>/dev/null || cat outputs-$ENVIRONMENT-$AWS_PROFILE-custom-domain.json
        echo ""
    fi
    
    # Get DNS configuration info
    echo -e "${BLUE}🌐 DNS Configuration Required:${NC}"
    DOMAIN_TARGET=$(aws cloudformation describe-stacks \
        --stack-name smsbot-$ENVIRONMENT-infrastructure \
        --query 'Stacks[0].Outputs[?OutputKey==`DomainNameTarget`].OutputValue' \
        --output text \
        --profile $AWS_PROFILE)
    
    if [ -n "$DOMAIN_TARGET" ] && [ "$DOMAIN_TARGET" != "None" ]; then
        echo -e "Create a CNAME record:"
        echo -e "${YELLOW}Name: $DOMAIN_NAME${NC}"
        echo -e "${YELLOW}Type: CNAME${NC}"
        echo -e "${YELLOW}Value: $DOMAIN_TARGET${NC}"
        echo ""
    fi
    
    # Display next steps
    echo -e "${BLUE}🎯 Next Steps:${NC}"
    echo -e "1. Create DNS CNAME record (shown above)"
    echo -e "2. Wait for DNS propagation (5-10 minutes)"
    echo -e "3. Test custom domain: ${YELLOW}curl https://$DOMAIN_NAME/health${NC}"
    echo -e "4. Configure Telnyx webhook URL: ${YELLOW}https://$DOMAIN_NAME/webhook/sms${NC}"
    echo -e "5. Add Telnyx public key to Secrets Manager"
    
else
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi
