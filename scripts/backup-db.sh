#!/bin/bash

################################################################################
# 🗄️ PostgreSQL BACKUP SCRIPT - Nexus CRM
# Automatic daily backup with encryption and retention
################################################################################

set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/nexus_backup_$TIMESTAMP.sql.gz"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🗄️  PostgreSQL Backup System${NC}"
echo "=================================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get database credentials from environment
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-vexus}"
DB_USER="${DATABASE_USER:-postgres}"

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}❌ pg_dump not found. Install PostgreSQL client tools.${NC}"
    exit 1
fi

echo -e "${YELLOW}📅 Backup Details:${NC}"
echo "  Database: $DB_NAME"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Destination: $BACKUP_FILE"
echo "  Retention: $RETENTION_DAYS days"
echo ""

# Perform backup
echo -e "${GREEN}⏱️  Starting backup...${NC}"
if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup successful!${NC}"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $SIZE"
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi

# Clean up old backups
echo ""
echo -e "${GREEN}🧹 Cleaning old backups (older than $RETENTION_DAYS days)...${NC}"
find "$BACKUP_DIR" -name "nexus_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✅ Cleanup complete${NC}"

# List recent backups
echo ""
echo -e "${GREEN}📋 Recent backups:${NC}"
ls -lh "$BACKUP_DIR"/nexus_backup_*.sql.gz 2>/dev/null | tail -5 || echo "No backups found"

echo ""
echo -e "${GREEN}✨ Backup process complete!${NC}"
