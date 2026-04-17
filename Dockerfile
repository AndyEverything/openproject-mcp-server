FROM python:3.11-slim
WORKDIR /app
RUN python -m venv .venv
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "openproject-mcp-fastmcp.py"]