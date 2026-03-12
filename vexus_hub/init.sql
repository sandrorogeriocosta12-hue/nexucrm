-- Vexus IA Database Initialization
-- This file is executed when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database (if not exists)
-- Note: This is handled by docker-compose environment variables

-- Set timezone
SET timezone = 'America/Sao_Paulo';

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we can add some basic ones here

-- Example indexes (will be created by migrations)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_date ON appointments(scheduled_date);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_status ON appointments(status);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_platform ON conversations(platform);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_phone ON patients(phone);

-- Create a function for updating updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a function to get current timestamp in milliseconds
CREATE OR REPLACE FUNCTION current_timestamp_ms()
RETURNS BIGINT AS $$
BEGIN
    RETURN EXTRACT(epoch FROM CURRENT_TIMESTAMP)::BIGINT * 1000;
END;
$$ LANGUAGE plpgsql;

-- Create a function to calculate age from birth_date
CREATE OR REPLACE FUNCTION calculate_age(birth_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(birth_date));
END;
$$ LANGUAGE plpgsql;

-- Create a view for appointment statistics
CREATE OR REPLACE VIEW appointment_stats AS
SELECT
    DATE_TRUNC('month', scheduled_date) AS month,
    COUNT(*) AS total_appointments,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_appointments,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_appointments,
    COUNT(*) FILTER (WHERE status = 'no_show') AS no_show_appointments,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completed')::DECIMAL /
        NULLIF(COUNT(*), 0) * 100, 2
    ) AS completion_rate
FROM appointments
WHERE scheduled_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', scheduled_date)
ORDER BY month DESC;

-- Create a view for clinic performance
CREATE OR REPLACE VIEW clinic_performance AS
SELECT
    c.id,
    c.name,
    COUNT(a.id) AS total_appointments,
    COUNT(a.id) FILTER (WHERE a.status = 'completed') AS completed_appointments,
    COUNT(a.id) FILTER (WHERE a.status = 'no_show') AS no_show_count,
    AVG(s.price) FILTER (WHERE a.status IN ('scheduled', 'confirmed', 'completed')) AS avg_revenue,
    ROUND(
        COUNT(a.id) FILTER (WHERE a.status = 'no_show')::DECIMAL /
        NULLIF(COUNT(a.id), 0) * 100, 2
    ) AS no_show_rate
FROM clinics c
LEFT JOIN appointments a ON c.id = a.clinic_id
LEFT JOIN services s ON a.service_id = s.id
WHERE a.scheduled_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY c.id, c.name;

-- Create a view for conversation analytics
CREATE OR REPLACE VIEW conversation_analytics AS
SELECT
    DATE_TRUNC('day', created_at) AS date,
    platform,
    COUNT(*) AS total_messages,
    COUNT(*) FILTER (WHERE intent IS NOT NULL) AS with_intent,
    COUNT(*) FILTER (WHERE processed_by_ai = true) AS ai_processed,
    ROUND(
        COUNT(*) FILTER (WHERE processed_by_ai = true)::DECIMAL /
        NULLIF(COUNT(*), 0) * 100, 2
    ) AS ai_processing_rate
FROM conversations
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at), platform
ORDER BY date DESC, platform;

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON appointment_stats TO readonly_user;
-- GRANT SELECT ON clinic_performance TO readonly_user;
-- GRANT SELECT ON conversation_analytics TO readonly_user;

-- Create a trigger function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_row JSONB;
    new_row JSONB;
    changes JSONB;
BEGIN
    -- Convert rows to JSONB
    old_row := to_jsonb(OLD);
    new_row := to_jsonb(NEW);

    -- Calculate changes
    changes := jsonb_object_agg(key, jsonb_build_array(old_row->key, new_row->key))
    FROM jsonb_object_keys(new_row) AS key
    WHERE old_row->key IS DISTINCT FROM new_row->key;

    -- Insert audit log
    INSERT INTO audit_logs (
        table_name,
        record_id,
        operation,
        old_values,
        new_values,
        changes,
        user_id,
        created_at
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE WHEN TG_OP != 'INSERT' THEN old_row ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN new_row ELSE NULL END,
        changes,
        NULL, -- Will be set by application
        CURRENT_TIMESTAMP
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Note: Audit triggers will be created by Alembic migrations for each table

-- Create a function to clean old data
CREATE OR REPLACE FUNCTION clean_old_data(days_old INTEGER DEFAULT 90)
RETURNS TABLE(
    conversations_deleted BIGINT,
    notifications_deleted BIGINT,
    audit_logs_deleted BIGINT
) AS $$
DECLARE
    cutoff_date TIMESTAMP;
BEGIN
    cutoff_date := CURRENT_TIMESTAMP - INTERVAL '1 day' * days_old;

    -- Delete old conversations
    DELETE FROM conversations WHERE created_at < cutoff_date;
    GET DIAGNOSTICS conversations_deleted = ROW_COUNT;

    -- Delete old notifications
    DELETE FROM notifications WHERE sent_at < cutoff_date;
    GET DIAGNOSTICS notifications_deleted = ROW_COUNT;

    -- Delete old audit logs (keep for 1 year)
    DELETE FROM audit_logs WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '365 days');
    GET DIAGNOSTICS audit_logs_deleted = ROW_COUNT;

    RETURN QUERY SELECT conversations_deleted, notifications_deleted, audit_logs_deleted;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_scheduled_date ON appointments(scheduled_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Vacuum and analyze for optimization
VACUUM ANALYZE;