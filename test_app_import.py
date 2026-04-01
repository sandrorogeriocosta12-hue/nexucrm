#!/usr/bin/env python3
"""Quick test of app_server import"""
import sys
import os
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
sys.path.insert(0, '/home/victor-emanuel/PycharmProjects/Vexus Service')

try:
    from app_server import app
    print('✅ App server importado com sucesso!')
    
    # Check routers
    routes = app.routes
    print(f'Total de rotas: {len(routes)}')
    
    # Check admin routes
    admin_routes = [r.path for r in routes if '/api/admin' in str(r.path)]
    print(f'Rotas de admin: {len(admin_routes)}')
    for route in admin_routes[:5]:
        print(f'  - {route}')
    
    # Check dashboard and login
    dashboard_login = [r.path for r in routes if r.path in ['/dashboard', '/login']]
    print(f'Dashboard/Login pages: {dashboard_login}')
    
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
