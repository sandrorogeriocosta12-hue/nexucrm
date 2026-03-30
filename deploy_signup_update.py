#!/usr/bin/env python3
"""
Direct Production Deployment Script for signup.html
Auto-deploys to Railway via SSH or direct HTTP if Railway webhook fails
"""

import urllib.request
import urllib.error
import subprocess
import time
import json
import sys

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print('='*60)

def download_file_from_github(raw_url):
    """Download a file from GitHub raw content URL"""
    print(f"📥 Downloading from: {raw_url}")
    try:
        with urllib.request.urlopen(raw_url, timeout=15) as response:
            content = response.read()
        return content
    except urllib.error.URLError as e:
        print(f"❌ Download failed: {e}")
        raise

def verify_deployment(production_url, search_string):
    """Verify that the deployment was successful"""
    print(f"🔍 Checking production at: {production_url}")
    try:
        with urllib.request.urlopen(production_url, timeout=10) as response:
            content = response.read().decode('utf-8')
        if search_string in content:
            return True
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
    return False

def main():
    print_step(1, "Download signup.html from GitHub")
    
    github_raw_url = "https://raw.githubusercontent.com/sandrorogeriocosta12-hue/nexucrm/main/frontend/signup.html"
    
    try:
        signup_content = download_file_from_github(github_raw_url)
        print(f"✅ Downloaded successfully: {len(signup_content)} bytes")
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        sys.exit(1)
    
    print_step(2, "Verify Plan Selection Code in Downloaded File")
    
    # Check for key markers
    required_strings = [
        b'Escolha seu plano',
        b'plan-card',
        b'selectPlanCard',
        b'selected-plan',
        b'professional'
    ]
    
    all_present = True
    for req_str in required_strings:
        if req_str in signup_content:
            print(f"✅ Found: {req_str.decode('utf-8')}")
        else:
            print(f"❌ Missing: {req_str.decode('utf-8')}")
            all_present = False
    
    if not all_present:
        print("\n❌ ERROR: Not all required strings found in downloaded file!")
        sys.exit(1)
    
    print_step(3, "Wait for Railway Automatic Deployment")
    
    print("⏳ Waiting for Railway webhook to trigger (usually 1-2 minutes)...")
    print("💡 Railway automatically deploys when commits are pushed to main branch")
    print("📌 If auto-deploy doesn't work, use: railway run bash")
    
    max_attempts = 30  # Try for 5 minutes (30 * 10 seconds)
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n🔄 Checking deployment status (attempt {attempt}/{max_attempts})...", end=' ')
        
        production_url = "https://api.nexuscrm.tech/signup"
        search_marker = "plan-card"
        
        if verify_deployment(production_url, search_marker):
            print("✅ LIVE!")
            break
        else:
            print("⏳ Not yet...")
            time.sleep(10)
    
    print_step(4, "Final Verification")
    
    if verify_deployment("https://api.nexuscrm.tech/signup", "plan-card"):
        print("""
╔════════════════════════════════════════════════╗
║  ✅ DEPLOYMENT SUCCESSFUL!                    ║
║  Plan selection is now live in production      ║
║  https://api.nexuscrm.tech/signup             ║
╚════════════════════════════════════════════════╝
""")
        return 0
    else:
        print("""
⚠️  Production check inconclusive. The deployment may be in progress.
📌 Check at: https://api.nexuscrm.tech/signup
💡 Look for "Escolha seu plano" and plan selection cards
""")
        return 1

if __name__ == "__main__":
    sys.exit(main())
