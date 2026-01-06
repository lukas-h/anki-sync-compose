FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make server.py executable
RUN chmod +x server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for HTTP/SSE (if needed in future)
EXPOSE 8080

# Run the MCP server
CMD ["python", "server.py"]
