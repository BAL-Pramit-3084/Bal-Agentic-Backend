# =============================================================================
# BALASORE ALLOYS BAL-AGENTIC-BACKEND PLATFORM - PRODUCTION DOCKERFILE
# =============================================================================
# Version: 3.0.0 - Modular Architecture
# Optimized for: Dashboard Generator + Chatbot + Voice Plugins
# Deployment Target: Windows Server with Docker Engine
# =============================================================================

# =============================================================================
# STAGE 1: BUILDER (Install dependencies)
# =============================================================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Fix Debian mirror issues by using HTTPS and clearing cache
# The 403 errors are due to CDN issues with HTTP
RUN rm -rf /var/lib/apt/lists/* && \
    sed -i 's/http:/https:/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    pkg-config \
    libmariadb-dev-compat \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# STAGE 2: RUNTIME (Minimal production image)
# =============================================================================
FROM python:3.11-slim

# Set metadata
LABEL maintainer="BAL DevOps Team"
LABEL description="BAL-Agentic-Backend AI Platform - Dashboard Generator & Chatbot"
LABEL version="3.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Kolkata \
    PYTHONPATH=/app

# Fix Debian mirror issues and install runtime dependencies
# Using HTTPS to avoid 403 errors from CDN
RUN rm -rf /var/lib/apt/lists/* && \
    sed -i 's/http:/https:/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    ca-certificates \
    tzdata \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security (non-root)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUSERBASE=/home/appuser/.local

# Install Playwright browsers (chromium only for smaller image)
RUN python -m playwright install chromium

# Copy application code (respecting .dockerignore)
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p \
    /app/logs \
    /app/generated_dashboards \
    /app/config_modules/generated_dashboards \
    /app/config_modules/logs \
    /app/static/uploads \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5100

# Health check (uses Flask's /health endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5100/health || exit 1

# =============================================================================
# ENTRYPOINT & CMD
# =============================================================================
CMD ["python", "app_main.py"]
