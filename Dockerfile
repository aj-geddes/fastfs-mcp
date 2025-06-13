FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install essential filesystem tools, Git and dependencies for PyGit2
RUN apt-get update && apt-get install -y \
    ripgrep \
    grep \
    jq \
    sed \
    gawk \
    fd-find \
    tree \
    coreutils \
    zip \
    unzip \
    gzip \
    xz-utils \
    git \
    libgit2-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    cmake \
    libssh2-1-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create workspace directory for mounting local filesystem
RUN mkdir -p /mnt/workspace

# Set up application
WORKDIR /app

# Copy package files
COPY fastfs_mcp /app/fastfs_mcp
COPY tests /app/tests
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make server executable
RUN chmod +x /app/fastfs_mcp/server.py

# Set working directory to the mounted workspace path
WORKDIR /mnt/workspace

# Run the server
ENTRYPOINT ["python", "-m", "fastfs_mcp.server"]
