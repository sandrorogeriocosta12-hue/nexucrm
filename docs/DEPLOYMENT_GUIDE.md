# 🚀 NEXUS CRM - PROFESSIONAL DEPLOYMENT GUIDE

## 📋 QUICK START (5 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/sandrorogeriocosta12-hue/nexucrm.git
cd nexucrm
cp .env.example .env

# 2. Edit .env file with your configuration
nano .env

# 3. Run deployment checker
python scripts/deployment_checker.py

# 4. Install dependencies
pip install -r requirements-production.txt

# 5. Run application
uvicorn app_server:app --host 0.0.0.0 --port 8000
```

---

## 🔧 DETAILED SETUP INSTRUCTIONS

### Step 1: Environment Configuration (15 minutes)

```bash
# Copy example file
cp .env.example .env

# Edit configuration (use your favorite editor)
nano .env  # or vim, code, etc.
```

**Minimum Required Settings:**

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexuscrm

# Security
SECRET_KEY=<generate-strong-random-string>
JWT_SECRET_KEY=<generate-another-random-string>
ENVIRONMENT=production

# Email (Gmail example)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app-password-from-google-account>

# Optional but recommended
SENTRY_DSN=<your-sentry-dsn>
REDIS_URL=redis://localhost:6379/0
```

**Generate Strong Secret Keys:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Database Setup (10 minutes)

**Option A: PostgreSQL on Local Machine**

```bash
# Install PostgreSQL (macOS)
brew install postgresql

# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE nexuscrm;
CREATE USER vexus_user WITH PASSWORD 'secure_password';
ALTER ROLE vexus_user SET client_encoding TO 'utf8';
ALTER ROLE vexus_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE vexus_user SET default_transaction_deferrable TO on;
ALTER ROLE vexus_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE nexuscrm TO vexus_user;
EOF

# Update .env
DATABASE_URL=postgresql://vexus_user:secure_password@localhost:5432/nexuscrm
```

**Option B: PostgreSQL on Docker**

```bash
# Run PostgreSQL container
docker run -d \
  --name nexuscrm-db \
  -e POSTGRES_USER=vexus_user \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=nexuscrm \
  -p 5432:5432 \
  postgres:15-alpine

# Update .env
DATABASE_URL=postgresql://vexus_user:secure_password@localhost:5432/nexuscrm
```

**Option C: Cloud Database (Recommended for Production)**

```bash
# AWS RDS example
DATABASE_URL=postgresql://user:password@nexuscrm.xxxxx.amazonaws.com:5432/nexuscrm

# DigitalOcean Managed PostgreSQL
DATABASE_URL=postgresql://user:password@db-postgresql-xxx.a.db.ondigitalocean.com:25060/nexuscrm

# Railway
DATABASE_URL=postgresql://user:password@containers-us-west-xxx.railway.app:5432/nexuscrm
```

### Step 3: Install Dependencies (5 minutes)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install production requirements
pip install -r requirements-production.txt

# Verify installation
pip list | grep -E "fastapi|sqlalchemy|sentry"
```

### Step 4: Optional Services Setup

#### 🔍 Error Tracking (Sentry)

```bash
# 1. Sign up at https://sentry.io
# 2. Create new project → select "Python/FastAPI"
# 3. Copy your DSN
# 4. Update .env
SENTRY_DSN=https://your-key@sentry.io/project-id

# 5. Test Sentry integration (optional)
python -c "from sentry_sdk import Client; c = Client(os.getenv('SENTRY_DSN')); c.capture_message('Test')"
```

#### 💾 Redis Cache (Optional but Recommended)

```bash
# Install Redis (macOS)
brew install redis

# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Start Redis
redis-server  # or: brew services start redis

# Update .env
REDIS_URL=redis://localhost:6379/0

# Test connection
redis-cli ping  # Should respond: PONG
```

#### 📧 Email Configuration

**Gmail:**
1. Enable 2-Step Verification on Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Update .env:
   ```bash
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

**SendGrid:**
1. Sign up at https://sendgrid.com
2. Create API key
3. Update .env:
   ```bash
   SMTP_SERVER=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=SG.your_api_key
   ```

**AWS SES:**
1. Set up AWS SES in your region
2. Generate SMTP credentials
3. Update .env:
   ```bash
   SMTP_SERVER=email-smtp.region.amazonaws.com
   SMTP_PORT=587
   SMTP_USER=your-ses-user
   SMTP_PASSWORD=your-ses-password
   ```

### Step 5: Run Deployment Checker

```bash
# Validate everything is configured
python scripts/deployment_checker.py

# Expected output:
# ✅ PASSED: XX
# ❌ FAILED: 0
# ⚠️ WARNINGS: X
# Production Readiness: 90%+
```

### Step 6: Start Application

**Development:**
```bash
uvicorn app_server:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
gunicorn app_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**With PM2 (Recommended):**
```bash
# Install PM2
npm install -g pm2

# Create ecosystem.config.js
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'nexuscrm-api',
    script: './venv/bin/uvicorn',
    args: 'app_server:app --host 0.0.0.0 --port 8000',
    instances: 4,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
EOF

# Start application
pm2 start ecosystem.config.js
pm2 save
```

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
# Build image
docker build -t nexuscrm:latest .

# Run container
docker run -d \
  --name nexuscrm-api \
  -p 8000:8000 \
  --env-file .env \
  nexuscrm:latest

# View logs
docker logs -f nexuscrm-api
```

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f app_server

