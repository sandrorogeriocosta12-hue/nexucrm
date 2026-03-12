#!/bin/bash
# Backup Script para PostgreSQL - Executa diariamente via cron
# Mantém últimos 7 dias de backups

set -e

BACKUP_DIR=/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="vexus_db_$TIMESTAMP.sql"
LOG_FILE="$BACKUP_DIR/backup.log"

# Criar diretório se não existir
mkdir -p "$BACKUP_DIR"

# Função para registrar logs
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_message "=== Iniciando backup do banco de dados ==="

# Executar pg_dump
if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h postgres \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --verbose \
    > "$BACKUP_DIR/$FILENAME" 2>> "$LOG_FILE"; then
    
    log_message "✓ Dump criado: $FILENAME"
    
    # Compactar arquivo
    if gzip "$BACKUP_DIR/$FILENAME"; then
        log_message "✓ Arquivo compactado: ${FILENAME}.gz"
        COMPRESSED_FILE="${FILENAME}.gz"
        COMPRESSED_SIZE=$(du -h "$BACKUP_DIR/$COMPRESSED_FILE" | cut -f1)
        log_message "✓ Tamanho: $COMPRESSED_SIZE"
    else
        log_message "✗ Erro ao compactar: $FILENAME"
        exit 1
    fi
    
    # Remover backups antigos (>7 dias)
    log_message "Removendo backups com mais de 7 dias..."
    find "$BACKUP_DIR" -name "vexus_db_*.sql.gz" -type f -mtime +7 -delete
    log_message "✓ Backups antigos removidos"
    
    # Listar backups disponíveis
    log_message "Backups disponíveis:"
    ls -lh "$BACKUP_DIR"/vexus_db_*.sql.gz | awk '{print "  " $9 " (" $5 ")"}' >> "$LOG_FILE"
    
    log_message "✓ Backup completado com sucesso"
    
else
    log_message "✗ Erro ao executar pg_dump"
    exit 1
fi

log_message "=== Fim do backup ==="
