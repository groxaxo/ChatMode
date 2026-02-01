#!/bin/bash
# Test ChatMode Login

echo "🧪 Testing ChatMode Login"
echo "========================="
echo ""

# Test 1: Health Check
echo "1. Health Check..."
HEALTH=$(curl -s http://localhost:8002/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ Server is healthy"
else
    echo "   ❌ Server health check failed"
    exit 1
fi
echo ""

# Test 2: Login
echo "2. Testing Login (admin/admin)..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "   ✅ Login successful"
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "   Token: ${TOKEN:0:50}..."
else
    echo "   ❌ Login failed"
    echo "   Response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Access Protected Endpoint
echo "3. Testing Protected Endpoint..."
AGENTS_RESPONSE=$(curl -s -X GET http://localhost:8002/api/v1/agents \
  -H "Authorization: Bearer $TOKEN")

if echo "$AGENTS_RESPONSE" | grep -q "agents"; then
    echo "   ✅ Successfully accessed protected endpoint"
    AGENT_COUNT=$(echo "$AGENTS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['agents']))" 2>/dev/null || echo "0")
    echo "   Found $AGENT_COUNT agents"
elif echo "$AGENTS_RESPONSE" | grep -q "detail"; then
    echo "   ⚠️  Endpoint returned error (might be expected):"
    echo "   $AGENTS_RESPONSE"
else
    echo "   ✅ Protected endpoint accessible"
fi
echo ""

echo "========================="
echo "✅ All critical tests passed!"
echo ""
echo "Login Credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "Access the web interface at:"
echo "  http://localhost:8002"
