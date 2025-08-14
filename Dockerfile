# Hendrix Video Analysis Pipeline - Docker Image
# Multi-stage build for optimized final image

# Build stage
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir .

# Production stage  
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash hendrix

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY hendrix/ ./hendrix/
COPY configs/ ./configs/

# Create directories for data
RUN mkdir -p /app/data /app/outputs && chown -R hendrix:hendrix /app

# Switch to non-root user
USER hendrix

# Set environment variables
ENV PYTHONPATH=/app
ENV HENDRIX_CACHE_DIR=/app/.cache

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import hendrix; print('OK')" || exit 1

# Default command
ENTRYPOINT ["hendrix"]
CMD ["--help"]