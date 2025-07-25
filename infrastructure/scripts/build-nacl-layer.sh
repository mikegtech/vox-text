#!/bin/bash

# Build PyNaCl Lambda Layer for Python 3.12
# This script creates a Lambda layer with the PyNaCl library (official Telnyx dependency)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Building PyNaCl Lambda Layer for Python 3.12${NC}"
echo -e "${BLUE}=============================================${NC}"
echo -e "${YELLOW}This matches the official Telnyx Python SDK dependency${NC}"

# Create layer directory structure
LAYER_DIR="lambda-layers/pynacl"
mkdir -p $LAYER_DIR/python

echo -e "${YELLOW}📦 Installing PyNaCl library...${NC}"

# Install PyNaCl library for Python 3.12 (try different pip commands)
if command -v pip3.12 &> /dev/null; then
    pip3.12 install PyNaCl -t $LAYER_DIR/python/
elif command -v pip3 &> /dev/null; then
    pip3 install PyNaCl -t $LAYER_DIR/python/
elif command -v pip &> /dev/null; then
    pip install PyNaCl -t $LAYER_DIR/python/
else
    echo -e "${RED}❌ No pip command found. Using Docker method...${NC}"
    
    # Use Docker to install PyNaCl (most reliable method)
    echo -e "${YELLOW}🐳 Using Docker to install PyNaCl...${NC}"
    docker run --rm -v $(pwd)/$LAYER_DIR/python:/var/task python:3.12-slim \
        pip install PyNaCl -t /var/task
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Docker installation failed. Please install pip or Docker.${NC}"
        exit 1
    fi
fi

# Create requirements.txt for reference
cat > $LAYER_DIR/requirements.txt << EOF
PyNaCl>=1.5.0
EOF

echo -e "${YELLOW}📋 Creating layer info...${NC}"

# Create layer info file
cat > $LAYER_DIR/layer-info.json << EOF
{
  "name": "pynacl-python312",
  "description": "PyNaCl library for Python 3.12 Lambda functions (official Telnyx SDK dependency)",
  "compatible_runtimes": ["python3.12"],
  "license": "Apache-2.0",
  "official_telnyx_dependency": true,
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo -e "${YELLOW}🗜️  Creating layer zip file...${NC}"

# Create zip file for layer
cd $LAYER_DIR
zip -r ../pynacl-python312-layer.zip . -x "*.pyc" "*/__pycache__/*"
cd ../..

echo -e "${GREEN}✅ PyNaCl layer built successfully!${NC}"
echo -e "${BLUE}📁 Layer file: lambda-layers/pynacl-python312-layer.zip${NC}"
echo -e "${BLUE}📋 Size: $(du -h lambda-layers/pynacl-python312-layer.zip | cut -f1)${NC}"

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo -e "1. Deploy the layer: ${YELLOW}aws lambda publish-layer-version --layer-name pynacl-python312 --zip-file fileb://lambda-layers/pynacl-python312-layer.zip --compatible-runtimes python3.12 --profile boss${NC}"
echo -e "2. Update CDK to use the layer"
echo -e "3. Deploy updated infrastructure"
echo ""
echo -e "${GREEN}🎯 This layer provides the exact same PyNaCl library used by the official Telnyx Python SDK!${NC}"
