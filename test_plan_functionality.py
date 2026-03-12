#!/usr/bin/env python3
"""
Test script to verify plan selection functionality
"""
import re

# Read the HTML file
with open('/home/victor-emanuel/PycharmProjects/Vexus Service/frontend/app.html', 'r') as f:
    html = f.read()

print("=" * 60)
print("Testing Plan Selection Functionality")
print("=" * 60)

# Test 1: Check plan cards exist
plan_cards = re.findall(r'class="plan-card.*?data-plan="(starter|professional|premium)"', html)
print(f"\n✅ Plan cards found: {len(plan_cards)}")
for card in plan_cards:
    print(f"   - {card}")

# Test 2: Check radio inputs exist
radios = re.findall(r'<input type="radio" name="selected-plan" value="(starter|professional|premium)"', html)
print(f"\n✅ Radio inputs found: {len(radios)}")
for radio in radios:
    print(f"   - {radio}")

# Test 3: Check if Professional has checked attribute (it shouldn't)
if 'value="professional" checked' in html:
    print("\n❌ ERROR: Professional radio has 'checked' attribute (should be removed)")
else:
    print("\n✅ Professional radio does NOT have 'checked' attribute (correct)")

# Test 4: Check if setupSignupStepListeners has debug logs
if '🎯 DEBUG: Procurando por .plan-card elementos...' in html:
    print("\n✅ Debug logs for plan card selection found")
else:
    print("\n❌ DEBUG: Debug logs not found")

# Test 5: Check if Professional default selection logic exists
if 'Professional selecionado como padrão' in html:
    print("\n✅ Professional default selection logic found")
else:
    print("\n❌ Professional default selection logic NOT found")

# Test 6: Check event listener code
if '.addEventListener(\'click\', function()' in html:
    print("\n✅ Plan card click listeners found")
else:
    print("\n❌ Plan card click listeners NOT found")

# Test 7: Check radio checked logic
if 'radio.checked = true;' in html:
    print("\n✅ Radio.checked = true logic found")
else:
    print("\n❌ Radio.checked = true logic NOT found")

# Test 8: Check validation for step 4
if "currentSignupStep === 4" in html and "Selecione um plano" in html:
    print("\n✅ Step 4 validation (plan selection) found")
else:
    print("\n❌ Step 4 validation NOT found")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
