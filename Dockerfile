# --- Stage 1: Build nsjail ---
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for building nsjail
RUN apt-get update && apt-get install -y \
    autoconf \
    bison \
    flex \
    gcc \
    g++ \
    git \
    libprotobuf-dev \
    libnl-route-3-dev \
    libtool \
    make \
    pkg-config \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Clone and build nsjail
WORKDIR /src
RUN git clone https://github.com/google/nsjail.git
WORKDIR /src/nsjail
RUN make && mv nsjail /usr/bin/nsjail

# --- Stage 2: Final Runtime Image ---
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3, pip, and the Runtime libraries for nsjail
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libprotobuf-dev \
    libnl-route-3-200 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
# FIXED: Removed "--break-system-packages" which is not supported/needed on Ubuntu 22.04
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy nsjail binary from builder
COPY --from=builder /usr/bin/nsjail /usr/bin/nsjail

# Copy application code
COPY app.py .
COPY runner.py .

# Create a non-root user (used by nsjail)
RUN groupadd -g 99999 sanduser && \
    useradd -r -u 99999 -g sanduser sanduser

# Expose the required port
EXPOSE 8080

# Start command using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]