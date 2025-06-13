#!/bin/bash
# Build and run the PyGit2 implementation for FastFS-MCP

set -e  # Exit on error

# Constants
IMAGE_NAME="fastfs-mcp-pygit2"
DOCKER_FILE="Dockerfile.pygit2.enhanced"

# Print section header
section() {
    echo -e "\n\033[1;34m===> $1\033[0m"
}

section "Building Docker image for PyGit2 implementation"
docker build -t ${IMAGE_NAME} -f ${DOCKER_FILE} .

section "Running tests"
echo "To run tests, execute the following command:"
echo "docker run --rm -v \$(pwd):/mnt/workspace ${IMAGE_NAME} python /app/test_advanced_pygit2.py"

section "Running the server"
echo "To run the server, execute the following command:"
echo "docker run -i --rm -v \$(pwd):/mnt/workspace ${IMAGE_NAME}"

section "Build completed successfully!"
echo "Image name: ${IMAGE_NAME}"
echo "You can now use the PyGit2 implementation for FastFS-MCP."
