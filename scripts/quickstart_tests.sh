#!/bin/bash
#
# QuickStart Tests - Valida todos os endpoints do Vexus CRM
# Executa verificações rápidas de cada funcionalidade
#

API_URL="http://localhost:8080"
FRONTEND_URL="http://localhost:8081"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0

# Helper function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_code=$5
    local token=$6

    echo -n "Testing $name... "
    
    local cmd="curl -s -w '\n%{http_code}' -X $method '$API_URL$endpoint'"
    
    if [ -n "$token" ]; then
        cmd="$cmd -H 'Authorization: Bearer $token'"
    fi
    
    if [ -n "$data" ]; then
        cmd="$cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    local response=$(eval $cmd)
    local code=$(echo "$response" | tail -n 1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$code" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS (HTTP $code)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL (Expected HTTP $expected_code, got $code)${NC}"
        echo "  Response: $body"
        ((FAILED++))
    fi
}

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}🚀 Vexus CRM - QuickStart Tests${NC}"
echo -e "${BLUE}=====================================${NC}\n"

# 1. Health Check
echo -e "${YELLOW}1. Health Checks${NC}"
test_endpoint "Health Check" "GET" "/health" "" "200"
echo ""

# 2. Authentication
echo -e "${YELLOW}2. Authentication${NC}"
test_endpoint "Login (Admin)" "POST" "/auth/login" '{"email":"admin@vexus.com","password":"admin123"}' "200"

# Get token for next tests
TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vexus.com","password":"admin123"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ Could not get auth token${NC}"
    exit 1
fi

test_endpoint "Get Current User" "GET" "/me" "" "200" "$TOKEN"
test_endpoint "Signup New User" "POST" "/auth/signup" '{"email":"test@example.com","password":"test123","name":"Test User"}' "200"
echo ""

# 3. Data Endpoints
echo -e "${YELLOW}3. Data Endpoints${NC}"
test_endpoint "Get Leads (authenticated)" "GET" "/leads" "" "200" "$TOKEN"
test_endpoint "Get Appointments (public)" "GET" "/appointments" "" "200"
test_endpoint "Get Agents" "GET" "/agents" "" "200" "$TOKEN"
test_endpoint "Get Analytics Summary" "GET" "/analytics/summary" "" "200" "$TOKEN"
echo ""

# 4. Operations
echo -e "${YELLOW}4. Operations${NC}"
test_endpoint "Get Lead by ID" "GET" "/leads/1" "" "200" "$TOKEN"
test_endpoint "Generate Proposal" "POST" "/proposals/generate" '{"lead_id":1,"template":"basic"}' "200" "$TOKEN"
test_endpoint "Get Proposals" "GET" "/proposals" "" "200" "$TOKEN"
test_endpoint "Send Chat Message" "POST" "/chat/send" '{"content":"Hello AI","sender":"user"}' "200" "$TOKEN"
test_endpoint "Get Chat History" "GET" "/chat/history" "" "200" "$TOKEN"
echo ""

# 5. Frontend
echo -e "${YELLOW}5. Frontend${NC}"
echo -n "Testing Frontend Health... "
STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$FRONTEND_URL/dashboard.html")
if [ "$STATUS" == "200" ]; then
    echo -e "${GREEN}✓ PASS (HTTP $STATUS)${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL (HTTP $STATUS)${NC}"
    ((FAILED++))
fi
echo ""

# Summary
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}📊 Test Results${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "✅ Passed: ${GREEN}$PASSED${NC}"
echo -e "❌ Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo -e "  1. Open frontend: ${BLUE}$FRONTEND_URL/dashboard.html${NC}"
    echo -e "  2. Login with: admin@vexus.com / admin123"
    echo -e "  3. Explore features: leads, propostas, agentes IA"
    echo -e "  4. View API docs: ${BLUE}$API_URL/docs${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Check backend logs: tail -f logs/backend.log${NC}"
    exit 1
fi