# Stop services
docker-compose down
```

---

## ☁️ Cloud Deployment

### Railway (Recommended - Easiest)

1. **Connect GitHub**
   - Go to https://railway.app
   - Connect your GitHub account
   - Select `sandrorogeriocosta12-hue/nexucrm` repository

2. **Configure Environment**
   - Add environment variables from `.env`
   - Set `ENVIRONMENT=production`

3. **Enable Auto-Deploy**
   - Push changes to `main` branch
   - Railway automatically builds and deploys

4. **View Logs**
   ```bash
   # CLI
   railway login
   railway status
   railway logs
   ```

### AWS (EC2 + RDS)

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. Connect via SSH
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv postgresql-client

# 4. Clone repository
git clone https://github.com/your-username/nexucrm.git
cd nexucrm

# 5. Setup and deploy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-production.txt

# 6. Create systemd service
sudo tee /etc/systemd/system/nexuscrm.service << 'EOF'
[Unit]
Description=Nexus CRM API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/nexucrm
Environment="PATH=/home/ubuntu/nexucrm/venv/bin"
EnvironmentFile=/home/ubuntu/nexucrm/.env
ExecStart=/home/ubuntu/nexucrm/venv/bin/gunicorn \
  app_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 7. Start service
sudo systemctl daemon-reload
sudo systemctl enable nexuscrm
sudo systemctl start nexuscrm
sudo systemctl status nexuscrm
```

### DigitalOcean (App Platform)

1. Push to GitHub
2. Go to DigitalOcean App Platform
3. Connect GitHub repository
4. Configure:
   - **Dockerfile**: `Dockerfile`
   - **Port**: `8000`
   - **Environment Variables**: Copy from `.env`
5. Deploy!

---

## 📊 Monitoring & Maintenance

### Check Application Health

```bash
# Health check endpoint
curl http://localhost:8000/health
# Response: {"status": "healthy"}

# Detailed status
curl http://localhost:8000/status
# Response: {"status": "healthy", "database": "connected", ...}

# Metrics
curl http://localhost:8000/metrics
```

### View Sentry Errors

```bash
# Go to https://sentry.io
# Select your project
# View errors and performance issues
```

### Database Backup

```bash
# Manual backup
./scripts/backup-db.sh

# Automated backup (add to crontab)
crontab -e
# Add: 0 2 * * * /home/user/nexucrm/scripts/backup-db.sh

# Restore from backup
./scripts/restore-db.sh /path/to/backup.sql.gz
```

### Check Logs

```bash
# Application logs
tail -f /var/log/nexuscrm/app.log

# With Docker
docker logs -f nexuscrm-api

# With PM2
pm2 logs nexuscrm-api
```

---

## ✅ Pre-Deployment Checklist

- [ ] Database configured and accessible
- [ ] All environment variables set in `.env`
- [ ] `python scripts/deployment_checker.py` shows 90%+ readiness
- [ ] Dependencies installed: `pip list | grep fastapi`
- [ ] Email service configured (SMTP credentials valid)
- [ ] Sentry DSN configured (optional but recommended)
- [ ] Redis running (if enabled in .env)
- [ ] SSL certificate obtained (for HTTPS)
- [ ] Domain DNS pointing to your server
- [ ] Firewall allows ports 80, 443
- [ ] Backup scripts tested and working
- [ ] All code committed to GitHub
- [ ] CI/CD pipeline (GitHub Actions) configured

---

## 🚨 Troubleshooting

### Database Connection Failed
```bash
# Check connection string
echo $DATABASE_URL

# Test manually
psql $DATABASE_URL

# Check PostgreSQL is running
psql -V  # Should show version
```

### Email Not Sending
```bash
# Test SMTP configuration
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
print('✅ Email configured correctly')
"
```

### Application Won't Start
```bash
# Check Python version
python --version  # Need Python 3.8+

# Check dependencies
pip list

# Run in foreground to see errors
uvicorn app_server:app --reload

# Check logs
journalctl -u nexuscrm -f  # For systemd
```

### High Memory Usage
```bash
# Reduce workers
gunicorn app_server:app --workers 2

# Set memory limit (Docker)
docker run --memory="512m" nexuscrm:latest
```

---

## 📞 Support & Resources

- **GitHub Issues**: https://github.com/sandrorogeriocosta12-hue/nexucrm/issues
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Sentry Docs**: https://docs.sentry.io/
- **Railway Docs**: https://docs.railway.app/

---

## 🎯 Next Steps

1. **Create Staging Environment**
   - Test all changes before production
   - Mirror production setup

2. **Setup Monitoring**
   - Enable Sentry error tracking
   - Configure uptime monitoring (UptimeRobot)
   - Setup status page (StatusPage.io)

3. **Implement Auto-Scaling**
   - Configure load balancer
   - Enable horizontal scaling
   - Setup auto-backup retention

4. **Security Hardening**
   - Enable WAF (Web Application Firewall)
   - Implement rate limiting
   - Setup DDoS protection
   - Enable audit logging

5. **Documentation**
   - API documentation (/api/docs)
   - Runbooks for common operations
   - Disaster recovery procedures

---

**Last Updated**: 2024
**Version**: 1.0.0
**Maintained By**: Development Team
