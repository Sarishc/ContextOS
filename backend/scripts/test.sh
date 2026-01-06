#!/bin/bash
# Test the API endpoints

set -e

API_URL="http://localhost:8000"

echo "🧪 Testing ContextOS Backend API..."
echo ""

# Test health endpoint
echo "1️⃣  Testing health endpoint..."
curl -s "${API_URL}/api/v1/health" | python -m json.tool
echo ""

# Test readiness endpoint
echo "2️⃣  Testing readiness endpoint..."
curl -s "${API_URL}/api/v1/health/ready" | python -m json.tool
echo ""

# Test liveness endpoint
echo "3️⃣  Testing liveness endpoint..."
curl -s "${API_URL}/api/v1/health/live" | python -m json.tool
echo ""

# Test creating a task
echo "4️⃣  Testing task creation..."
TASK_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/tasks/example" \
  -H "Content-Type: application/json" \
  -d '{"data": {"test": "hello"}}')
echo "$TASK_RESPONSE" | python -m json.tool
TASK_ID=$(echo "$TASK_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['task_id'])")
echo ""

# Wait a bit for task to process
echo "⏳ Waiting for task to process..."
sleep 3

# Check task status
echo "5️⃣  Checking task status..."
curl -s "${API_URL}/api/v1/tasks/${TASK_ID}" | python -m json.tool
echo ""

echo "✅ All tests passed!"

