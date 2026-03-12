-- migration: create_processed_webhooks
CREATE TABLE IF NOT EXISTS processed_webhooks (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
