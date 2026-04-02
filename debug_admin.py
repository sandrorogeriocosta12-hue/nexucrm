#!/usr/bin/env python3
"""
Debug script to test admin router import
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())
print(f"Python path: {sys.path}")
print(f"Current dir: {os.getcwd()}")

try:
    print("Testing admin router import...")
    from vexus_crm.admin.routes import router
    print("✅ Admin router imported successfully")
    print(f"Router prefix: {router.prefix}")
    print(f"Number of routes: {len(router.routes)}")
    for i, route in enumerate(router.routes[:5]):
        print(f"  Route {i+1}: {route.path} - {route.methods}")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    import vexus_crm
    print(f"vexus_crm path: {vexus_crm.__file__}")
    import vexus_crm.admin
    print(f"vexus_crm.admin path: {vexus_crm.admin.__file__}")
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()
