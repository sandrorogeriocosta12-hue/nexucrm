# ⚡ NEXUS CRM - PERFORMANCE & OTIMIZAÇÃO DE BANCO

## 📊 ÍNDICES CRÍTICOS (Para criar na produção)

```sql
-- Índices para Autenticação e Segurança
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active_created ON users(active, created_at DESC);
CREATE INDEX idx_users_email_verified ON users(email_verified);

-- Índices para Contatos (acesso mais frequente)
CREATE INDEX idx_contacts_user_id ON contacts(user_id);
CREATE INDEX idx_contacts_user_created ON contacts(user_id, created_at DESC);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_phone ON contacts(phone);
CREATE INDEX idx_contacts_status ON contacts(status);

-- Índices para Campanhas
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created ON campaigns(created_at DESC);

-- Índices para Analytics
CREATE INDEX idx_analytics_user_campaign ON analytics(user_id, campaign_id);
CREATE INDEX idx_analytics_date ON analytics(created_at DESC);

-- Índices para Performance
CREATE INDEX idx_webhook_events_type ON webhook_events(event_type);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
```

---

## 🚀 OTIMIZAÇÕES DE QUERY

### 1. N+1 Query Problem

❌ **Problema (N+1 queries)**:
```python
# Ruim - 1 + N queries
campaigns = db.query(Campaign).all()
for campaign in campaigns:
    print(campaign.user.name)  # Query extra para cada linha!
```

✅ **Solução (Eager loading)**:
```python
# Bom - 1 query apenas
campaigns = db.query(Campaign).options(
    joinedload(Campaign.user)
).all()

# Ou com selectinload
campaigns = db.query(Campaign).options(
    selectinload(Campaign.user)
).all()
```

### 2. Limitar Resultados

❌ **Problema**:
```python
contacts = db.query(Contact).all()  # Traz TODOS os contatos!
```

✅ **Solução**:
```python
# Usar paginação
skip = (page - 1) * per_page
contacts = db.query(Contact).offset(skip).limit(per_page).all()
```

### 3. Select Apenas Colunas Necessárias

❌ **Problema**:
```python
users = db.query(User).all()  # Traz tudo: password hash, tokens, etc
```

✅ **Solução**:
```python
users = db.query(User.id, User.name, User.email).all()
```

---

## 💾 OTIMIZAÇÕES DE BANCO

### 1. Connection Pooling

```python
# app_server.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Conexões ativas
    max_overflow=10,       # Conexões extras se necessário
    pool_recycle=3600,     # Reciclar a cada 1 hora
    pool_pre_ping=True,    # Verificar conexão antes de usar
)
```

### 2. Connection Reuse

```python
# Usar context manager
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

with SessionLocal() as session:
    users = session.query(User).all()
    # Conexão retorna ao pool automatically
```

### 3. Query Timeout

```python
# Prevenir queries muito longas
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET statement_timeout TO '30s'")  # PostgreSQL
    cursor.close()
```

---

## 🔄 CACHING COM REDIS

```python
from redis import Redis
from functools import wraps
import json

redis_client = Redis.from_url(REDIS_URL)

def cache(ttl: int = 3600):
    """Decorator para cache de funções"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave de cache
            key = f"{func.__name__}:{args}:{kwargs}"
            
            # Verificar cache
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # Executar função
            result = await func(*args, **kwargs)
            
            # Armazenar em cache
            redis_client.setex(key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Uso
@cache(ttl=3600)
async def get_all_campaigns(user_id: str):
    return db.query(Campaign).filter_by(user_id=user_id).all()
```

---

## 📈 MONITORAMENTO DE PERFORMANCE

### Métricas a Rastrear

```python
import time
from sqlalchemy import event

# Log de queries lentas
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Alertar se query lenta (> 100ms)
    if total_time > 0.1:
        logger.warning(f"⚠️ Slow query ({total_time*1000:.0f}ms): {statement}")
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

# Métricas
db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration')
cache_hits = Counter('cache_hits_total', 'Cache hits')
cache_misses = Counter('cache_misses_total', 'Cache misses')

# Uso
@db_query_duration.time()
async def get_user(user_id: str):
    return db.query(User).get(user_id)
```

---

## ⚡ OTIMIZAÇÕES DE API

### 1. Compressão de Resposta

```python
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

### 2. Async Everywhere

```python
# Ruim - bloqueante
@app.get("/users")
def get_users():
    return db.query(User).all()

# Bom - assíncrono
@app.get("/users")
async def get_users():
    return await async_db.query(User).all()
```

### 3. Batch Operations

```python
# Ruim - N queries
for user_id in user_ids:
    user = db.query(User).get(user_id)
    update_user(user)

# Bom - 1 query
users = db.query(User).filter(User.id.in_(user_ids)).all()
for user in users:
    update_user(user)
```

---

## 🧪 TESTES DE PERFORMANCE

### Load Test com K6

```javascript
// tests/load-test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 50,           // 50 usuários simultâneos
  duration: '5m',    // 5 minutos
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% < 200ms
    http_req_failed: ['<1%'],          // < 1% falhas
  },
};

export default function() {
  let response = http.get('https://api.nexuscrm.tech/api/contacts');
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
}
```

### Executar teste

```bash
k6 run tests/load-test.js

# Com profile customizado
k6 run tests/load-test.js --vus 100 --duration 10m
```

---

## 🔍 IDENTIFYING BOTTLENECKS

### Slow Query Log

```sql
-- PostgreSQL
SET log_min_duration_statement = 100;  -- Log queries > 100ms

-- Ver log
SELECT * FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

### Database Statistics

```sql
-- Verificar índices não utilizados
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Tamanho de tabelas
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename) DESC;
```

---

## 🚀 CHECKLIST DE PERFORMANCE

- [ ] Todos os campos com índices apropriados
- [ ] Queries com EXPLAIN ANALYZE revisadas
- [ ] Connection pooling configurado
- [ ] Caching ativo para dados frequentes
- [ ] Compressão de resposta habilitada
- [ ] Async/await em todos endpoints
- [ ] Paginação em listas grandes
- [ ] Rate limiting ativo
- [ ] Load test passando com < 200ms p95
- [ ] Monitoramento de slow queries ativo
- [ ] Memory leaks não detectados
- [ ] CPU médio < 50% em produção

---

## 📊 RESULTADO ESPERADO

Após aplicar otimizações:

```
Antes:
  Latência P95: 800ms
  Throughput: 10 req/s
  Erros: 5%

Depois:
  Latência P95: 150ms ⚡
  Throughput: 100 req/s ⚡
  Erros: < 0.1% ⚡
  
Melhoria: 5x mais rápido! 🚀
```

