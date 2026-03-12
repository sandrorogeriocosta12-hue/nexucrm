-- Initialize PostgreSQL database with pgvector extension and tables

-- Create extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leads/Contacts table
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    company VARCHAR(255),
    score INTEGER DEFAULT 0,
    stage VARCHAR(100) DEFAULT 'novo',
    source VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    lead_id INTEGER REFERENCES leads(id),
    content TEXT NOT NULL,
    sender VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge base documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proposals table
CREATE TABLE IF NOT EXISTS proposals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    lead_id INTEGER REFERENCES leads(id),
    template VARCHAR(100),
    content TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP
);

-- Agents configuration table
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    model VARCHAR(100) DEFAULT 'GPT-4',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2048,
    auto_response BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    metric_name VARCHAR(255),
    metric_value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_leads_user_id ON leads(user_id);
CREATE INDEX idx_leads_score ON leads(score);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_lead_id ON messages(lead_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_proposals_user_id ON proposals(user_id);
CREATE INDEX idx_agents_user_id ON agents(user_id);

-- Insert demo user
INSERT INTO users (email, password_hash, name, role) VALUES
('admin@vexus.com', '$2b$12$R9h7cIPz0gi.URNNVWG4uu3g8gPKA4sJbxC0vZPvGQu/Ypz8WVE9.', 'Admin Vexus', 'admin');

-- Insert demo leads
INSERT INTO leads (user_id, name, email, phone, company, score, stage, source) VALUES
(1, 'João Silva', 'joao@example.com', '(11) 99999-9999', 'TechFlow Solutions', 85, 'Negociação', 'WhatsApp'),
(1, 'Maria Santos', 'maria@example.com', '(11) 98888-8888', 'Inovação Tech', 75, 'Proposta', 'LinkedIn'),
(1, 'Carlos Mendes', 'carlos@example.com', '(11) 97777-7777', 'Data Solutions', 62, 'Qualificação', 'Website');

-- Insert demo agents
INSERT INTO agents (user_id, name, model, temperature, max_tokens, auto_response) VALUES
(1, 'Agente Vendas', 'GPT-4', 0.7, 2048, TRUE),
(1, 'Agente Knowledge', 'GPT-4', 0.5, 1536, TRUE),
(1, 'Agente Email', 'GPT-3.5-turbo', 0.6, 1024, TRUE);
