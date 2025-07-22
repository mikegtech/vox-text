#!/bin/bash

# Quick deployment script using the 'boss' AWS SSO profile
# Usage: ./deploy-with-boss.sh [environment] [company] [tenant]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 SMS Bot Deployment with 'boss' profile${NC}"
echo -e "${BLUE}=========================================${NC}"

# Default values
ENVIRONMENT=${1:-dev}
COMPANY=${2:-your-company}
TENANT=${3:-}

echo -e "Using AWS profile: ${GREEN}boss${NC}"
echo ""

# Call the main deployment script with boss profile
./scripts/deploy.sh "$ENVIRONMENT" "$COMPANY" "$TENANT" "boss"
