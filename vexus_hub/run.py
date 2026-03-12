#!/usr/bin/env python3
"""
Vexus IA - Sistema de Agendamento via WhatsApp
Aplicação principal para execução do servidor Flask
"""

import os
import sys
from app import create_app, socketio, db
from app.tasks import celery

def main():
    """Função principal para executar a aplicação"""
    # Definir ambiente
    env = os.getenv('FLASK_ENV', 'development')

    # Criar aplicação
    app = create_app(env)

    # Configurar Celery
    celery.conf.update(
        broker_url=app.config.get('CELERY_BROKER_URL'),
        result_backend=app.config.get('CELERY_RESULT_BACKEND')
    )

    # Verificar se deve executar worker do Celery
    if len(sys.argv) > 1 and sys.argv[1] == 'worker':
        print("🚀 Iniciando worker do Celery...")
        from celery.bin.worker import worker
        from celery.bin.beat import beat

        # Executar beat e worker
        if len(sys.argv) > 2 and sys.argv[2] == 'beat':
            print("⏰ Iniciando Celery Beat...")
            beat().run()
        else:
            print("⚙️  Iniciando Celery Worker...")
            worker().run()
        return

    # Executar aplicação Flask
    if env == 'development':
        print("🚀 Iniciando servidor de desenvolvimento...")
        print(f"🌐 Aplicação disponível em: http://localhost:{app.config.get('PORT', 5000)}")
        print("📱 Webhook WhatsApp: http://localhost:5000/api/whatsapp/webhook")

        # Executar com SocketIO para desenvolvimento
        socketio.run(
            app,
            host=app.config.get('HOST', '0.0.0.0'),
            port=app.config.get('PORT', 5000),
            debug=True
        )
    else:
        print("🚀 Iniciando servidor de produção...")
        from gunicorn.app.wsgiapp import WSGIApplication

        # Configurar Gunicorn
        sys.argv = [
            'gunicorn',
            'run:app',
            '--bind', f"0.0.0.0:{app.config.get('PORT', 8000)}",
            '--workers', str(app.config.get('WORKERS', 4)),
            '--worker-class', 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker',
            '--log-level', 'info'
        ]

        WSGIApplication().run()

if __name__ == '__main__':
    main()