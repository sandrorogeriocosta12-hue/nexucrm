#!/bin/bash

################################################################################
# 🔄 PostgreSQL RESTORE SCRIPT - Nexus CRM Disaster Recovery
# Restore database from backup file
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/nexus_backup_20240325_143000.sql.gz"
    exit 1
}

if [ $# -ne 1 ]; then
    usage
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Get database credentials
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-vexus}"
DB_USER="${DATABASE_USER:-postgres}"

echo -e "${YELLOW}⚠️  DATABASE RESTORE WARNING!${NC}"
echo "=================================================="
echo "This will restore the database from:"
echo "  File: $BACKUP_FILE"
echo "  Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""
echo "Database: $DB_NAME at $DB_HOST:$DB_PORT"
echo ""
echo -e "${RED}⚠️  All existing data will be replaced!${NC}"
read -p "Type 'YES' to proceed: " -r confirm

if [ "$confirm" != "YES" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}🔄 Starting restore...${NC}"

if gunzip < "$BACKUP_FILE" | psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"; then
    echo -e "${GREEN}✅ Restore successful!${NC}"
    echo "Database restored from: $BACKUP_FILE"
else
    echo -e "${RED}❌ Restore failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✨ Database restore complete!${NC}"
