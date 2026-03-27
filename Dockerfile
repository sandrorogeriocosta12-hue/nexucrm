# Railway-specific Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

# Copy app code
COPY . .

# Railway expects the app to listen on $PORT
ENV PORT=8000
EXPOSE $PORT

# Start command
CMD ["uvicorn", "app_server:app", "--host", "0.0.0.0", "--port", "8000"]
