Deployment guide - Vexus CRM (production)

This guide describes the steps to make the application run under `api.nexuscrm.tech`.
Adjust paths and user names to your server environment.

1) Place files on server
------------------------
scp -r . "user@yourserver:/home/victor-emanuel/PycharmProjects/Vexus\ Service"

2) Create virtualenv and install dependencies
---------------------------------------------
ssh user@yourserver
cd /home/victor-emanuel/PycharmProjects/Vexus\ Service
python3 -m venv /home/victor-emanuel/.venv
source /home/victor-emanuel/.venv/bin/activate
pip install -r requirements.txt

3) Configure environment
------------------------
- Copy `.env.example` to `.env` and fill real keys:
  cp .env.example .env
  nano .env

4) Nginx
--------
- Copy `deploy/nginx_vexus.conf` to `/etc/nginx/sites-available/vexus`
- Edit paths: frontend root and proxy_pass target
- Enable and test config:

sudo ln -s /etc/nginx/sites-available/vexus /etc/nginx/sites-enabled/vexus
sudo nginx -t
sudo systemctl reload nginx

5) Obtain TLS certificate (Certbot)
-----------------------------------
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.nexuscrm.tech

6) systemd services (API & workers)
-----------------------------------
# Copy unit files
sudo cp deploy/systemd_vexus_api.service /etc/systemd/system/vexus_api.service
sudo cp deploy/systemd_vexus_worker.service /etc/systemd/system/vexus_worker.service

# Reload and start
sudo systemctl daemon-reload
sudo systemctl enable vexus_api.service
sudo systemctl start vexus_api.service
sudo systemctl status vexus_api.service

sudo systemctl enable vexus_worker.service
sudo systemctl start vexus_worker.service
sudo systemctl status vexus_worker.service

7) Test endpoints
-----------------
# Health
curl -i https://api.nexuscrm.tech/
# Login
curl -X POST https://api.nexuscrm.tech/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"demo@vexus.com","password":"demo123"}'

8) Webhooks
-----------
- Configure your WhatsApp, Telegram, Instagram and Stripe webhooks to point to:
  https://api.nexuscrm.tech/api/v1/webhooks/whatsapp
  https://api.nexuscrm.tech/api/v1/webhooks/telegram
  https://api.nexuscrm.tech/api/v1/webhooks/instagram
  https://api.nexuscrm.tech/api/v1/webhooks/stripe

- Set verify tokens from `.env` (WHATSAPP_VERIFY_TOKEN etc.)

9) OpenAI
---------
- Add your `OPENAI_API_KEY` to `.env`
- Confirm domain is allowed if using organization restrictions

10) Monitoring & Logs
---------------------
- Logs default to `/var/log/nexuscrm/app.log` (set in `.env`)
- Consider Sentry/Dynatrace/Datadog for error/metrics

11) Troubleshooting
-------------------
- nginx test: `sudo nginx -t`
- systemd logs: `sudo journalctl -u vexus_api -f`
- worker logs: `sudo journalctl -u vexus_worker -f`


If you want, I can:
- generate the exact `nginx` server block adapted to your server paths,
- generate certbot command for a dry-run,
- help craft `systemd` ExecStart commands if your worker entrypoint differs.
