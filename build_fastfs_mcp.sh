#!/bin/bash
# Build and run the FastFS-MCP with PyGit2 implementation

set -e  # Exit on error

# Constants
IMAGE_NAME="fastfs-mcp"
DOCKER_FILE="Dockerfile"

# Print section header
section() {
    echo -e "\n\033[1;34m===> $1\033[0m"
}

section "Building Docker image for FastFS-MCP with PyGit2"
docker build -t ${IMAGE_NAME} -f ${DOCKER_FILE} .

section "Testing package structure"
echo "Testing if the package structure is valid..."
docker run --rm ${IMAGE_NAME} python /app/tests/test_package.py || {
    echo -e "\n\033[1;31m===> Package structure test failed!\033[0m"
    exit 1
}

section "Running tests"
echo "To run the full test suite, execute the following command:"
echo "docker run --rm -v \$(pwd):/mnt/workspace ${IMAGE_NAME} python -m unittest discover tests"

section "Running the server"
echo "To run the server, execute the following command:"
echo "docker run -i --rm -v \$(pwd):/mnt/workspace ${IMAGE_NAME}"

section "Build completed successfully!"
echo "Image name: ${IMAGE_NAME}"
echo "You can now use FastFS-MCP with PyGit2."
