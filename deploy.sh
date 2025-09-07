#!/bin/bash

# Survey Engine Railway Deployment Script
# This script builds and pushes the Docker image to Railway

set -e  # Exit on any error

echo "🚀 Starting Survey Engine deployment to Railway..."

# Build the Docker image for AMD64/Linux platform
echo "📦 Building Docker image for AMD64/Linux platform..."
docker buildx build --platform linux/amd64 -t chaitanyakc/survey-engine:latest --load .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

# Push the image to Docker Hub
echo "📤 Pushing image to Docker Hub..."
docker push chaitanyakc/survey-engine:latest

if [ $? -eq 0 ]; then
    echo "✅ Image pushed to Docker Hub successfully!"
    
    # Trigger Railway redeploy
    echo "🔄 Triggering Railway redeploy..."
    if railway redeploy -y; then
        echo "✅ Railway redeploy triggered successfully."
    else
        echo "❌ Railway redeploy failed."
        exit 1
    fi
    
    echo ""
    echo "🎉 Deployment complete!"
    echo "📋 Next steps:"
    echo "   1. Railway is redeploying your service with the latest image"
    echo "   2. Your app will be available at: https://survey-engine-production.up.railway.app"
    echo ""
    echo "🔍 To check logs:"
    echo "   - Use Railway dashboard logs tab"
    echo "   - Or run: railway logs"
else
    echo "❌ Docker push failed!"
    exit 1
fi
