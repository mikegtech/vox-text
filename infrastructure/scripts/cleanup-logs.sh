#!/bin/bash

# CloudWatch Log Groups Cleanup Script
# Usage: ./scripts/cleanup-logs.sh [environment] [aws-profile]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
AWS_PROFILE=${2:-boss}

echo -e "${BLUE}🧹 CloudWatch Log Groups Cleanup${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "AWS Profile: ${GREEN}$AWS_PROFILE${NC}"
echo ""

# Set AWS profile
export AWS_PROFILE=$AWS_PROFILE

# Function to delete log group if it exists
delete_log_group_if_exists() {
    local log_group_name=$1
    
    if aws logs describe-log-groups --log-group-name-prefix "$log_group_name" --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$log_group_name"; then
        echo -e "${YELLOW}🗑️  Deleting log group: $log_group_name${NC}"
        aws logs delete-log-group --log-group-name "$log_group_name" || echo -e "${RED}❌ Failed to delete $log_group_name${NC}"
    else
        echo -e "${GREEN}✅ Log group doesn't exist: $log_group_name${NC}"
    fi
}

# List of log groups that might cause conflicts
LOG_GROUPS=(
    "/aws/lambda/smsbot-$ENVIRONMENT-messaging-sms-handler"
    "/aws/lambda/smsbot-$ENVIRONMENT-security-telnyx-authorizer"
    "/aws/sns/smsbot-$ENVIRONMENT-delivery-logs"
    "/aws/apigateway/smsbot-$ENVIRONMENT-telnyx-webhook"
)

echo -e "${YELLOW}🔍 Checking for existing log groups...${NC}"

for log_group in "${LOG_GROUPS[@]}"; do
    delete_log_group_if_exists "$log_group"
done

echo ""
echo -e "${GREEN}✅ Log group cleanup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "1. Run deployment: ${YELLOW}./deploy-with-boss.sh $ENVIRONMENT your-company${NC}"
echo -e "2. Monitor for any remaining log issues"
echo -e "3. Check CloudWatch console for new log groups"
