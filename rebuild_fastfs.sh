#!/bin/bash
# FastFS-MCP with PyGit2 build and run script
# This unified script handles building, testing, and running the FastFS-MCP server

set -e  # Exit on error

# Constants
IMAGE_NAME="fastfs-mcp"
DOCKER_FILE="Dockerfile"
WORKSPACE_DIR="/mnt/workspace"

# Command line argument parsing
ACTION="build"
MOUNT_PATH=$(pwd)
RUN_TESTS=false
GITHUB_TOKEN=""
DEBUG=false

# Print section header
section() {
    echo -e "\n\033[1;34m===> $1\033[0m"
}

# Print usage info
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                Show this help message"
    echo "  -r, --run                 Run the server after building"
    echo "  -t, --test                Run tests after building"
    echo "  -m, --mount PATH          Mount path (default: current directory)"
    echo "  -g, --github-token TOKEN  GitHub Personal Access Token for authentication"
    echo "  -d, --debug               Enable debug logging"
    echo ""
    echo "Examples:"
    echo "  $0                       # Build only"
    echo "  $0 -r                    # Build and run"
    echo "  $0 -t                    # Build and test"
    echo "  $0 -r -m ~/projects      # Build and run with custom mount path"
    echo "  $0 -r -g ghp_token123    # Build and run with GitHub authentication"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -r|--run)
            ACTION="run"
            shift
            ;;
        -t|--test)
            RUN_TESTS=true
            shift
            ;;
        -m|--mount)
            MOUNT_PATH="$2"
            shift 2
            ;;
        -g|--github-token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Build the Docker image
build_image() {
    section "Building Docker image for FastFS-MCP with PyGit2"
    echo "This build process includes compiling libgit2 v1.7.2 from source and may take a few minutes..."
    docker build -t ${IMAGE_NAME} -f ${DOCKER_FILE} .
}

# Run package structure tests
test_package_structure() {
    section "Testing package structure"
    echo "Testing if the package structure is valid..."
    docker run --rm ${IMAGE_NAME} python -c "import fastfs_mcp; print('Package structure is valid')" || {
        echo -e "\n\033[1;31m===> Package structure test failed!\033[0m"
        exit 1
    }
}

# Run full test suite
run_tests() {
    section "Running tests"
    echo "Running the full test suite..."
    docker run --rm -v "${MOUNT_PATH}:${WORKSPACE_DIR}" ${IMAGE_NAME} python -m unittest discover tests
}

# Run the server
run_server() {
    section "Running the server"
    echo "Starting FastFS-MCP server..."
    
    # Build the docker run command
    DOCKER_CMD="docker run -i --rm"
    
    # Add volume mount
    DOCKER_CMD+=" -v \"${MOUNT_PATH}:${WORKSPACE_DIR}\""
    
    # Add GitHub token if provided
    if [ -n "$GITHUB_TOKEN" ]; then
        DOCKER_CMD+=" -e GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_TOKEN}"
    fi
    
    # Add debug flag if enabled
    if [ "$DEBUG" = true ]; then
        DOCKER_CMD+=" -e FASTFS_DEBUG=true"
    fi
    
    # Add image name
    DOCKER_CMD+=" ${IMAGE_NAME}"
    
    # Run the command
    echo "Executing: $DOCKER_CMD"
    eval $DOCKER_CMD
}

# Main execution
build_image
test_package_structure

if [ "$RUN_TESTS" = true ]; then
    run_tests
fi

if [ "$ACTION" = "run" ]; then
    run_server
else
    section "Build completed successfully!"
    echo "Image name: ${IMAGE_NAME}"
    echo "To run the server: $0 --run"
    echo "To run with custom mount path: $0 --run --mount /path/to/directory"
    echo "To run with GitHub authentication: $0 --run --github-token YOUR_TOKEN"
fi
