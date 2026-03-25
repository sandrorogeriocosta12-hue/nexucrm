#!/bin/bash

################################################################################
# 📊 SLA & UPTIME MONITORING SETUP
# Configure Uptime Robot, StatusPage, and monitoring
################################################################################

cat > /tmp/sla_config.md << 'EOF'
# 🏆 SLA & UPTIME MONITORING - Nexus CRM

## ✅ IMPLEMENTED MONITORING

### 1. Application Health Checks
- ✅ `/health` - Simple health endpoint (for load balancers)
- ✅ `/status` - Detailed status with service health
- ✅ `/metrics` - Performance metrics

### 2. Structured Logging
- ✅ JSON logging for log aggregation
- ✅ Sentry integration for error tracking
- ✅ Request/Response logging

### 3. Database Monitoring
- ✅ Connection health checks
- ✅ Automatic backup scripts
- ✅ Disaster recovery procedures

---

## 📈 SLA TARGETS

```
Service Level Agreement (SLA):
├── Availability:       99.9% (max 43 min downtime/month)
├── Response Time:      <200ms p95
├── Error Rate:         <0.1%
├── MTTR (Mean Time):   <15 minutes
└── RPO (Recovery):     <1 hour
```

---

## 🔧 NEXT STEPS - MONITORING SETUP

### Step 1: Enable Sentry (5 minutes)
1. Sign up at https://sentry.io
2. Create project for Python/FastAPI
3. Copy DSN
4. Set environment variable:
   ```bash
   export SENTRY_DSN="https://your-key@sentry.io/project-id"
   ```

### Step 2: Setup Uptime Monitoring (10 minutes)
1. Sign up at https://uptimerobot.com
2. Add monitor for:
   - https://api.nexuscrm.tech/health (every 5 min)
   - https://api.nexuscrm.tech/status (every 15 min)
3. Set alerts to your email

### Step 3: Configure StatusPage (10 minutes)
1. Sign up at https://www.statuspage.io
2. Create status page for api.nexuscrm.tech
3. Add components:
   - API Server
   - Database
   - CDN (Cloudflare)
4. Integrate with incidents

### Step 4: Setup Log Aggregation (15 minutes)
Option A - Datadog (Recommended)
```bash
pip install --upgrade datadog
export DD_API_KEY="your_key"
export DD_SITE="datadoghq.com"
```

Option B - Elastic Stack
```bash
docker-compose up -d elasticsearch kibana
# Ship logs to ELK
```

---

## 📊 MONITORING DASHBOARDS

### Prometheus Metrics (Built-in)
Endpoint: `https://api.nexuscrm.tech/metrics`
Metrics exported:
- uptime_seconds
- requests_total
- response_time_ms
- errors_total

### Grafana Dashboard
1. Connect Prometheus data source
2. Import dashboard from: https://grafana.com/dashboards
3. Setup alerts for:
   - High error rate (>1%)
   - High latency (>500ms p95)
   - Database connection failures

---

## 🚨 ALERTING RULES

```yaml
Alerts:
  - name: HighErrorRate
    condition: error_rate > 1%
    action: PagerDuty, Email, Slack
  
  - name: HighLatency
    condition: response_time_p95 > 500ms
    action: Slack notification
  
  - name: DatabaseDown
    condition: db_connection_failed
    action: PagerDuty, SMS
  
  - name: DiskSpaceLow
    condition: disk_usage > 85%
    action: Email notification
```

---

## 📞 INCIDENT RESPONSE

### On-Call Schedule
- Primary: Victor Emanuel
- Secondary: [Team member]
- Tertiary: [Team member]

### Escalation Policy
1. Alert sent to on-call (5 min timeout)
2. Alert escalated to primary (10 min timeout)
3. Alert escalated to manager (15 min timeout)

### MTTR Target
- **15 minutes** for critical incidents
- **1 hour** for major incidents
- **4 hours** for minor incidents

---

## ✅ MONTHLY REVIEW

Every 1st of month:
- [ ] Review error logs in Sentry
- [ ] Analyze performance metrics
- [ ] Check backup retention
- [ ] Update incident logs
- [ ] Meet with team for retrospective

EOF

cat /tmp/sla_config.md
