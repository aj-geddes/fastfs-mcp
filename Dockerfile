FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install essential filesystem tools and build dependencies
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
    pkg-config \
    libssl-dev \
    libffi-dev \
    cmake \
    libssh2-1-dev \
    build-essential \
    ca-certificates \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install compatible libgit2 version (1.7.x)
RUN wget https://github.com/libgit2/libgit2/archive/refs/tags/v1.7.2.tar.gz && \
    tar xzf v1.7.2.tar.gz && \
    cd libgit2-1.7.2 && \
    mkdir build && \
    cd build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/usr && \
    make && \
    make install && \
    cd ../../ && \
    rm -rf libgit2-1.7.2 v1.7.2.tar.gz

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
