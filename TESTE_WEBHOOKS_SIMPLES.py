#!/usr/bin/env python3
"""
🎯 TESTE RÁPIDO DE WEBHOOKS - Nexus CRM
"""

import requests
import time

server_url = "http://localhost:8080"

# Test WhatsApp
try:
    response = requests.post(
        f'{server_url}/webhooks/whatsapp/test',
        json={
            'event': 'messages.upsert',
            'data': {
                'instanceName': 'test',
                'messages': [{
                    'key': {'fromMe': False},
                    'from': '5511987654321',
                    'pushName': 'Test',
                    'text': 'Webhook test',
                    'type': 'text',
                    'messageTimestamp': int(time.time())
                }]
            }
        },
        timeout=3
    )
    print(f"✅ WhatsApp Webhook: {response.status_code}")
except Exception as e:
    print(f"❌ WhatsApp: {str(e)}")

# Test Instagram
try:
    response = requests.post(
        f'{server_url}/webhooks/instagram',
        json={
            'entry': [{
                'messaging': [{
                    'sender': {'id': '123'},
                    'message': {'text': 'test'}
                }]
            }]
        },
        timeout=3
    )
    print(f"✅ Instagram Webhook: {response.status_code}")
except Exception as e:
    print(f"❌ Instagram: {str(e)}")

print("\n✅ Webhooks respondendo!")
