#!/bin/bash

################################################################################
# 🚀 NEXUS CRM - QUICK START REFERENCE CARD
# Copy & paste commands below to get production-ready in minutes
################################################################################

echo "
╔════════════════════════════════════════════════════════════════════════════╗
║                 🚀 NEXUS CRM - PRODUCTION QUICK START                      ║
║                    By: Development Team                                    ║
║                    Status: 🟢 Ready for Production                         ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 STEP 1: SETUP ENVIRONMENT (1 minute)
════════════════════════════════════════════════════════════════════════════
"

# Copy env template
cp .env.example .env
echo "✅ Created .env from template"
echo ""
echo "📝 Edit .env with your configuration:"
echo "   nano .env"
echo ""
echo "   Required settings:"
echo "   • DATABASE_URL=postgresql://user:pass@localhost:5432/nexuscrm"
echo "   • SECRET_KEY=<generate-random-key>"
echo "   • SMTP_USER=your-email@gmail.com"
echo "   • SMTP_PASSWORD=<app-password>"
echo ""

echo "════════════════════════════════════════════════════════════════════════════
📦 STEP 2: INSTALL DEPENDENCIES (3 minutes)
════════════════════════════════════════════════════════════════════════════
"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-production.txt
echo "✅ Dependencies installed"

echo ""
echo "════════════════════════════════════════════════════════════════════════════
✅ STEP 3: VALIDATE DEPLOYMENT (2 minutes)
════════════════════════════════════════════════════════════════════════════
"

# Run deployment checker
python scripts/deployment_checker.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════
🧪 STEP 4: TEST LOCALLY (2 minutes)
════════════════════════════════════════════════════════════════════════════
"

echo "Start server with:"
echo "  uvicorn app_server:app --reload"
echo ""
echo "Visit API docs:"
echo "  http://localhost:8000/api/docs"
echo ""

echo "════════════════════════════════════════════════════════════════════════════
🚀 STEP 5: DEPLOY TO CLOUD
════════════════════════════════════════════════════════════════════════════
"

echo "Option A: Railway (Easiest)"
echo "  1. Go to https://railway.app"
echo "  2. Connect GitHub repository"
echo "  3. Set environment variables from .env"
echo "  4. Deploy!"
echo ""

echo "Option B: AWS EC2"
echo "  See: docs/DEPLOYMENT_GUIDE.md → AWS (EC2 + RDS)"
echo ""

echo "Option C: DigitalOcean"
echo "  See: docs/DEPLOYMENT_GUIDE.md → DigitalOcean (App Platform)"
echo ""

cat << 'EOF'

════════════════════════════════════════════════════════════════════════════
📋 SETUP CHECKLIST
════════════════════════════════════════════════════════════════════════════

CONFIGURATION:
  [ ] Edit .env with database credentials
  [ ] Set SMTP_USER & SMTP_PASSWORD (email)
  [ ] Generate SECRET_KEY and JWT_SECRET_KEY
  [ ] Set ENVIRONMENT=production

SETUP:
  [ ] Create PostgreSQL database (local or cloud)
  [ ] Install Python dependencies
  [ ] Run deployment_checker.py
  [ ] Test API at http://localhost:8000/api/docs

DEPLOYMENT:
  [ ] Choose cloud provider (Railway recommended)
  [ ] Configure environment variables
  [ ] Deploy application
  [ ] Verify endpoints responding

MONITORING:
  [ ] Setup Sentry (optional but recommended)
  [ ] Configure UptimeRobot monitoring
  [ ] Enable backup automation
  [ ] Test database backup/restore

════════════════════════════════════════════════════════════════════════════
🔗 IMPORTANT ENDPOINTS
════════════════════════════════════════════════════════════════════════════

When deployed at https://api.nexuscrm.tech:

Health Check ........... GET  /health
Status Report .......... GET  /status  
Performance Metrics .... GET  /metrics
API Documentation ...... GET  /api/docs
OpenAPI Schema ......... GET  /api/openapi.json

Email Verification ..... POST /auth/email/send-verification
Verify Email Code ....... POST /auth/email/verify-email
Enable 2FA .............. POST /auth/email/enable-2fa

════════════════════════════════════════════════════════════════════════════
🛠️ USEFUL COMMANDS
════════════════════════════════════════════════════════════════════════════

# Start development server
uvicorn app_server:app --reload

# Run production server
gunicorn app_server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Validate deployment readiness
python scripts/deployment_checker.py

# Backup database
./scripts/backup-db.sh

# Restore from backup
./scripts/restore-db.sh /path/to/backup.sql.gz

# View PostgreSQL
psql $DATABASE_URL
  SELECT * FROM users;  -- List users

# Git operations
git status           # Check changes
git add -A           # Stage all files
git commit -m "..."  # Commit
git push origin main # Push to GitHub

════════════════════════════════════════════════════════════════════════════
📚 DOCUMENTATION
════════════════════════════════════════════════════════════════════════════

Start Here: PRODUCTION_SETUP_COMPLETE.md
Deployment: docs/DEPLOYMENT_GUIDE.md
Monitoring: docs/SLA_MONITORING.md
Email Setup: vexus_crm/services/email_service.py

════════════════════════════════════════════════════════════════════════════
⏱️ ESTIMATED TIME
════════════════════════════════════════════════════════════════════════════

Local Setup ..................... 10 minutes
Database Configuration .......... 5 minutes
Validation & Testing ............ 5 minutes
Cloud Deployment (Railway) ...... 5 minutes
─────────────────────────────────────────────
TOTAL .............................. ~30 minutes

════════════════════════════════════════════════════════════════════════════
❓ TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════

If something doesn't work, check:

1. Validator: python scripts/deployment_checker.py
2. Logs: tail -f /var/log/nexuscrm/app.log
3. API Docs: http://localhost:8000/api/docs
4. Guide: See docs/DEPLOYMENT_GUIDE.md → Troubleshooting

════════════════════════════════════════════════════════════════════════════
🎯 YOU ARE HERE (Production Ready)
════════════════════════════════════════════════════════════════════════════

✅ Professional infrastructure implemented
✅ Monitoring & health checks ready
✅ Backup & disaster recovery automated
✅ CI/CD pipeline configured
✅ Email & 2FA service ready
✅ Complete documentation provided
✅ All code committed to GitHub

Next: Follow checklist above and start deployment! 🚀

════════════════════════════════════════════════════════════════════════════
EOF
