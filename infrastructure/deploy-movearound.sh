#!/bin/bash

# SMS Bot Infrastructure Deployment for api.movearound.co
# Usage: ./deploy-movearound.sh [certificate-arn]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CERTIFICATE_ARN=${1}

if [ -z "$CERTIFICATE_ARN" ]; then
    echo -e "${RED}❌ Certificate ARN required${NC}"
    echo -e "${YELLOW}Usage: $0 [certificate-arn]${NC}"
    echo -e "${YELLOW}Example: $0 arn:aws:acm:us-east-1:123456789012:certificate/abc123${NC}"
    echo ""
    echo -e "${BLUE}📋 To get your certificate ARN:${NC}"
    echo -e "1. Request certificate: ${YELLOW}aws acm request-certificate --domain-name api.movearound.co --validation-method DNS --profile boss${NC}"
    echo -e "2. Validate in AWS Console"
    echo -e "3. Get ARN: ${YELLOW}aws acm list-certificates --profile boss${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Deploying SMS Bot for api.movearound.co${NC}"
echo -e "${BLUE}=======================================${NC}"
echo -e "Domain: ${GREEN}api.movearound.co${NC}"
echo -e "Webhook URL: ${GREEN}https://api.movearound.co/dev/webhooks/telnyx/sms${NC}"
echo -e "Certificate: ${GREEN}$CERTIFICATE_ARN${NC}"
echo ""

# Deploy with movearound.co configuration
./scripts/deploy-with-custom-domain.sh \
  dev \
  movearound \
  "api.movearound.co" \
  "$CERTIFICATE_ARN" \
  boss

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "1. Create DNS CNAME record (see output above)"
echo -e "2. Test health: ${YELLOW}curl https://api.movearound.co/health${NC}"
echo -e "3. Configure Telnyx webhook: ${YELLOW}https://api.movearound.co/dev/webhooks/telnyx/sms${NC}"
echo -e "4. Add Telnyx public key to Secrets Manager"
