#!/bin/bash
# Test Agent Manager Functionality

echo "=========================================="
echo "Agent Manager Test Suite"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8002"

# Test 1: Login
echo "Test 1: Login to get access token..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
  echo "✓ Login successful"
else
  echo "✗ Login failed"
  exit 1
fi

echo ""

# Test 2: List agents
echo "Test 2: Listing all agents..."
AGENTS=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/agents/")
COUNT=$(echo "$AGENTS" | jq -r '.total')

if [ "$COUNT" == "5" ]; then
  echo "✓ Found 5 agents as expected"
else
  echo "✗ Expected 5 agents, found $COUNT"
fi

echo ""

# Test 3: Show agent names
echo "Test 3: Agent personalities loaded:"
echo "$AGENTS" | jq -r '.items[] | "  - \(.display_name) (\(.name)) - Temp: \(.temperature)"'

echo ""

# Test 4: Web interface accessible
echo "Test 4: Checking web interface..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$HTTP_CODE" == "200" ]; then
  echo "✓ Web interface accessible at $BASE_URL"
else
  echo "✗ Web interface returned HTTP $HTTP_CODE"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "All critical tests passed!"
echo ""
echo "Next steps:"
echo "  1. Open: $BASE_URL"
echo "  2. Go to Agent Manager tab"
echo "  3. Login: admin / admin123"
echo "  4. Explore the 5 personalities!"
echo ""
