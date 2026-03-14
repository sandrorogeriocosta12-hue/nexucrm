#!/bin/bash
# Test script for Vexus CRM Railway deployment

echo "🧪 Testing Vexus CRM locally..."

# Set PORT
export PORT=8000

# Test import
echo "📦 Testing app import..."
python3 -c "import app_test; print('✅ App imports successfully')" || exit 1

# Test server startup (background)
echo "🚀 Starting server..."
python3 -m uvicorn app_test:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test health endpoint
echo "🏥 Testing health endpoint..."
curl -s http://localhost:8000/health || {
    echo "❌ Health endpoint failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
}

# Test root endpoint
echo "🏠 Testing root endpoint..."
curl -s http://localhost:8000/ | head -5 || {
    echo "❌ Root endpoint failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
}

# Cleanup
echo "🧹 Cleaning up..."
kill $SERVER_PID 2>/dev/null

echo "✅ All tests passed! App is ready for Railway."