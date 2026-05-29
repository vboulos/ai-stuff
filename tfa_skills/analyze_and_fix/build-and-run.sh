#!/bin/bash
# Build and run the Ollama-enabled RHEL9 container

set -e

IMAGE_NAME="rhel9-ollama-analyzer"
CONTAINER_NAME="test-analyzer"
MODEL="${1:-llama3.1}"

echo "=========================================="
echo "Building Docker Image"
echo "=========================================="
docker build -t ${IMAGE_NAME} .

echo ""
echo "=========================================="
echo "Starting Container"
echo "=========================================="
docker run -d \
  --name ${CONTAINER_NAME} \
  -v $(pwd):/app \
  -p 11434:11434 \
  ${IMAGE_NAME}

echo ""
echo "Waiting for container to be ready..."
sleep 5

echo ""
echo "=========================================="
echo "Pulling Ollama Model: ${MODEL}"
echo "=========================================="
docker exec ${CONTAINER_NAME} ollama pull ${MODEL}

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Container is running. You can now:"
echo ""
echo "  # Enter the container:"
echo "  docker exec -it ${CONTAINER_NAME} bash"
echo ""
echo "  # Run analysis directly:"
echo "  docker exec ${CONTAINER_NAME} python3 analyze_and_suggest_fixes.py test_failures.json --model ${MODEL}"
echo ""
echo "  # Create sample test file:"
echo "  docker exec ${CONTAINER_NAME} python3 analyze_and_suggest_fixes.py --sample"
echo ""
echo "  # Stop the container:"
echo "  docker stop ${CONTAINER_NAME}"
echo ""
echo "  # Remove the container:"
echo "  docker rm ${CONTAINER_NAME}"
echo ""
