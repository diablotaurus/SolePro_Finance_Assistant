# Dockerfile for SolePro Finance Assistant

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create non-root user
RUN groupadd -r solepro && useradd -r -g solepro solepro

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/exports /app/backups \
    && chown -R solepro:solepro /app

# Copy application code
COPY . .

# Switch to non-root user
USER solepro

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose port (for future web interface)
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "-m", "solepro.presentation.telegram.bot"]
