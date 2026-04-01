#!/bin/bash

# ============================================================================
# COMPLETE PAYMENT FLOW TEST SUITE
# ============================================================================
# This script tests all endpoints and flows for the payment system
# Run with: bash test_complete_flow.sh

echo "=====================================================
🚀 COMPLETE PAYMENT FLOW TEST SUITE
=====================================================\n"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for tests
PASSED=0
FAILED=0

# Test function
run_test() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "${YELLOW}Test:${NC} $test_name"
    
    response=$(curl -s -X $method http://localhost:8000$endpoint \
        -H "Content-Type: application/json" \
        -d "$data")
    
    success=$(echo $response | jq -r '.success' 2>/dev/null)
    
    if [ "$success" = "true" ]; then
        echo -e "${GREEN}✅ PASSED${NC}\n"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Response: $response\n"
        ((FAILED++))
    fi
}

# ============================================================================
# TEST 1: Homepage Access
# ============================================================================
echo -e "\n${YELLOW}=== TEST GROUP 1: PAGE LOADING ===${NC}"

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/signup | grep -q "200"; then
    echo -e "${GREEN}✅ /signup page loads${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ /signup page failed${NC}"
    ((FAILED++))
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/payment | grep -q "200"; then
    echo -e "${GREEN}✅ /payment page loads${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ /payment page failed${NC}"
    ((FAILED++))
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard | grep -q "200"; then
    echo -e "${GREEN}✅ /dashboard page loads${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ /dashboard page failed${NC}"
    ((FAILED++))
fi

# ============================================================================
# TEST 2: Signup API
# ============================================================================
echo -e "\n${YELLOW}=== TEST GROUP 2: SIGNUP API ===${NC}"

run_test "Create account - Starter plan" "POST" "/api/auth/signup" \
'{
  "name":"Carlos",
  "sobrenome":"Silva",
  "email":"carlos@test.com",
  "password":"password123",
  "plan":"starter"
}'

run_test "Create account - Professional plan" "POST" "/api/auth/signup" \
'{
  "name":"Ana",
  "sobrenome":"Santos",
  "email":"ana@test.com",
  "password":"password456",
  "plan":"professional"
}'

run_test "Create account - Premium plan" "POST" "/api/auth/signup" \
'{
  "name":"Paulo",
  "sobrenome":"Costa",
  "email":"paulo@test.com",
  "password":"password789",
  "plan":"premium"
}'

# ============================================================================
# TEST 3: Payment with Card
# ============================================================================
echo -e "\n${YELLOW}=== TEST GROUP 3: CARD PAYMENT ===${NC}"

run_test "Card payment - Starter plan" "POST" "/api/payment/process" \
'{
  "plan":"starter",
  "payment_method":"card",
  "card_name":"João Silva",
  "card_number":"4111111111111111",
  "card_expiry":"12/25",
  "card_cvv":"123",
  "email":"joao@card.com",
  "whatsapp":"+5511999999999",
  "contact_preference_email":true,
  "contact_preference_whatsapp":true
}'

run_test "Card payment - Professional plan" "POST" "/api/payment/process" \
'{
  "plan":"professional",
  "payment_method":"card",
  "card_name":"Maria Oliveira",
  "card_number":"5555555555554444",
  "card_expiry":"06/26",
  "card_cvv":"456",
  "email":"maria@card.com",
  "whatsapp":"+5521987654321",
  "contact_preference_email":true,
  "contact_preference_whatsapp":false
}'

run_test "Card payment - Premium plan" "POST" "/api/payment/process" \
'{
  "plan":"premium",
  "payment_method":"card",
  "card_name":"Pedro Santos",
  "card_number":"378282246310005",
  "card_expiry":"03/27",
  "card_cvv":"7893",
  "email":"pedro@card.com",
  "whatsapp":"",
  "contact_preference_email":true,
  "contact_preference_whatsapp":false
}'

# ============================================================================
# TEST 4: Payment with Boleto
# ============================================================================
echo -e "\n${YELLOW}=== TEST GROUP 4: BOLETO PAYMENT ===${NC}"

run_test "Boleto payment - Starter plan" "POST" "/api/payment/process" \
'{
  "plan":"starter",
  "payment_method":"boleto",
  "boleto_cnpj":"12.345.678/0001-93",
  "boleto_company":"Company A LTDA",
  "email":"company.a@boleto.com",
  "whatsapp":"",
  "contact_preference_email":true,
  "contact_preference_whatsapp":false
}'

