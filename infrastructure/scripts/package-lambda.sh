#!/bin/bash

# Package Lambda functions with dependencies using uv
# Usage: ./scripts/package-lambda.sh [function-name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

FUNCTION_NAME=${1}

if [ -z "$FUNCTION_NAME" ]; then
    echo -e "${RED}❌ Function name required${NC}"
    echo -e "${YELLOW}Usage: $0 [function-name]${NC}"
    echo -e "${YELLOW}Available functions: telnyx-authorizer, telnyx-fallback${NC}"
    exit 1
fi

LAMBDA_DIR="lambda/$FUNCTION_NAME"
PACKAGE_DIR="lambda-packages/$FUNCTION_NAME"

if [ ! -d "$LAMBDA_DIR" ]; then
    echo -e "${RED}❌ Lambda function directory not found: $LAMBDA_DIR${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Packaging Lambda function: $FUNCTION_NAME${NC}"
echo -e "${BLUE}============================================${NC}"

# Clean up previous package
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

echo -e "${YELLOW}🔧 Installing dependencies with uv...${NC}"

# Change to Lambda function directory
cd "$LAMBDA_DIR"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Install dependencies to package directory
echo -e "${YELLOW}📥 Installing Python dependencies...${NC}"

# Use requirements.txt if available, otherwise extract from pyproject.toml
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}Using requirements.txt${NC}"
    uv pip install --python python3.12 --target "../../$PACKAGE_DIR" -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    echo -e "${BLUE}Extracting dependencies from pyproject.toml${NC}"
    # Simple grep-based extraction for common dependency format
    grep -A 20 "dependencies = \[" pyproject.toml | grep '".*"' | sed 's/.*"\(.*\)".*/\1/' > temp_requirements.txt
    uv pip install --python python3.12 --target "../../$PACKAGE_DIR" -r temp_requirements.txt
    rm temp_requirements.txt
else
    echo -e "${RED}❌ No requirements.txt or pyproject.toml found${NC}"
    exit 1
fi

# Copy Lambda function code
echo -e "${YELLOW}📋 Copying Lambda function code...${NC}"
cp *.py "../../$PACKAGE_DIR/"

# Copy any additional files
if [ -f "requirements.txt" ]; then
    cp requirements.txt "../../$PACKAGE_DIR/"
fi

cd ../..

echo -e "${YELLOW}🗜️  Creating deployment package...${NC}"

# Create zip file for deployment
cd "$PACKAGE_DIR"
zip -r "../${FUNCTION_NAME}-deployment.zip" . -x "*.pyc" "*/__pycache__/*" "*.dist-info/*"
cd ../..

# Get package size
PACKAGE_SIZE=$(du -h "lambda-packages/${FUNCTION_NAME}-deployment.zip" | cut -f1)

echo -e "${GREEN}✅ Lambda function packaged successfully!${NC}"
echo -e "${BLUE}📁 Package: lambda-packages/${FUNCTION_NAME}-deployment.zip${NC}"
echo -e "${BLUE}📋 Size: $PACKAGE_SIZE${NC}"

# List dependencies
echo -e "${BLUE}📦 Installed dependencies:${NC}"
ls -la "$PACKAGE_DIR" | grep -E "^d" | awk '{print "  - " $9}' | grep -v "^\.$\|^\.\.$"

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo -e "1. Update CDK to use packaged deployment"
echo -e "2. Deploy updated infrastructure"
echo -e "3. Test Lambda function with dependencies"
