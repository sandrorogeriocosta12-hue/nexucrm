#!/usr/bin/env python
"""Quick test of admin router import"""
import sys
sys.path.insert(0, '/home/victor-emanuel/PycharmProjects/Vexus Service')

try:
    from vexus_crm.admin.routes import router
    print('✅ Admin router importado com sucesso!')
    print(f'Router prefix: {router.prefix}')
    print(f'Router tags: {router.tags}')
    print(f'Routes: {len(router.routes)}')
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
