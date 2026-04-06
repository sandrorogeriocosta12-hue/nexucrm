# Railway-specific Dockerfile
# Force rebuild: 2024-01-15
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Railway expects the app to listen on $PORT
ENV PORT=8080
EXPOSE $PORT

# Start command
CMD uvicorn app_server:app --host 0.0.0.0 --port $PORT