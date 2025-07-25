#!/bin/bash

# Manual Lambda deployment with dependency installation
# Usage: ./scripts/manual-lambda-deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Manual Lambda Deployment with Dependencies${NC}"
echo -e "${BLUE}=============================================${NC}"

# Create temp directory for packaging
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Using temp directory: $TEMP_DIR${NC}"

# Package authorizer function
echo -e "${YELLOW}📦 Packaging authorizer function...${NC}"
AUTHORIZER_DIR="$TEMP_DIR/authorizer"
mkdir -p "$AUTHORIZER_DIR"

# Copy authorizer code
cp lambda/telnyx-authorizer/index.py "$AUTHORIZER_DIR/"

# Install dependencies using pip
echo -e "${YELLOW}Installing PyNaCl and dependencies...${NC}"
pip3 install PyNaCl boto3 botocore -t "$AUTHORIZER_DIR" --upgrade

# Create zip file
cd "$AUTHORIZER_DIR"
zip -r ../authorizer.zip . -x "*.pyc" "*/__pycache__/*"
cd - > /dev/null

# Update Lambda function
echo -e "${YELLOW}Updating authorizer Lambda function...${NC}"
aws lambda update-function-code \
  --function-name smsbot-dev-security-telnyx-authorizer \
  --zip-file fileb://$TEMP_DIR/authorizer.zip \
  --profile boss

# Package fallback function
echo -e "${YELLOW}📦 Packaging fallback function...${NC}"
FALLBACK_DIR="$TEMP_DIR/fallback"
mkdir -p "$FALLBACK_DIR"

# Copy fallback code
cp lambda/telnyx-fallback/index.py "$FALLBACK_DIR/"

# Install dependencies
echo -e "${YELLOW}Installing boto3 dependencies...${NC}"
pip3 install boto3 botocore -t "$FALLBACK_DIR" --upgrade

# Create zip file
cd "$FALLBACK_DIR"
zip -r ../fallback.zip . -x "*.pyc" "*/__pycache__/*"
cd - > /dev/null

# Update Lambda function
echo -e "${YELLOW}Updating fallback Lambda function...${NC}"
aws lambda update-function-code \
  --function-name smsbot-dev-messaging-telnyx-fallback \
  --zip-file fileb://$TEMP_DIR/fallback.zip \
  --profile boss

# Clean up
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✅ Manual Lambda deployment completed!${NC}"
echo ""
echo -e "${BLUE}🧪 Test the functions:${NC}"
echo -e "aws lambda invoke --function-name smsbot-dev-security-telnyx-authorizer --payload '{\"test\":\"data\"}' response.json --profile boss"
echo ""
echo -e "${BLUE}📊 Monitor logs:${NC}"
echo -e "aws logs tail /aws/lambda/smsbot-dev-security-telnyx-authorizer --follow --profile boss"
