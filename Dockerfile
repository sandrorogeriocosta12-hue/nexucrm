# Use Python 3.9 slim image for compatibility
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and constraints
COPY requirements.txt constraints.txt ./

# Install Python dependencies with constraints
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PORT=8000
ENV DEBUG=False
ENV PYDANTIC_SKIP_VALIDATION=1

# Run the main application with explicit uvicorn command
CMD uvicorn app_server:app --host 0.0.0.0 --port 8000