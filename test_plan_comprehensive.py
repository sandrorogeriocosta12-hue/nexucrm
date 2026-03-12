#!/usr/bin/env python3
"""
Comprehensive test for plan selection functionality
"""
import re
import json

print("=" * 70)
print(" 🧪 COMPREHENSIVE PLAN SELECTION TEST")
print("=" * 70)

with open('/home/victor-emanuel/PycharmProjects/Vexus Service/frontend/app.html', 'r') as f:
    html = f.read()

tests_passed = 0
tests_failed = 0

def test(name, condition, details=""):
    global tests_passed, tests_failed
    if condition:
        print(f"✅ PASS: {name}")
        if details:
            print(f"   📍 {details}")
        tests_passed += 1
    else:
        print(f"❌ FAIL: {name}")
        if details:
            print(f"   📍 {details}")
        tests_failed += 1

print("\n1️⃣  PLAN CARDS EXIST")
plan_count = len(re.findall(r'data-plan="(starter|professional|premium)"', html))
test("Plan cards present", plan_count == 3, f"Found {plan_count} cards")

print("\n2️⃣  RADIO INPUTS EXIST")
radio_count = len(re.findall(r'name="selected-plan"', html))
test("Radio inputs present", radio_count == 3, f"Found {radio_count} radios")

print("\n3️⃣  NO PRE-CHECKED RADIOS")
no_prechecked = 'value="starter" checked' not in html and 'value="premium" checked' not in html
professional_checked = 'value="professional" checked' in html
test("Professional not pre-checked", not professional_checked, 
     "Removed pre-checked attribute" if not professional_checked else "ERROR: still has checked")

print("\n4️⃣  PLAN CARD LISTENERS CODE")
has_listeners = 'document.querySelectorAll(\'.plan-card\').forEach' in html
test("Plan card listeners exist", has_listeners, 
     "Found forEach loop for plan-cards" if has_listeners else "ERROR: listeners not found")

print("\n5️⃣  CLICK EVENT HANDLER")
has_click_handler = 'card.addEventListener(\'click\', function()' in html
test("Click event handler", has_click_handler,
     "Found click listener" if has_click_handler else "ERROR: click handler missing")

print("\n6️⃣  RADIO SELECTION CODE")
has_radio_check = 'radio.checked = true' in html or 'this.querySelector(\'.plan-radio\').checked' in html
test("Radio selection logic", has_radio_check,
     "Found radio.checked = true" if has_radio_check else "ERROR: radio selection missing")

print("\n7️⃣  CSS STYLING FOR SELECTED")
has_css_selected = '.plan-card.selected' in html
test("CSS for selected cards", has_css_selected,
     "Found .plan-card.selected CSS" if has_css_selected else "ERROR: CSS missing")

print("\n8️⃣  STEP 4 VALIDATION")
has_step4_validation = 'currentSignupStep === 4' in html and 'input[name="selected-plan"]:checked' in html
test("Step 4 validation logic", has_step4_validation,
     "Found plan selection validation" if has_step4_validation else "ERROR: validation missing")

print("\n9️⃣  PROFESSIONAL DEFAULT LOGIC")
has_default_logic = 'Professional selecionado como padrão' in html
test("Professional default selection", has_default_logic,
     "Found default selection logic" if has_default_logic else "ERROR: default logic missing")

print("\n🔟 PLAN SELECTION IN HANDLEIGNUP")
has_plan_in_handle = re.search(r'selectedPlan(Radio)?\s*=\s*document\.querySelector.*selected-plan.*checked', html)
test("Plan collection in handleSignup", has_plan_in_handle is not None,
     "Found plan selection in handleSignup" if has_plan_in_handle else "ERROR: plan not collected")

print("\n1️⃣1️⃣  DEBUG LOGS PRESENT")
has_debug_logs = '🎯 DEBUG:' in html and '🎯 Card clicado:' in html
test("Debug console logs", has_debug_logs,
     "Found debug logs for troubleshooting" if has_debug_logs else "WARNING: debug logs missing")

print("\n1️⃣2️⃣  SETUPSIGNUPSTEPLISTENERS CALLED")
has_setup_call = 'setupSignupStepListeners()' in html
test("setupSignupStepListeners called", has_setup_call,
     "Found function call" if has_setup_call else "ERROR: function not called")

print("\n" + "=" * 70)
print(f" RESULTS: ✅ {tests_passed} passed | ❌ {tests_failed} failed")
print("=" * 70)

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! Plan selection should be working correctly.")
    print("\n📋 NEXT STEPS:")
    print("   1. Open http://localhost:8000/frontend/app.html")
    print("   2. Click 'Cadastro Direto'")
    print("   3. Fill in steps 1-3")
    print("   4. Go to step 4 (plan selection)")
    print("   5. Click on different plan cards and verify:")
    print("      - Plan card gets highlighted (border + background color)")
    print("      - Only one plan is selected at a time")
    print("   6. Click 'Finalizar Cadastro'")
    print("\n📊 Check browser console for debug logs (F12 -> Console tab)")
else:
    print(f"\n⚠️  {tests_failed} issues found. Please review the errors above.")
