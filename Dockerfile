FROM python:3.12-slim

LABEL maintainer="platoba"
LABEL description="SEO Audit CLI - Comprehensive website SEO auditor"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./
COPY seo_audit.py ./
COPY audit/ ./audit/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[reports,dev]"

# Create output directory
RUN mkdir -p /app/output

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from audit.core import AuditEngine; print('OK')"

ENTRYPOINT ["python", "seo_audit.py"]
CMD ["--help"]
