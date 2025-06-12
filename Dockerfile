FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install essential filesystem tools and Git
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
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create workspace directory for mounting local filesystem
RUN mkdir -p /mnt/workspace

# Set up application
WORKDIR /app
COPY server.py /app/server.py
COPY git_tools.py /app/git_tools.py
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make server.py executable
RUN chmod +x /app/server.py

# Set working directory to the mounted workspace path
WORKDIR /mnt/workspace

# Run the server
ENTRYPOINT ["python", "/app/server.py"]