run_test "Boleto payment - Professional plan" "POST" "/api/payment/process" \
'{
  "plan":"professional",
  "payment_method":"boleto",
  "boleto_cnpj":"98.765.432/0001-10",
  "boleto_company":"Tech Solutions Inc",
  "email":"tech@boleto.com",
  "whatsapp":"+5585987654321",
  "contact_preference_email":true,
  "contact_preference_whatsapp":true
}'

run_test "Boleto payment - Premium plan" "POST" "/api/payment/process" \
'{
  "plan":"premium",
  "payment_method":"boleto",
  "boleto_cnpj":"11.222.333/0001-44",
  "boleto_company":"Premium Services LLC",
  "email":"premium@boleto.com",
  "whatsapp":"+5511999888777",
  "contact_preference_email":false,
  "contact_preference_whatsapp":true
}'

# ============================================================================
# TEST 5: Payment with PIX
# ============================================================================
echo -e "\n${YELLOW}=== TEST GROUP 5: PIX PAYMENT ===${NC}"

run_test "PIX payment - Starter plan" "POST" "/api/payment/process" \
'{
  "plan":"starter",
  "payment_method":"pix",
  "email":"startup@pix.com",
  "whatsapp":"",
  "contact_preference_email":true,
  "contact_preference_whatsapp":false
}'

run_test "PIX payment - Professional plan" "POST" "/api/payment/process" \
'{
  "plan":"professional",
  "payment_method":"pix",
  "email":"professional@pix.com",
  "whatsapp":"+5512988776655",
  "contact_preference_email":true,
  "contact_preference_whatsapp":true
}'

run_test "PIX payment - Premium plan" "POST" "/api/payment/process" \
'{
  "plan":"premium",
  "payment_method":"pix",
  "email":"premium@pix.com",
  "whatsapp":"",
  "contact_preference_email":false,
  "contact_preference_whatsapp":false
}'

# ============================================================================
# TEST 6: Error Cases
# ============================================================================
echo -e "\n${YELLOW}=== TEST GROUP 6: ERROR VALIDATION ===${NC}"

# Test invalid plan
invalid_plan=$(curl -s -X POST http://localhost:8000/api/payment/process \
    -H "Content-Type: application/json" \
    -d '{
      "plan":"invalid_plan",
      "payment_method":"card",
      "card_name":"Test",
      "card_number":"4111111111111111",
      "card_cvv":"123",
      "email":"test@test.com",
      "whatsapp":"",
      "contact_preference_email":true,
      "contact_preference_whatsapp":false
    }' | jq -r '.success' 2>/dev/null)

if [ "$invalid_plan" != "true" ]; then
    echo -e "${GREEN}✅ Rejects invalid plan${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Should reject invalid plan${NC}"
    ((FAILED++))
fi

# Test missing email
missing_email=$(curl -s -X POST http://localhost:8000/api/payment/process \
    -H "Content-Type: application/json" \
    -d '{
      "plan":"professional",
      "payment_method":"card",
      "card_name":"Test",
      "card_number":"4111111111111111",
      "card_cvv":"123",
      "email":"",
      "whatsapp":"",
      "contact_preference_email":true,
      "contact_preference_whatsapp":false
    }' | jq -r '.success' 2>/dev/null)

if [ "$missing_email" != "true" ]; then
    echo -e "${GREEN}✅ Rejects missing email${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Should reject missing email${NC}"
    ((FAILED++))
fi

# Test invalid CNPJ
invalid_cnpj=$(curl -s -X POST http://localhost:8000/api/payment/process \
    -H "Content-Type: application/json" \
    -d '{
      "plan":"professional",
      "payment_method":"boleto",
      "boleto_cnpj":"12.345.678",
      "boleto_company":"Test Co",
      "email":"test@test.com",
      "whatsapp":"",
      "contact_preference_email":true,
      "contact_preference_whatsapp":false
    }' | jq -r '.success' 2>/dev/null)

if [ "$invalid_cnpj" != "true" ]; then
    echo -e "${GREEN}✅ Rejects invalid CNPJ (wrong length)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Should reject invalid CNPJ${NC}"
    ((FAILED++))
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n${YELLOW}=== TEST SUMMARY ===${NC}"
TOTAL=$((PASSED + FAILED))
echo -e "${GREEN}✅ PASSED: $PASSED${NC}"
echo -e "${RED}❌ FAILED: $FAILED${NC}"
echo -e "📊 TOTAL: $TOTAL tests\n"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! SYSTEM IS PRODUCTION READY!${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED. Review the output above.${NC}\n"
    exit 1
fi
