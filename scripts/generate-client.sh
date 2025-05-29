#!/bin/bash

# Script to generate the frontend TypeScript client from the FastAPI OpenAPI schema

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Generating Frontend TypeScript Client${NC}"

# Check if backend is running
echo -e "${YELLOW}📡 Checking if backend is running...${NC}"
if curl -f -s http://localhost:8000/api/v1/openapi.json > /dev/null; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is not running. Please start the backend with: docker compose up backend${NC}"
    exit 1
fi

# Download OpenAPI schema
echo -e "${YELLOW}📥 Downloading OpenAPI schema...${NC}"
cd "$(dirname "$0")/.."  # Go to project root
curl -o frontend/openapi.json http://localhost:8000/api/v1/openapi.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ OpenAPI schema downloaded successfully${NC}"
else
    echo -e "${RED}❌ Failed to download OpenAPI schema${NC}"
    exit 1
fi

# Generate TypeScript client
echo -e "${YELLOW}🔨 Generating TypeScript client...${NC}"
cd frontend
npm run generate-client

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TypeScript client generated successfully${NC}"
    echo -e "${BLUE}📁 Client location: frontend/src/client${NC}"
    echo -e "${YELLOW}💡 Remember to commit the changes to version control${NC}"
else
    echo -e "${RED}❌ Failed to generate TypeScript client${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 All done!${NC}"
