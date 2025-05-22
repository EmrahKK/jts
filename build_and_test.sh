#!/bin/bash
# build_and_test.sh - Builds the Docker image and runs basic tests

set -e

echo "Building Docker image..."
docker build -t json-transform-service:latest .

echo "Starting container for testing..."
CONTAINER_ID=$(docker run -d -p 8000:8000 json-transform-service:latest)

echo "Container started with ID: $CONTAINER_ID"
echo "Waiting for service to start..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
curl -f http://localhost:8000/health || echo "Health check failed"

# Test readiness endpoint
echo "Testing readiness endpoint..."
curl -f http://localhost:8000/ready || echo "Readiness check failed"

# Test root endpoint
echo "Testing root endpoint..."
curl -s http://localhost:8000/ | python3 -m json.tool || echo "Root endpoint failed"

# Test transformation endpoint with sample data
echo "Testing transformation endpoint..."
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "alert": {
      "recipient": "+12345678900",
      "severity": "critical",
      "message": "Server CPU usage above 90%"
    }
  }' \
  http://localhost:8000/alert-to-sms | python3 -m json.tool || echo "Transformation test failed"

echo "Stopping container..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "Tests completed!"
