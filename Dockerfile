# Hendrix Video Analysis Pipeline - Docker Image
# Multi-stage build for optimized final image

# Build stage
FROM python:3.11.10-slim as builder

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg=7:5.1.6-0+deb12u1 \
    git=1:2.39.2-1.1 \
    build-essential=12.9 \
    ca-certificates=20230311 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies with security verification
RUN pip install --no-cache-dir --upgrade pip==24.3.1 setuptools==75.6.0 wheel==0.45.1
RUN pip install --no-cache-dir --verify-pep508 .

# Production stage  
FROM python:3.11.10-slim

# Install runtime dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg=7:5.1.6-0+deb12u1 \
    ca-certificates=20230311 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with specific UID/GID for security
RUN groupadd --gid 10001 hendrix && \
    useradd --uid 10001 --gid hendrix --create-home --shell /bin/bash hendrix

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code with proper ownership
COPY --chown=hendrix:hendrix hendrix/ ./hendrix/
COPY --chown=hendrix:hendrix configs/ ./configs/

# Create directories for data with secure permissions
RUN mkdir -p /app/data /app/outputs /app/.cache && \
    chown -R hendrix:hendrix /app && \
    chmod -R 750 /app

# Switch to non-root user
USER hendrix

# Set secure environment variables
ENV PYTHONPATH=/app
ENV HENDRIX_CACHE_DIR=/app/.cache
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

# Add security labels
LABEL maintainer="Material Lab <info@material-lab.io>" \
      version="3.0.0" \
      description="Hendrix Video Analysis Pipeline" \
      security.scan="true" \
      org.opencontainers.image.source="https://github.com/material-lab-io/HendrixVideo"

# Health check with security timeout
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=2 \
    CMD python -c "import sys; import hendrix; sys.exit(0)" || exit 1

# Default command
ENTRYPOINT ["hendrix"]
CMD ["--help"]