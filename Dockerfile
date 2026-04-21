FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

# Health check: verify the main process (PID 1) is still running
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD test -f /proc/1/status || exit 1

CMD ["python", "openproject-mcp-fastmcp.py"]
