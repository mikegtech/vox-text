#!/bin/bash

# Build Cryptography Lambda Layer for Python 3.12
# This script creates a Lambda layer with the cryptography library

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Building Cryptography Lambda Layer for Python 3.12${NC}"
echo -e "${BLUE}====================================================${NC}"

# Create layer directory structure
LAYER_DIR="lambda-layers/cryptography"
mkdir -p $LAYER_DIR/python

echo -e "${YELLOW}📦 Installing cryptography library...${NC}"

# Install cryptography library for Python 3.12 (try different pip commands)
if command -v pip3.12 &> /dev/null; then
    pip3.12 install cryptography -t $LAYER_DIR/python/
elif command -v pip3 &> /dev/null; then
    pip3 install cryptography -t $LAYER_DIR/python/
elif command -v pip &> /dev/null; then
    pip install cryptography -t $LAYER_DIR/python/
else
    echo -e "${RED}❌ No pip command found. Please install pip first.${NC}"
    exit 1
fi

# Create requirements.txt for reference
cat > $LAYER_DIR/requirements.txt << EOF
cryptography>=41.0.0
EOF

echo -e "${YELLOW}📋 Creating layer info...${NC}"

# Create layer info file
cat > $LAYER_DIR/layer-info.json << EOF
{
  "name": "cryptography-python312",
  "description": "Cryptography library for Python 3.12 Lambda functions",
  "compatible_runtimes": ["python3.12"],
  "license": "Apache-2.0",
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "${YELLOW}🗜️  Creating layer zip file...${NC}"

# Create zip file for layer
cd $LAYER_DIR
zip -r ../cryptography-python312-layer.zip . -x "*.pyc" "*/__pycache__/*"
cd ../..

echo -e "${GREEN}✅ Cryptography layer built successfully!${NC}"
echo -e "${BLUE}📁 Layer file: lambda-layers/cryptography-python312-layer.zip${NC}"
echo -e "${BLUE}📋 Size: $(du -h lambda-layers/cryptography-python312-layer.zip | cut -f1)${NC}"

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo -e "1. Deploy the layer: ${YELLOW}aws lambda publish-layer-version --layer-name cryptography-python312 --zip-file fileb://lambda-layers/cryptography-python312-layer.zip --compatible-runtimes python3.12 --profile boss${NC}"
echo -e "2. Update CDK to use the layer"
echo -e "3. Deploy updated infrastructure"
