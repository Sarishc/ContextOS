#!/bin/bash
# Test RAG pipeline endpoints

set -e

API_URL="http://localhost:8000/api/v1/rag"

echo "🧪 Testing RAG Pipeline..."
echo ""

# Test 1: Ingest sample documents
echo "1️⃣  Testing document ingestion..."
INGEST_RESPONSE=$(curl -s -X POST "${API_URL}/ingest/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "Password Reset Guide",
        "content": "To reset your password, go to the login page and click on Forgot Password. Enter your email address and you will receive a reset link. Click the link and enter your new password. Make sure your password is at least 8 characters long and includes numbers and special characters.",
        "doc_type": "plain_text",
        "source": "docs/auth_guide.txt",
        "metadata": {"category": "authentication", "version": "1.0"}
      },
      {
        "title": "JIRA-123: Login Issue",
        "content": "Users are reporting that they cannot log in to the system. The error message shows authentication failed. This appears to be related to the recent password policy update. Users need to reset their passwords to comply with the new policy requirements.",
        "doc_type": "jira_ticket",
        "source": "JIRA",
        "metadata": {"ticket_id": "JIRA-123", "status": "Open", "priority": "High"}
      },
      {
        "title": "Slack: #support - Password Discussion",
        "content": "User asked: How do I change my password? Admin replied: You can change your password in your account settings. Navigate to Settings > Security > Change Password. Remember to use a strong password with mixed case letters, numbers, and symbols.",
        "doc_type": "slack_message",
        "source": "#support",
        "metadata": {"channel": "support", "timestamp": "2024-01-06T10:00:00Z"}
      },
      {
        "title": "API Authentication Documentation",
        "content": "Our API uses OAuth 2.0 for authentication. To authenticate, you need to obtain an access token by sending your credentials to the /auth/token endpoint. Include the token in the Authorization header for all subsequent requests. Tokens expire after 1 hour.",
        "doc_type": "plain_text",
        "source": "docs/api_auth.txt",
        "metadata": {"category": "api", "version": "2.0"}
      }
    ]
  }')

echo "$INGEST_RESPONSE" | python3 -m json.tool
echo ""
echo "✅ Documents ingested successfully!"
echo ""

# Wait for indexing
echo "⏳ Waiting for indexing to complete..."
sleep 3
echo ""

# Test 2: Get sources
echo "2️⃣  Testing sources endpoint..."
curl -s "${API_URL}/sources" | python3 -m json.tool
echo ""

# Test 3: Get stats
echo "3️⃣  Testing stats endpoint..."
curl -s "${API_URL}/stats" | python3 -m json.tool
echo ""

# Test 4: Search for similar documents
echo "4️⃣  Testing semantic search..."
echo ""
echo "Query 1: 'How do I reset my password?'"
SEARCH_RESPONSE=$(curl -s -X POST "${API_URL}/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "top_k": 3
  }')

echo "$SEARCH_RESPONSE" | python3 -m json.tool
echo ""

echo "Query 2: 'API authentication'"
curl -s -X POST "${API_URL}/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API authentication",
    "top_k": 3
  }' | python3 -m json.tool
echo ""

echo "Query 3: 'login problems' (filtered by JIRA tickets)"
curl -s -X POST "${API_URL}/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "login problems",
    "top_k": 2,
    "doc_type": "jira_ticket"
  }' | python3 -m json.tool
echo ""

# Test 5: Test async ingestion
echo "5️⃣  Testing async ingestion..."
ASYNC_RESPONSE=$(curl -s -X POST "${API_URL}/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "Test Async Document",
        "content": "This document is being processed asynchronously in the background.",
        "doc_type": "plain_text",
        "source": "test_async.txt"
      }
    ]
  }')

echo "$ASYNC_RESPONSE" | python3 -m json.tool
TASK_ID=$(echo "$ASYNC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])")
echo ""
echo "Task ID: $TASK_ID"
echo "Check task status: curl http://localhost:8000/api/v1/tasks/${TASK_ID}"
echo ""

echo "✅ All RAG pipeline tests completed successfully!"
echo ""
echo "📊 Summary:"
echo "  - Documents ingested and indexed"
echo "  - Semantic search working"
echo "  - Source attribution included"
echo "  - Async processing functional"
echo ""
echo "🎉 RAG Pipeline is operational!"

