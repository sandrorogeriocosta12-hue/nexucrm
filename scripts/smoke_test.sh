#!/bin/bash
# Simple automated smoke test for core paths
set -e

BASE_URL=${BASE_URL:-http://localhost:8080}

function check() {
  echo "Checking $1..."
  curl -fsS $2 > /dev/null || { echo "FAIL $1"; exit 1; }
  echo "OK $1"
}

# 1. health
check health "$BASE_URL/health"

# 2. signup/login
EMAIL=testsmoke@vexus.com
PASSWORD=Sm0keTest123
DATA="{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"name\":\"Smoke\"}"

echo "Signing up..."
curl -fsS -X POST "$BASE_URL/auth/signup" -H "Content-Type: application/json" -d "$DATA" -c smoke_cookies.txt > /dev/null

# login (should succeed even if user exists)
echo "Logging in..."
curl -fsS -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d "$DATA" -c smoke_cookies.txt > /dev/null

# 3. get current user via cookies
echo "Getting /me via cookie"
curl -fsS "$BASE_URL/me" -b smoke_cookies.txt | jq

echo "Smoke tests passed"
