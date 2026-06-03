"""
FastAPI main application with routers.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.authentication import AuthCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import os
import re
import time
import logging
logger = logging.getLogger(__name__)

# ── Simple in-memory TTL cache ──────────────────────────────────────────────
_cache: dict = {}
def _cache_get(key: str):
    entry = _cache.get(key)
    return entry["v"] if entry and time.time() < entry["exp"] else None

def _cache_set(key: str, value, ttl: int = 30):
    _cache[key] = {"v": value, "exp": time.time() + ttl}

def _cache_del(key: str):
    _cache.pop(key, None)

# ── Connection Pools ─────────────────────────────────────────────────────────
import psycopg2
from psycopg2 import pool as _pg_pool

_CRM_DSN = os.getenv("DATABASE_URL", "postgresql://vexus:vexus_password_123@localhost/vexus_crm")
_EVO_DSN = os.getenv("EVOLUTION_DB_URL", "postgresql://vexus:vexus_password_123@localhost/vexus_crm")

_crm_pool = None  # type: Optional[_pg_pool.ThreadedConnectionPool]
_evo_pool = None  # type: Optional[_pg_pool.ThreadedConnectionPool]

def _get_crm_pool() -> _pg_pool.ThreadedConnectionPool:
    global _crm_pool
    if _crm_pool is None:
        _crm_pool = _pg_pool.ThreadedConnectionPool(2, 10, _CRM_DSN)
    return _crm_pool

def _get_evo_pool() -> _pg_pool.ThreadedConnectionPool:
    global _evo_pool
    if _evo_pool is None:
        _evo_pool = _pg_pool.ThreadedConnectionPool(2, 8, _EVO_DSN)
    return _evo_pool

class _PooledConn:
    """Wrapper: makes pool.putconn() transparent via .close()"""
    __slots__ = ("_pool", "_conn")
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn
    def __getattr__(self, name):
        return getattr(self._conn, name)
    def __setattr__(self, name, value):
        if name in ("_pool", "_conn"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._conn, name, value)
    def close(self):
        try:
            self._conn.rollback()
        except Exception:
            pass
        self._pool.putconn(self._conn)

def _crm_conn() -> _PooledConn:
    p = _get_crm_pool()
    return _PooledConn(p, p.getconn())

def _evo_conn_pool() -> _PooledConn:
    p = _get_evo_pool()
    return _PooledConn(p, p.getconn())

# Persistência real via PostgreSQL
try:
    from app.db_users import init_db, get_user, create_user, update_password, user_exists, count_users
    _DB_AVAILABLE = True
except Exception as _db_err:
    _DB_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"DB unavailable, using in-memory fallback: {_db_err}")

from app.core.auth import (
    create_tokens,
    verify_token,
    get_password_hash,
    verify_password,
    Token,
    TokenData,
)
from app.core.auth import (
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_invite_token,
    verify_invite_token,
)
from app.core.email import (
    send_email,
    template_verify_email,
    template_password_reset,
    template_invite,
)

# from app.core.stripe import create_checkout_session, handle_webhook  # Optional integration

# fuzzy system router will be imported below to avoid circular import
from app.api.fuzzy import router as fuzzy_router

app = FastAPI(
    title="Vexus CRM", description="Sistema de CRM Automático com IA", version="2.0.0"
)

# include fuzzy router
app.include_router(fuzzy_router)


@app.on_event("startup")
async def startup_event():
    if _DB_AVAILABLE:
        try:
            init_db()
        except Exception as _e:
            logging.getLogger(__name__).warning(f"init_db failed: {_e}")
    for _fn in [
        _ensure_campaigns_table,
        _ensure_contacts_table,
        _ensure_workflows_table,
        _ensure_whatsapp_instances_table,
        _ensure_quick_replies_table,
        _ensure_kanban_tables,
        _ensure_sales_goals_table,
    ]:
        try:
            _fn()
        except Exception as _e:
            logging.getLogger(__name__).warning(f"{_fn.__name__} failed: {_e}")


@app.api_route("/api/admin/init-db", methods=["GET", "POST"], include_in_schema=False)
async def admin_init_db(secret: str = ""):
    """Força re-inicialização das tabelas. Protegido por secret env."""
    expected = os.getenv("ADMIN_INIT_SECRET", "nexus_init_2026")
    if secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    results = {}
    if _DB_AVAILABLE:
        try:
            init_db()
            results["init_db"] = "ok"
        except Exception as e:
            results["init_db"] = str(e)
    for fn in [_ensure_campaigns_table, _ensure_contacts_table, _ensure_workflows_table,
               _ensure_whatsapp_instances_table, _ensure_quick_replies_table,
               _ensure_kanban_tables, _ensure_sales_goals_table]:
        try:
            fn()
            results[fn.__name__] = "ok"
        except Exception as e:
            results[fn.__name__] = str(e)
    return results

# CORS - Allow both backend (8080) and frontend (8081) ports
default_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
]
cors_origins = os.getenv("CORS_ORIGINS", ",".join(default_origins)).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Schemas =====
class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    company: Optional[str] = ""
    ramo_empresa: Optional[str] = ""
    objetivo_ia: Optional[str] = ""
    tom_de_voz: Optional[str] = ""
    plan: Optional[str] = "trial"


class ChatMessage(BaseModel):
    content: str
    sender: str = "user"
    timestamp: Optional[datetime] = None


class KBQuery(BaseModel):
    query: str
    top_k: int = 5


class ProposalRequest(BaseModel):
    lead_id: int
    template: str = "basic"


class AgentConfig(BaseModel):
    name: str
    model: str
    temperature: float
    max_tokens: int
    auto_response: bool = True


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class PaymentRequest(BaseModel):
    plan: str
    payment_method: str
    email: str
    whatsapp: Optional[str] = None
    contact_preference_email: bool = True
    contact_preference_whatsapp: bool = False
    card_name: Optional[str] = None
    card_number: Optional[str] = None
    card_cvv: Optional[str] = None
    cnpj: Optional[str] = None
    company: Optional[str] = None


# ===== In-Memory fallback (usado só se DB indisponível) =====
mock_users: dict = {}

def _get_user(email: str) -> dict | None:
    if _DB_AVAILABLE:
        return get_user(email)
    return mock_users.get(email)

_PWD_RE = re.compile(r'^(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}$')

def _validate_password_strength(password: str):
    if not _PWD_RE.match(password):
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter mínimo 8 caracteres, pelo menos 1 letra maiúscula, 1 número e 1 caractere especial (@#$%& etc.)"
        )

def _user_exists(email: str) -> bool:
    if _DB_AVAILABLE:
        return user_exists(email)
    return email in mock_users

def _create_user(email: str, password_hash: str, name: str = "", company: str = "",
                 role: str = "user", ramo_empresa: str = "", objetivo_ia: str = "",
                 tom_de_voz: str = "", plan: str = "trial") -> dict:
    if _DB_AVAILABLE:
        return create_user(email=email, password_hash=password_hash, name=name, company=company,
                           role=role, ramo_empresa=ramo_empresa, objetivo_ia=objetivo_ia,
                           tom_de_voz=tom_de_voz, plan=plan)
    uid = len(mock_users) + 1
    user = {"id": uid, "email": email, "password_hash": password_hash, "name": name,
            "company": company, "role": role, "plan": plan}
    mock_users[email] = user
    return user

def _update_password(email: str, new_hash: str) -> bool:
    if _DB_AVAILABLE:
        return update_password(email, new_hash)
    user = mock_users.get(email)
    if user:
        user["password_hash"] = new_hash
        return True
    return False

mock_companies: dict = {}
mock_subscriptions: dict = {}
mock_chats: dict = {}
mock_leads: dict = {}
mock_proposals: dict = {}

# All CRM data now in PostgreSQL (leads, campaigns, contacts)

import uuid as _uuid

def _new_id() -> str:
    return str(_uuid.uuid4())[:8]


# ===== Dependencies =====
async def get_current_user(request: Request) -> dict:
    """Extract and verify JWT token from header or cookie.

    Falls back to HttpOnly cookie if Authorization header is missing.
    This allows SPAs to rely solely on cookies for security.
    """
    token = None

    # Check Authorization header first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix

    # Fall back to cookie if no header
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = verify_token(token)
        return {"email": token_data.email, "user_id": token_data.user_id}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _parse_dt(val) -> "datetime | None":
    """Safely parses a trial_ends_at value that may be a datetime, a space-sep string,
    or an ISO string. Returns a naive UTC datetime or None."""
    from datetime import datetime as _dt
    if val is None:
        return None
    if isinstance(val, _dt):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        # Postgres returns "2026-06-09 20:26:36.137928" — Python <3.11 needs 'T'
        return _dt.fromisoformat(val.replace(" ", "T").split("+")[0])
    return None


def _trial_iso(val) -> "str | None":
    """Serialises trial_ends_at to a consistent ISO-8601 string."""
    dt = _parse_dt(val)
    return dt.isoformat() if dt else None


async def check_subscription(current_user: dict = Depends(get_current_user)) -> dict:
    """Blocks access if trial expired and no active paid plan."""
    from datetime import datetime as _dt
    user = _get_user(current_user["email"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    if not user.get("is_active", True):
        raise HTTPException(status_code=402, detail="Conta suspensa. Acesse o painel de cobrança.")
    trial_ends = _parse_dt(user.get("trial_ends_at"))
    plan = user.get("plan", "trial")
    paid_plans = {"starter", "pro", "enterprise", "professional", "business"}
    if trial_ends and plan not in paid_plans:
        if _dt.utcnow() > trial_ends:
            raise HTTPException(
                status_code=402,
                detail="Período de testes encerrado. Escolha um plano para continuar."
            )
    return current_user


# ===== Routes =====


@app.post("/auth/logout")
async def logout():
    """Clear JWT cookies, effectively logging out the session."""
    from fastapi import Response

    resp = Response(content='{"msg": "logged out"}', media_type="application/json")
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/auth/signup", response_model=Token)
async def signup(request: SignupRequest):
    """Sign up new user and set JWT cookies.

    Returns the same body as before for backwards compatibility, but also sets
    ``access_token``/``refresh_token`` cookies so SPA clients can rely on them.
    """
    if _user_exists(request.email):
        raise HTTPException(status_code=400, detail="User already exists")

    _validate_password_strength(request.password)

    user = _create_user(
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name,
        company=request.company or "",
        ramo_empresa=request.ramo_empresa or "",
        objetivo_ia=request.objetivo_ia or "",
        tom_de_voz=request.tom_de_voz or "",
        plan=request.plan or "trial",
    )

    tokens = create_tokens(user["id"], user["email"], user["name"], user["role"])
    # set cookies via response model
    from fastapi import Response

    resp = Response(content=tokens.json(), media_type="application/json")
    resp.set_cookie("access_token", tokens.access_token, httponly=True, samesite="Lax")
    resp.set_cookie(
        "refresh_token", tokens.refresh_token, httponly=True, samesite="Lax"
    )
    return resp


@app.post("/auth/login", response_model=Token)
async def login(request: LoginRequest):
    """Login user, respond with tokens and set HttpOnly cookies."""
    user = _get_user(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tokens = create_tokens(user["id"], user["email"], user["name"], user["role"])
    from fastapi import Response

    resp = Response(content=tokens.json(), media_type="application/json")
    resp.set_cookie("access_token", tokens.access_token, httponly=True, samesite="Lax")
    resp.set_cookie(
        "refresh_token", tokens.refresh_token, httponly=True, samesite="Lax"
    )
    return resp


@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    user = _get_user(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "plan": user.get("plan", "trial"),
        "company": user.get("company", ""),
        "ramo_empresa": user.get("ramo_empresa", ""),
        "objetivo_ia": user.get("objetivo_ia", ""),
        "tom_de_voz": user.get("tom_de_voz", ""),
        "trial_ends_at": _trial_iso(user.get("trial_ends_at")),
        "is_active": user.get("is_active", True),
    }


@app.get("/me/trial")
async def get_trial_status(current_user: dict = Depends(get_current_user)):
    """Returns trial expiry info and days remaining."""
    from datetime import datetime as _dt
    user = _get_user(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    trial_ends = _parse_dt(user.get("trial_ends_at"))
    plan = user.get("plan", "trial")
    paid_plans = {"starter", "pro", "enterprise", "professional", "business"}
    on_paid_plan = plan in paid_plans
    days_left = None
    if trial_ends and not on_paid_plan:
        diff = (trial_ends - _dt.utcnow()).days
        days_left = max(0, diff)
    return {
        "plan": plan,
        "on_paid_plan": on_paid_plan,
        "trial_ends_at": _trial_iso(user.get("trial_ends_at")),
        "days_left": days_left,
        "is_active": user.get("is_active", True),
    }


@app.patch("/me")
async def update_me(payload: dict, current_user: dict = Depends(get_current_user)):
    """Atualiza nome, empresa e telefone do usuário."""
    allowed = {"name", "company", "phone"}
    fields = {k: v for k, v in payload.items() if k in allowed and v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nenhum campo válido")
    try:
        import psycopg2
        from app.db_users import _DB_URL, _SCHEMA
        con = psycopg2.connect(_DB_URL)
        cur = con.cursor()
        set_clause = ", ".join(f"{k} = %s" for k in fields)
        cur.execute(
            f"UPDATE {_SCHEMA}.users SET {set_clause} WHERE email = %s",
            [*fields.values(), current_user["email"]]
        )
        con.commit()
        con.close()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/me/change-password")
async def change_password(payload: dict, current_user: dict = Depends(get_current_user)):
    """Troca a senha do usuário após verificar a senha atual."""
    current_pw = payload.get("current_password", "")
    new_pw     = payload.get("new_password", "")
    if len(new_pw) < 6:
        raise HTTPException(status_code=400, detail="Mínimo 6 caracteres")
    user = _get_user(current_user["email"])
    if not user:
        raise HTTPException(status_code=404)
    if not verify_password(current_pw, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    update_password(current_user["email"], get_password_hash(new_pw))
    return {"ok": True}


@app.post("/billing/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """Cancela assinatura — downgrade para trial."""
    try:
        import psycopg2
        from app.db_users import _DB_URL, _SCHEMA
        con = psycopg2.connect(_DB_URL)
        cur = con.cursor()
        cur.execute(f"UPDATE {_SCHEMA}.users SET plan = 'trial' WHERE email = %s", (current_user["email"],))
        con.commit()
        con.close()
        _cache_del(f"metrics:{current_user['email']}")
        return {"ok": True, "message": "Assinatura cancelada. Plano revertido para Trial."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verify-email")
async def verify_email(token: str):
    """Verify an email verification token."""
    email = verify_email_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = _get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {"msg": "E-mail verificado com sucesso"}


@app.post("/resend-verification")
async def resend_verification(current_user: dict = Depends(get_current_user)):
    """Resend email verification to current user."""
    user = _get_user(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="E-mail já verificado")

    token = create_email_verification_token(user["email"])
    link = f"https://{os.getenv('DOMAIN','localhost')}/verify-email?token={token}"
    html = template_verify_email(link)
    await send_email(to=[user["email"]], subject="Verifique seu e-mail", html=html)
    return {"msg": "E‑mail de verificação reenviado"}


@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Initiate password reset flow."""
    email = req.email
    user = _get_user(email)
    if not user:
        return {"msg": "Se o e‑mail estiver cadastrado, você receberá um link"}

    token = create_password_reset_token(email)
    link = f"https://{os.getenv('DOMAIN','api.nexuscrm.tech')}/reset-password?token={token}"

    # Tenta envio via módulo de email (SendGrid/Resend/SMTP)
    sent = False
    try:
        html = template_password_reset(link)
        sent = await send_email(to=[email], subject="Redefinição de senha - Nexus CRM", html=html)
    except Exception:
        pass

    # Fallback: Gmail SMTP direto quando nenhum provedor configurado
    if not sent:
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASSWORD", "")
        if smtp_user and smtp_pass:
            try:
                import smtplib, ssl
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                msg = MIMEMultipart("alternative")
                msg["Subject"] = "Redefinição de senha - Nexus CRM"
                msg["From"]    = f"Nexus CRM <{smtp_user}>"
                msg["To"]      = email
                msg.attach(MIMEText(f"Acesse o link para redefinir sua senha:\n\n{link}\n\nO link expira em 1 hora.", "plain"))
                msg.attach(MIMEText(template_password_reset(link), "html"))
                ctx = ssl.create_default_context()
                with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587"))) as srv:
                    srv.ehlo()
                    srv.starttls(context=ctx)
                    srv.login(smtp_user, smtp_pass)
                    srv.sendmail(smtp_user, email, msg.as_string())
                sent = True
                logger.info(f"✅ Email de reset enviado via SMTP para {email}")
            except Exception as e:
                logger.error(f"❌ SMTP error: {e}")

    if not sent:
        # Sem provedor de email — loga o link para acesso manual se necessário
        print(f"⚠️  Email não enviado. Reset link para {email}: {link}", flush=True)

    return {"msg": "Se o e‑mail estiver cadastrado, você receberá um link"}


@app.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Reset password using token."""
    email = verify_password_reset_token(req.token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = _get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    _validate_password_strength(req.new_password)
    _update_password(email, get_password_hash(req.new_password))
    return {"msg": "Senha redefinida com sucesso"}


@app.post("/company/invite")
async def invite_user(
    email: str, role: str = "member", current_user: dict = Depends(get_current_user)
):
    """Invite a user to current user's company."""
    inviter = _get_user(current_user["email"])
    if not inviter:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    company_id = inviter.get("company_id", f"company_{inviter['id']}")
    # if company does not exist, create minimal
    mock_companies.setdefault(
        company_id,
        {
            "id": company_id,
            "name": f"Company {company_id}",
            "users": [inviter["email"]],
        },
    )

    # If user already exists, do not send invite
    if _user_exists(email):
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")

    token = create_invite_token(email, company_id, role)
    link = f"https://{os.getenv('DOMAIN','localhost')}/accept-invite?token={token}"
    html = template_invite(mock_companies[company_id]["name"], link)
    await send_email(to=[email], subject="Convite para Vexus CRM", html=html)
    return {"msg": "Convite enviado"}


@app.post("/company/accept-invite")
async def accept_invite(token: str, password: str):
    """Accept invite and create user linked to company."""
    payload = verify_invite_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Convite inválido ou expirado")

    email = payload["email"]
    if _user_exists(email):
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")

    user = _create_user(
        email=email,
        password_hash=get_password_hash(password),
        name=email.split("@")[0],
        role=payload.get("role", "member"),
    )
    # add to company
    comp = mock_companies.setdefault(
        payload.get("company_id"),
        {"id": payload.get("company_id"), "name": "Company", "users": []},
    )
    comp.setdefault("users", []).append(email)
    return {
        "msg": "Usuário criado com sucesso",
        "user": {"email": email, "company_id": payload.get("company_id")},
    }


@app.post("/billing/create-subscription")
async def create_subscription(
    price_id: str, current_user: dict = Depends(get_current_user)
):
    """Create a Stripe checkout session for the current user's company."""
    user = _get_user(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    company_id = user.get("company_id")
    if not company_id:
        # create company for user
        company_id = f"company_{user['id']}"
        mock_companies.setdefault(
            company_id,
            {
                "id": company_id,
                "name": f"Company {company_id}",
                "users": [user["email"]],
            },
        )
        user["company_id"] = company_id

    success_url = f"https://{os.getenv('DOMAIN','localhost')}/dashboard?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"https://{os.getenv('DOMAIN','localhost')}/planos"
    checkout_url = await create_checkout_session(
        customer_email=user["email"],
        price_id=price_id,
        company_id=company_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    if not checkout_url:
        raise HTTPException(status_code=500, detail="Erro ao criar sessão de checkout")
    return {"checkout_url": checkout_url}


@app.post("/billing/stripe-webhook")
async def stripe_webhook(request: dict):
    """Endpoint to receive Stripe webhooks (expects raw body in production)."""
    # In this mock environment, expect a dict with payload and signature
    payload = request.get("payload")
    sig_header = request.get("sig_header")
    result = await handle_webhook(payload, sig_header)
    return result


@app.get("/billing/subscription")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    user = _get_user(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    company_id = user.get("company_id")
    subs = mock_subscriptions.get(company_id)
    return {"subscription": subs}


@app.post("/payment/process")
async def process_payment(request: Request):
    """
    Complete payment processing with contact info and notification
    Expected payload:
    {
        "plan": "starter|professional|premium",
        "payment_method": "card|boleto|pix",
        "email": "user@email.com",
        "whatsapp": "+55 11 99999-9999",
        "contact_preference_email": true/false,
        "contact_preference_whatsapp": true/false,
        "card_name": "João Silva" (if card),
        "card_number": "4532..." (if card),
        "cnpj": "00.000.000/0000-00" (if boleto),
        "company": "Empresa XYZ" (if boleto)
    }
    """
    try:
        data = await request.json()
        print(f"💳 Processing payment with contact info: {data.get('email')}")

        # Validate required fields
        plan = data.get("plan")
        payment_method = data.get("payment_method")
        email = data.get("email", "").strip()
        whatsapp = data.get("whatsapp", "").strip()

        # Validate plan
        valid_plans = ["starter", "professional", "premium"]
        if plan not in valid_plans:
            raise HTTPException(status_code=400, detail=f"Plano inválido: {plan}")

        # Validate payment method
        valid_methods = ["card", "boleto", "pix"]
        if payment_method not in valid_methods:
            raise HTTPException(status_code=400, detail=f"Método inválido: {payment_method}")

        # Validate email
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="Email válido é obrigatório")

        # Validate card if card payment
        if payment_method == "card":
            card_name = data.get("card_name", "").strip()
            card_number = data.get("card_number", "").strip()
            card_cvv = data.get("card_cvv", "").strip()

            if not card_name:
                raise HTTPException(status_code=400, detail="Nome do titular é obrigatório")
            if not card_number or len(card_number) < 13:
                raise HTTPException(status_code=400, detail="Número do cartão inválido")
            if not card_cvv or len(card_cvv) < 3:
                raise HTTPException(status_code=400, detail="CVV inválido")

        # Validate CNPJ if boleto payment
        elif payment_method == "boleto":
            cnpj = data.get("boleto_cnpj") or data.get("cnpj", "")
            cnpj = cnpj.strip()
            cnpj_clean = ''.join(filter(str.isdigit, cnpj))

            if len(cnpj_clean) != 14:
                raise HTTPException(status_code=400, detail="CNPJ deve ter 14 dígitos")

        # Store contact preferences
        contact_by_email = data.get("contact_preference_email", True)
        contact_by_whatsapp = data.get("contact_preference_whatsapp", False)

        # Log the payment
        payment_log = {
            "plan": plan,
            "payment_method": payment_method,
            "email": email,
            "whatsapp": whatsapp if contact_by_whatsapp else None,
            "contact_by_email": contact_by_email,
            "contact_by_whatsapp": contact_by_whatsapp,
            "timestamp": str(datetime.now())
        }

        print(f"💳 Payment Details: {payment_log}")

        # Simulate payment processing
        import asyncio
        await asyncio.sleep(0.5)

        # Send confirmation to customer based on preferences
        notification_message = f"""
        ✅ Pagamento Recebido!

        Plano: {plan.upper()}
        Método: {payment_method.upper()}
        Email: {email}
        Status: ATIVO

        Você receberá em breve um email com os dados de acesso à plataforma.
        """

        print(f"📧 Sending notification to: {email}")
        if contact_by_whatsapp and whatsapp:
            print(f"📱 Also sending WhatsApp to: {whatsapp}")

        # Return success
        return {
            "success": True,
            "message": "Pagamento processado com sucesso!",
            "subscription": {
                "plan": plan,
                "payment_method": payment_method,
                "status": "active",
                "next_billing": "2024-04-30",
                "email": email
            },
            "notification": {
                "email_sent": contact_by_email,
                "whatsapp_sent": contact_by_whatsapp
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Payment processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")


# ===== Chat Routes =====


@app.post("/chat/send")
async def send_message(
    message: ChatMessage, current_user: dict = Depends(get_current_user)
):
    """Send a chat message."""
    if current_user["email"] not in mock_chats:
        mock_chats[current_user["email"]] = []

    msg = {
        "id": len(mock_chats[current_user["email"]]) + 1,
        "content": message.content,
        "sender": message.sender,
        "timestamp": datetime.utcnow(),
    }
    mock_chats[current_user["email"]].append(msg)

    return {"status": "sent", "message": msg}


@app.get("/chat/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    """Get chat history."""
    return mock_chats.get(current_user["email"], [])


# ===== Knowledge Base Routes =====


@app.post("/agents/{agent_id}/files")
async def upload_agent_file(
    agent_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a file to an agent's knowledge base. Stores text content in DB."""
    import psycopg2.extras
    email = current_user["email"]
    raw = await file.read()
    content = ""
    filename = file.filename or "arquivo.txt"
    # Try to decode as text; for PDFs extract what we can without extra deps
    try:
        content = raw.decode("utf-8", errors="replace")
    except Exception:
        content = raw.decode("latin-1", errors="replace")
    # Strip binary noise for non-text files (keep printable + newlines)
    if filename.lower().endswith(".pdf"):
        import re
        content = re.sub(r'[^\x20-\x7E\n\r\tÀ-ɏ]+', ' ', content)
        content = re.sub(r'\s{3,}', '\n', content).strip()
    try:
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id FROM nexus.agents WHERE id=%s AND user_email=%s",
            (agent_id, email)
        )
        if not cur.fetchone():
            con.close()
            raise HTTPException(status_code=404, detail="Agente não encontrado")
        cur.execute(
            """INSERT INTO nexus.agent_files (user_email, agent_id, filename, content, file_size)
               VALUES (%s, %s, %s, %s, %s) RETURNING id, filename, file_size, created_at""",
            (email, agent_id, filename, content[:50000], len(raw))
        )
        row = dict(cur.fetchone())
        con.commit()
        con.close()
        return {"status": "uploaded", "file": row}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/files")
async def list_agent_files(agent_id: int, current_user: dict = Depends(get_current_user)):
    """List files in an agent's knowledge base."""
    import psycopg2.extras
    try:
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, filename, file_size, created_at FROM nexus.agent_files WHERE agent_id=%s AND user_email=%s ORDER BY created_at DESC",
            (agent_id, current_user["email"])
        )
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return {"files": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_id}/files/{file_id}")
async def delete_agent_file(agent_id: int, file_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a file from an agent's knowledge base."""
    import psycopg2.extras
    try:
        con = _agents_conn()
        cur = con.cursor()
        cur.execute(
            "DELETE FROM nexus.agent_files WHERE id=%s AND agent_id=%s AND user_email=%s",
            (file_id, agent_id, current_user["email"])
        )
        con.commit()
        con.close()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kb/upload")
async def upload_document(
    file_name: str, current_user: dict = Depends(get_current_user)
):
    return {"status": "uploaded", "file": file_name, "user": current_user["email"]}


@app.post("/kb/query")
async def query_kb(query: KBQuery, current_user: dict = Depends(get_current_user)):
    return {"query": query.query, "results": []}


# ===== Leads Routes =====

class LeadCreate(BaseModel):
    name: str
    email: str = ""
    company: str = ""
    value: float = 0
    status: str = "Novo"
    notes: str = ""

@app.get("/leads")
async def get_leads(current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    con = _crm_conn()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM nexus.leads WHERE user_email=%s ORDER BY created_at DESC",
        (current_user["email"],)
    )
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

@app.post("/leads")
async def create_lead(lead: LeadCreate, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    con = _crm_conn()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """INSERT INTO nexus.leads (user_email, name, email, company, value, status, notes)
           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
        (current_user["email"], lead.name, lead.email, lead.company,
         lead.value, lead.status, lead.notes)
    )
    row = dict(cur.fetchone())
    con.commit()
    con.close()
    return row

@app.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    con = _crm_conn()
    cur = con.cursor()
    cur.execute(
        "DELETE FROM nexus.leads WHERE id=%s AND user_email=%s",
        (lead_id, current_user["email"])
    )
    con.commit()
    con.close()
    return {"deleted": lead_id}

@app.get("/leads/{lead_id}")
async def get_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    con = _crm_conn()
    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM nexus.leads WHERE id=%s AND user_email=%s",
        (lead_id, current_user["email"])
    )
    row = cur.fetchone()
    con.close()
    if not row:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return dict(row)


# ===== Campaigns Routes =====

class CampaignCreate(BaseModel):
    name: str
    description: str = ""
    budget: float = 0


def _ensure_campaigns_table():
    con = _crm_conn()
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS nexus")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.campaigns (
                id                  VARCHAR(20)  PRIMARY KEY,
                user_email          VARCHAR(255) NOT NULL,
                name                VARCHAR(255) NOT NULL DEFAULT '',
                description         TEXT         DEFAULT '',
                budget              NUMERIC(12,2) DEFAULT 0,
                status              VARCHAR(50)  DEFAULT 'draft',
                message_template    TEXT         DEFAULT '',
                instance_name       VARCHAR(255) DEFAULT '',
                target_type         VARCHAR(50)  DEFAULT 'all_contacts',
                target_stage_id     INTEGER,
                target_manual_jids  TEXT         DEFAULT '',
                sent_count          INTEGER      DEFAULT 0,
                failed_count        INTEGER      DEFAULT 0,
                total_count         INTEGER      DEFAULT 0,
                scheduled_at        TIMESTAMP,
                created_at          TIMESTAMP    DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS campaigns_user_email_idx ON nexus.campaigns(user_email)")
        # Migra tabelas existentes sem as novas colunas (idempotente)
        for col, defn in [
            ("message_template",   "TEXT DEFAULT ''"),
            ("instance_name",      "VARCHAR(255) DEFAULT ''"),
            ("target_type",        "VARCHAR(50) DEFAULT 'all_contacts'"),
            ("target_stage_id",    "INTEGER"),
            ("target_manual_jids", "TEXT DEFAULT ''"),
            ("sent_count",         "INTEGER DEFAULT 0"),
            ("failed_count",       "INTEGER DEFAULT 0"),
            ("total_count",        "INTEGER DEFAULT 0"),
            ("scheduled_at",       "TIMESTAMP"),
        ]:
            try:
                cur.execute(f"ALTER TABLE nexus.campaigns ADD COLUMN IF NOT EXISTS {col} {defn}")
            except Exception:
                pass
    finally:
        con.close()


# ── Motor de Disparo de Campanhas ──────────────────────────────────────────────
import random as _random

_campaign_tasks: dict[str, asyncio.Task] = {}   # campaign_id → Task em execução
_campaign_stop:  set[str]                = set() # campaign_ids pausados/cancelados


async def _run_campaign(campaign_id: str, user_email: str) -> None:
    """Processa o disparo de uma campanha com delay antibanimento (15-30s)."""
    import httpx as _hx
    evo_url = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
    evo_key = os.getenv("EVOLUTION_API_KEY", "")

    try:
        con = _crm_conn()
        cur = con.cursor()
        cur.execute(
            "SELECT name, message_template, instance_name, target_type, target_stage_id, target_manual_jids "
            "FROM nexus.campaigns WHERE id = %s AND user_email = %s",
            (campaign_id, user_email)
        )
        camp = cur.fetchone()
        con.close()
        if not camp:
            return
        c_name, template, instance, target_type, stage_id, manual_jids = camp

        # Resolve lista de JIDs alvo
        jids: list[str] = []
        con2 = _crm_conn()
        cur2 = con2.cursor()
        if target_type == "all_contacts":
            cur2.execute(
                "SELECT COALESCE(whatsapp_jid, CONCAT(phone,'@s.whatsapp.net')) FROM nexus.contacts "
                "WHERE user_email = %s AND (whatsapp_jid IS NOT NULL OR phone IS NOT NULL)",
                (user_email,)
            )
            jids = [r[0] for r in cur2.fetchall() if r[0] and "@" in r[0]]
        elif target_type == "kanban_stage" and stage_id:
            cur2.execute(
                "SELECT contact_jid FROM nexus.deals WHERE stage_id = %s AND user_email = %s AND contact_jid IS NOT NULL",
                (stage_id, user_email)
            )
            jids = [r[0] for r in cur2.fetchall() if r[0]]
        elif target_type == "manual" and manual_jids:
            jids = [j.strip() for j in manual_jids.splitlines() if j.strip() and "@" in j]

        # Busca contatos para personalizar {{nome}}
        cur2.execute(
            "SELECT COALESCE(whatsapp_jid,''), COALESCE(phone,''), name FROM nexus.contacts WHERE user_email = %s",
            (user_email,)
        )
        name_map = {}
        for wjid, phone, cname in cur2.fetchall():
            if wjid: name_map[wjid] = cname
            if phone: name_map[phone + "@s.whatsapp.net"] = cname
        con2.close()

        total = len(jids)
        # Atualiza total e muda status para 'running'
        con3 = _crm_conn()
        cur3 = con3.cursor()
        cur3.execute(
            "UPDATE nexus.campaigns SET total_count=%s, sent_count=0, failed_count=0, status='running' WHERE id=%s AND user_email=%s",
            (total, campaign_id, user_email)
        )
        con3.commit(); con3.close()

        logger.info(f"📢 Campanha [{c_name}] iniciada: {total} destinatários via [{instance}]")

        async with _hx.AsyncClient(timeout=15) as client:
            for jid in jids:
                if campaign_id in _campaign_stop:
                    break
                contact_name = name_map.get(jid, "Cliente")
                number = jid.split("@")[0]
                msg = template.replace("{{nome}}", contact_name).replace("{{name}}", contact_name)
                status_update = "sent_count = sent_count + 1"
                try:
                    r = await client.post(
                        f"{evo_url}/message/sendText/{instance}",
                        headers={"apikey": evo_key, "Content-Type": "application/json"},
                        json={"number": number, "text": msg},
                    )
                    if r.status_code not in (200, 201):
                        status_update = "failed_count = failed_count + 1"
                        logger.warning(f"[Campanha] falha {jid}: {r.status_code}")
                except Exception as e:
                    status_update = "failed_count = failed_count + 1"
                    logger.warning(f"[Campanha] erro {jid}: {e}")

                con4 = _crm_conn()
                cur4 = con4.cursor()
                cur4.execute(
                    f"UPDATE nexus.campaigns SET {status_update} WHERE id=%s AND user_email=%s",
                    (campaign_id, user_email)
                )
                con4.commit(); con4.close()

                # Delay antibanimento: 15-30s aleatório
                delay = _random.uniform(15, 30)
                await asyncio.sleep(delay)

        # Finaliza
        final_status = "paused" if campaign_id in _campaign_stop else "finished"
        _campaign_stop.discard(campaign_id)
        _campaign_tasks.pop(campaign_id, None)
        con5 = _crm_conn()
        cur5 = con5.cursor()
        cur5.execute(
            "UPDATE nexus.campaigns SET status=%s WHERE id=%s AND user_email=%s",
            (final_status, campaign_id, user_email)
        )
        con5.commit(); con5.close()
        logger.info(f"📢 Campanha [{c_name}] finalizada com status '{final_status}'")

    except Exception as e:
        logger.error(f"[Campanha] erro fatal {campaign_id}: {e}")
        _campaign_tasks.pop(campaign_id, None)


@app.get("/campaigns")
async def get_campaigns(current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM nexus.campaigns WHERE user_email = %s ORDER BY created_at DESC",
            (current_user["email"],)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


@app.post("/campaigns")
async def create_campaign(campaign: CampaignCreate, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    new_id = _new_id()
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO nexus.campaigns (id, user_email, name, description, budget)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (new_id, current_user["email"], campaign.name,
             campaign.description or "", campaign.budget or 0)
        )
        row = dict(cur.fetchone())
        con.commit()
        return row
    finally:
        con.close()


@app.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "DELETE FROM nexus.campaigns WHERE id = %s AND user_email = %s",
            (campaign_id, current_user["email"])
        )
        con.commit()
    finally:
        con.close()
    return {"deleted": campaign_id}


class CampaignUpdate(BaseModel):
    name:               Optional[str]   = None
    description:        Optional[str]   = None
    message_template:   Optional[str]   = None
    instance_name:      Optional[str]   = None
    target_type:        Optional[str]   = None
    target_stage_id:    Optional[int]   = None
    target_manual_jids: Optional[str]   = None


@app.put("/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, payload: CampaignUpdate, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    fields = {k: v for k, v in payload.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute(
            f"UPDATE nexus.campaigns SET {set_clause} WHERE id = %s AND user_email = %s RETURNING id",
            list(fields.values()) + [campaign_id, user_email]
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
        con.commit()
        return {"updated": campaign_id}
    except HTTPException:
        raise
    except Exception as e:
        con.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.post("/campaigns/{campaign_id}/start")
async def start_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    if campaign_id in _campaign_tasks and not _campaign_tasks[campaign_id].done():
        raise HTTPException(status_code=409, detail="Campanha já está em execução")
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT message_template, instance_name FROM nexus.campaigns WHERE id=%s AND user_email=%s",
            (campaign_id, user_email)
        )
        row = cur.fetchone()
        con.close()
        if not row:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
        if not row[0] or not row[0].strip():
            raise HTTPException(status_code=400, detail="Defina a mensagem da campanha antes de disparar")
        if not row[1] or not row[1].strip():
            raise HTTPException(status_code=400, detail="Selecione a instância WhatsApp antes de disparar")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    _campaign_stop.discard(campaign_id)
    task = asyncio.create_task(_run_campaign(campaign_id, user_email))
    _campaign_tasks[campaign_id] = task
    return {"started": campaign_id}


@app.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    _campaign_stop.add(campaign_id)
    task = _campaign_tasks.get(campaign_id)
    if task and not task.done():
        return {"paused": campaign_id, "message": "Campanha será pausada após a mensagem atual"}
    return {"paused": campaign_id, "message": "Campanha não estava em execução"}


@app.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: str, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, name, status, sent_count, failed_count, total_count FROM nexus.campaigns WHERE id=%s AND user_email=%s",
            (campaign_id, user_email)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
        data = dict(row)
        data["running"] = campaign_id in _campaign_tasks and not _campaign_tasks[campaign_id].done()
        return data
    finally:
        con.close()


# ===== Contacts Routes =====

class ContactCreate(BaseModel):
    name: str
    email: str = ""
    phone: Optional[str] = None
    company: str = ""
    title: Optional[str] = None


def _contacts_conn():
    return _crm_conn()


def _ensure_contacts_table():
    con = _contacts_conn()
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.contacts (
                id           VARCHAR(20)  PRIMARY KEY,
                user_email   VARCHAR(255) NOT NULL,
                name         VARCHAR(255) NOT NULL DEFAULT '',
                email        VARCHAR(255) DEFAULT '',
                phone        VARCHAR(50)  DEFAULT '',
                company      VARCHAR(255) DEFAULT '',
                title        VARCHAR(255) DEFAULT '',
                source       VARCHAR(50)  DEFAULT 'manual',
                whatsapp_jid VARCHAR(100) DEFAULT '',
                created_at   TIMESTAMP    DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS contacts_user_email_idx ON nexus.contacts(user_email)")
    finally:
        con.close()


@app.get("/contacts")
async def get_contacts(sort: str = "recent", current_user: dict = Depends(get_current_user)):
    """sort: recent | oldest | az"""
    import psycopg2.extras
    order_map = {
        "recent":  "created_at DESC",
        "oldest":  "created_at ASC",
        "az":      "LOWER(name) ASC",
    }
    order = order_map.get(sort, "created_at DESC")
    con = _contacts_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"SELECT * FROM nexus.contacts WHERE user_email = %s ORDER BY {order}",
            (current_user["email"],)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


@app.post("/contacts")
async def create_contact(contact: ContactCreate, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    new_id = _new_id()
    con = _contacts_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO nexus.contacts (id, user_email, name, email, phone, company, title, source)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'manual') RETURNING *""",
            (new_id, current_user["email"], contact.name, contact.email or "",
             contact.phone or "", contact.company or "", contact.title or "")
        )
        row = dict(cur.fetchone())
        con.commit()
        return row
    finally:
        con.close()


@app.post("/contacts/import-whatsapp")
async def import_whatsapp_contacts(current_user: dict = Depends(get_current_user)):
    """Import WhatsApp contacts from Evolution API database into CRM."""
    import psycopg2.extras

    try:
        evo_con = _evo_conn()
        evo_cur = evo_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        evo_cur.execute("""
            SELECT c."remoteJid", c."pushName"
            FROM vexus."Contact" c
            WHERE c."remoteJid" NOT LIKE '%@g.us'
              AND c."pushName" IS NOT NULL
              AND c."pushName" != ''
            LIMIT 2000
        """)
        wa_contacts = evo_cur.fetchall()
        evo_con.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler contatos do WhatsApp: {e}")

    crm_con = _crm_conn()
    crm_cur = crm_con.cursor()
    imported = 0
    skipped = 0
    user_email = current_user["email"]

    for wc in wa_contacts:
        jid = wc["remoteJid"]
        name = wc["pushName"] or ""
        phone = jid.split("@")[0] if "@" in jid else jid
        contact_id = f"wa_{phone}"

        crm_cur.execute(
            "SELECT 1 FROM nexus.contacts WHERE id = %s AND user_email = %s",
            (contact_id, user_email)
        )
        if crm_cur.fetchone():
            skipped += 1
            continue

        crm_cur.execute(
            """INSERT INTO nexus.contacts (id, user_email, name, phone, source, whatsapp_jid)
               VALUES (%s, %s, %s, %s, 'whatsapp', %s)
               ON CONFLICT (id) DO NOTHING""",
            (contact_id, user_email, name, phone, jid)
        )
        imported += 1

    crm_con.commit()
    crm_con.close()
    return {"imported": imported, "skipped": skipped, "total": imported + skipped}


@app.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: dict = Depends(get_current_user)):
    con = _contacts_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "DELETE FROM nexus.contacts WHERE id = %s AND user_email = %s",
            (contact_id, current_user["email"])
        )
        con.commit()
    finally:
        con.close()
    return {"deleted": contact_id}


@app.get("/contacts/export")
async def export_contacts_csv(current_user: dict = Depends(get_current_user)):
    """Exporta contatos em CSV."""
    import csv, io
    from fastapi.responses import StreamingResponse
    con = _contacts_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT name, email, phone, company, title, source, created_at FROM nexus.contacts WHERE user_email = %s ORDER BY name",
            (current_user["email"],)
        )
        rows = cur.fetchall()
    finally:
        con.close()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Nome", "Email", "Telefone", "Empresa", "Cargo", "Origem", "Criado em"])
    for r in rows:
        writer.writerow([r[0] or "", r[1] or "", r[2] or "", r[3] or "", r[4] or "", r[5] or "", str(r[6] or "")])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contatos.csv"},
    )


@app.post("/contacts/import-csv")
async def import_contacts_csv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Importa contatos de CSV com colunas: nome, telefone (obrigatório), email, empresa, cargo."""
    import csv, io, re
    user_email = current_user["email"]
    content = await file.read()
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    def _clean_phone(p: str) -> str:
        digits = re.sub(r"\D", "", p or "")
        if not digits:
            return ""
        if len(digits) < 10:
            return ""
        if not digits.startswith("55") and len(digits) <= 13:
            digits = "55" + digits
        return digits

    imported = updated = rejected = 0
    errors: list[str] = []
    con = _crm_conn()
    cur = con.cursor()

    for i, row in enumerate(reader, start=2):
        name  = (row.get("nome") or row.get("name") or row.get("Nome") or "").strip()
        phone = _clean_phone(row.get("telefone") or row.get("phone") or row.get("Telefone") or "")
        email = (row.get("email") or row.get("Email") or "").strip().lower()
        company = (row.get("empresa") or row.get("company") or row.get("Empresa") or "").strip()
        title   = (row.get("cargo") or row.get("title") or row.get("Cargo") or "").strip()

        if not phone:
            errors.append(f"Linha {i}: telefone inválido")
            rejected += 1
            continue
        if not name:
            name = phone

        contact_id = f"csv_{phone}"
        cur.execute("SELECT id FROM nexus.contacts WHERE user_email = %s AND (id = %s OR phone = %s)", (user_email, contact_id, phone))
        existing = cur.fetchone()
        if existing:
            cur.execute(
                "UPDATE nexus.contacts SET name=%s, email=%s, company=%s, title=%s WHERE id=%s AND user_email=%s",
                (name, email, company, title, existing[0], user_email)
            )
            updated += 1
        else:
            cur.execute(
                "INSERT INTO nexus.contacts (id, user_email, name, phone, email, company, title, source) VALUES (%s,%s,%s,%s,%s,%s,%s,'csv') ON CONFLICT (id) DO NOTHING",
                (contact_id, user_email, name, phone, email, company, title)
            )
            imported += 1

    con.commit()
    con.close()
    return {"imported": imported, "updated": updated, "rejected": rejected, "errors": errors[:20]}


@app.get("/crm/deals/export")
async def export_deals_csv(current_user: dict = Depends(get_current_user)):
    """Exporta deals do pipeline em CSV."""
    import csv, io
    from fastapi.responses import StreamingResponse
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT d.name, ps.name AS stage, d.value, d.status, d.probability, d.close_date,
                   d.assigned_to, d.created_at, d.updated_at
            FROM nexus.deals d
            JOIN nexus.pipeline_stages ps ON ps.id = d.stage_id
            WHERE d.user_email = %s ORDER BY d.updated_at DESC
        """, (user_email,))
        rows = cur.fetchall()
    finally:
        con.close()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Deal", "Estágio", "Valor", "Status", "Probabilidade", "Prev. Fechamento", "Responsável", "Criado", "Atualizado"])
    for r in rows:
        writer.writerow([r["name"], r["stage"], r["value"], r["status"], r["probability"] or "",
                         str(r["close_date"] or ""), r["assigned_to"] or "", str(r["created_at"] or ""), str(r["updated_at"] or "")])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pipeline.csv"},
    )


# ===== Proposals Routes =====


@app.post("/proposals/generate")
async def generate_proposal(
    request: ProposalRequest, current_user: dict = Depends(get_current_user)
):
    """Generate proposal for lead."""
    return {
        "id": 1,
        "lead_id": request.lead_id,
        "template": request.template,
        "content": "Proposta personalizada gerada com sucesso",
        "created_at": datetime.utcnow(),
    }


@app.get("/proposals")
async def get_proposals(current_user: dict = Depends(get_current_user)):
    """Get all proposals."""
    return {
        "proposals": [
            {
                "id": 1,
                "lead_id": 1,
                "status": "enviada",
                "created_at": datetime.utcnow(),
            },
            {
                "id": 2,
                "lead_id": 2,
                "status": "pendente",
                "created_at": datetime.utcnow(),
            },
        ]
    }


# ===== Agents Routes =====

def _agents_conn():
    return _crm_conn()


# ── Gerador de prompt padrão ───────────────────────────────────────────────────

_TONE_MAP = {
    "formal":    "Use linguagem formal, profissional e respeitosa.",
    "amigavel":  "Use linguagem amigável, próxima e descontraída, como um consultor de confiança.",
    "tecnico":   "Use linguagem técnica, precisa e objetiva, sem rodeios.",
    "vendedor":  "Use linguagem entusiasmada, focada em benefícios e com senso de urgência.",
}

_GOAL_MAP = {
    "atendimento": "Seu objetivo principal é resolver dúvidas, orientar o cliente e garantir sua satisfação.",
    "vendas":      "Seu objetivo principal é entender as necessidades do cliente e apresentar soluções que gerem valor, conduzindo-o naturalmente para a compra.",
    "suporte":     "Seu objetivo principal é ajudar a resolver problemas técnicos passo a passo, com paciência e clareza.",
    "agendamento": "Seu objetivo principal é coletar as informações necessárias e agendar atendimentos de forma eficiente.",
}

def generate_default_prompt(company_name: str, niche: str, tone: str, goal: str) -> str:
    tone_text = _TONE_MAP.get(tone, _TONE_MAP["amigavel"])
    goal_text = _GOAL_MAP.get(goal, _GOAL_MAP["atendimento"])
    return (
        f"Você é o assistente virtual da empresa {company_name}, "
        f"atuando no setor de {niche}.\n\n"
        f"{tone_text}\n\n"
        f"{goal_text}\n\n"
        f"Regras importantes:\n"
        f"- Responda sempre em português brasileiro.\n"
        f"- Seja breve e direto nas mensagens de WhatsApp (máximo 3 parágrafos curtos).\n"
        f"- Se não souber a resposta, informe que vai verificar e retornar em breve.\n"
        f"- Nunca invente informações sobre preços, prazos ou condições sem confirmação.\n"
        f"- Finalize sempre oferecendo uma próxima ação concreta ao cliente."
    )


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    persona: Optional[str] = None
    instructions: Optional[str] = None
    active: Optional[bool] = None
    auto_respond: Optional[bool] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    file_search: Optional[bool] = None
    code_interpreter: Optional[bool] = None
    functions_json: Optional[str] = None
    avatar: Optional[str] = None
    work_days: Optional[str] = None
    work_start: Optional[str] = None
    work_end: Optional[str] = None
    away_message: Optional[str] = None


class AgentChatRequest(BaseModel):
    agent_type: str
    message: str
    conversation_history: list = []


@app.get("/agents")
async def get_agents(current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    try:
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM nexus.agents WHERE user_email = %s ORDER BY id",
            (current_user["email"],)
        )
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        # Ensure default agents exist
        if not rows:
            defaults = [
                ("Atendimento", "atendimento", "Assistente cordial de atendimento ao cliente",
                 "Responda de forma educada e objetiva. Se não souber algo, diga que vai verificar."),
                ("Vendas", "vendas", "Consultor de vendas proativo",
                 "Identifique as necessidades do cliente e apresente soluções. Seja persuasivo mas honesto."),
                ("Suporte", "suporte", "Especialista técnico de suporte",
                 "Ajude a resolver problemas técnicos passo a passo. Peça detalhes quando necessário."),
            ]
            con2 = _agents_conn()
            cur2 = con2.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            for name, atype, persona, instructions in defaults:
                cur2.execute(
                    """INSERT INTO nexus.agents (user_email, name, type, persona, instructions)
                       VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_email,type) DO NOTHING RETURNING *""",
                    (current_user["email"], name, atype, persona, instructions)
                )
                row = cur2.fetchone()
                if row:
                    rows.append(dict(row))
            con2.commit()
            con2.close()
        return {"agents": rows}
    except Exception as e:
        return {"agents": [], "error": str(e)}


@app.put("/agents/{agent_id}")
async def update_agent(
    agent_id: int, update: AgentUpdate, current_user: dict = Depends(get_current_user)
):
    import psycopg2.extras
    fields = {k: v for k, v in update.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [agent_id, current_user["email"]]
    try:
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"UPDATE nexus.agents SET {set_clause}, updated_at = NOW() WHERE id = %s AND user_email = %s RETURNING *",
            values
        )
        row = cur.fetchone()
        con.commit()
        con.close()
        if not row:
            raise HTTPException(status_code=404, detail="Agente não encontrado")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Onboarding ─────────────────────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    company_name: str
    niche: str
    tone: str = "amigavel"   # formal | amigavel | tecnico | vendedor
    goal: str = "atendimento"  # atendimento | vendas | suporte | agendamento


@app.post("/agents/onboarding")
async def agent_onboarding(req: OnboardingRequest, current_user: dict = Depends(get_current_user)):
    """
    Recebe o perfil da empresa e gera automaticamente o system_prompt de todos os agentes.
    Também atualiza persona/instructions com valores inteligentes por tipo de agente.
    """
    import psycopg2.extras

    # Prompt e configs específicos por tipo — cada agente tem seu goal próprio
    agent_configs = {
        "atendimento": {
            "goal": "atendimento",
            "persona": f"Assistente de atendimento da {req.company_name}, especializado em {req.niche}.",
            "instructions": f"Responda dúvidas com clareza. {_TONE_MAP.get(req.tone,'')} Foque em resolver o problema do cliente rapidamente.",
        },
        "vendas": {
            "goal": "vendas",
            "persona": f"Consultor de vendas da {req.company_name}, expert em {req.niche}.",
            "instructions": f"Identifique a necessidade, apresente o valor do produto/serviço e conduza para o fechamento. {_TONE_MAP.get(req.tone,'')}",
        },
        "suporte": {
            "goal": "suporte",
            "persona": f"Especialista técnico de suporte da {req.company_name}.",
            "instructions": f"Resolva problemas passo a passo. Peça detalhes quando necessário. {_TONE_MAP.get(req.tone,'')}",
        },
    }

    try:
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, type FROM nexus.agents WHERE user_email = %s",
            (current_user["email"],)
        )
        agents = cur.fetchall()

        updated = []
        for agent in agents:
            cfg = agent_configs.get(agent["type"], {"goal": req.goal, "persona": "", "instructions": ""})
            agent_prompt = generate_default_prompt(req.company_name, req.niche, req.tone, cfg["goal"])
            cur.execute("""
                UPDATE nexus.agents
                SET system_prompt = %s,
                    persona       = %s,
                    instructions  = %s,
                    company_name  = %s,
                    niche         = %s,
                    tone          = %s,
                    goal          = %s,
                    onboarded     = TRUE,
                    updated_at    = NOW()
                WHERE id = %s AND user_email = %s
                RETURNING id, name, type, system_prompt
            """, (
                agent_prompt,
                cfg.get("persona", ""),
                cfg.get("instructions", ""),
                req.company_name, req.niche, req.tone, cfg["goal"],
                agent["id"], current_user["email"]
            ))
            row = cur.fetchone()
            if row:
                updated.append(dict(row))

        con.commit()
        con.close()
        return {
            "message": f"✅ {len(updated)} agentes configurados para {req.company_name}",
            "agents_updated": updated,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/agents/{agent_id}/prompt")
async def update_agent_prompt(
    agent_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    """Permite que o usuário edite manualmente o system_prompt de um agente."""
    import psycopg2.extras
    system_prompt = payload.get("system_prompt", "").strip()
    if not system_prompt:
        raise HTTPException(status_code=400, detail="system_prompt não pode estar vazio")
    try:
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "UPDATE nexus.agents SET system_prompt=%s, updated_at=NOW() WHERE id=%s AND user_email=%s RETURNING *",
            (system_prompt, agent_id, current_user["email"])
        )
        row = cur.fetchone()
        con.commit()
        con.close()
        if not row:
            raise HTTPException(status_code=404, detail="Agente não encontrado")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/chat")
async def agent_chat(req: AgentChatRequest, current_user: dict = Depends(get_current_user)):
    """Send a message to an AI agent and get a response."""
    import psycopg2.extras
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key or openai_key == "sua_chave_openai_aqui":
        raise HTTPException(status_code=503, detail="OpenAI API key não configurada")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)

        # Load agent config
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM nexus.agents WHERE user_email = %s AND type = %s",
            (current_user["email"], req.agent_type)
        )
        agent = cur.fetchone()
        con.close()

        persona = agent["persona"] if agent else "Assistente útil"
        instructions = agent["instructions"] if agent else "Responda de forma clara e objetiva."
        model = agent["model"] if agent else "gpt-4o-mini"
        temperature = float(agent["temperature"]) if agent and agent.get("temperature") is not None else 0.7
        agent_id = agent["id"] if agent else None
        file_search_on = bool(agent.get("file_search")) if agent else False
        sp_override = agent.get("system_prompt", "") if agent else ""

        if sp_override:
            system_prompt = sp_override
        else:
            system_prompt = f"{persona}\n\n{instructions}\n\nVocê é um agente do CRM Nexus. Responda sempre em português."

        # Inject knowledge base files if file_search is enabled
        if file_search_on and agent_id:
            con2 = _agents_conn()
            cur2 = con2.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur2.execute(
                "SELECT filename, content FROM nexus.agent_files WHERE agent_id=%s AND user_email=%s ORDER BY created_at DESC LIMIT 5",
                (agent_id, current_user["email"])
            )
            files = cur2.fetchall()
            con2.close()
            if files:
                kb_context = "\n\n".join(
                    f"--- Arquivo: {f['filename']} ---\n{(f['content'] or '')[:8000]}"
                    for f in files
                )
                system_prompt += f"\n\n=== BASE DE CONHECIMENTO ===\nUse as informações abaixo para responder com precisão:\n{kb_context}"

        messages = [{"role": "system", "content": system_prompt}]
        for h in req.conversation_history[-10:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": req.message})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=800,
            temperature=temperature,
        )
        reply = response.choices[0].message.content
        return {"reply": reply, "agent_type": req.agent_type, "model": model}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao chamar IA: {e}")


# ===== Workflows Routes =====

class WorkflowCreate(BaseModel):
    name: str = "Novo Workflow"
    description: str = ""
    drawflow: dict = {}


def _ensure_workflows_table():
    con = _crm_conn()
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.workflows (
                id          SERIAL PRIMARY KEY,
                user_email  VARCHAR(255) NOT NULL,
                name        VARCHAR(255) NOT NULL DEFAULT 'Novo Workflow',
                description TEXT DEFAULT '',
                drawflow    JSONB NOT NULL DEFAULT '{}',
                active      BOOLEAN DEFAULT FALSE,
                created_at  TIMESTAMP DEFAULT NOW(),
                updated_at  TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS workflows_user_email_idx ON nexus.workflows(user_email)")
    finally:
        con.close()


@app.get("/workflows")
async def list_workflows(current_user: dict = Depends(get_current_user)):
    import psycopg2.extras, json as _json
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, name, description, active, created_at, updated_at FROM nexus.workflows WHERE user_email=%s ORDER BY updated_at DESC",
            (current_user["email"],)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


@app.post("/workflows")
async def create_workflow(wf: WorkflowCreate, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras, json as _json
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Auto-inject company context from user's agents
        cur.execute(
            "SELECT company_name, niche, tone FROM nexus.agents WHERE user_email=%s AND company_name IS NOT NULL LIMIT 1",
            (current_user["email"],)
        )
        agent_row = cur.fetchone()
        company_ctx = {
            "company_name": agent_row["company_name"] if agent_row and agent_row.get("company_name") else "",
            "niche": agent_row["niche"] if agent_row and agent_row.get("niche") else "",
            "tone": agent_row["tone"] if agent_row and agent_row.get("tone") else "amigavel",
        }
        drawflow = wf.drawflow or {"drawflow": {"Home": {"data": {}}}, "context": company_ctx}
        if "context" not in drawflow:
            drawflow["context"] = company_ctx

        cur.execute(
            """INSERT INTO nexus.workflows (user_email, name, description, drawflow)
               VALUES (%s, %s, %s, %s) RETURNING id, name, description, active, created_at""",
            (current_user["email"], wf.name, wf.description, _json.dumps(drawflow))
        )
        row = dict(cur.fetchone())
        row["drawflow"] = drawflow
        con.commit()
        return row
    finally:
        con.close()


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: int, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM nexus.workflows WHERE id=%s AND user_email=%s",
            (workflow_id, current_user["email"])
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Workflow não encontrado")
        return dict(row)
    finally:
        con.close()


@app.put("/workflows/{workflow_id}")
async def save_workflow(workflow_id: int, wf: WorkflowCreate, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras, json as _json
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """UPDATE nexus.workflows SET name=%s, description=%s, drawflow=%s, updated_at=NOW()
               WHERE id=%s AND user_email=%s RETURNING id, name, active, updated_at""",
            (wf.name, wf.description, _json.dumps(wf.drawflow), workflow_id, current_user["email"])
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Workflow não encontrado")
        con.commit()
        return dict(row)
    finally:
        con.close()


@app.post("/workflows/{workflow_id}/activate")
async def activate_workflow(workflow_id: int, current_user: dict = Depends(get_current_user)):
    con = _crm_conn()
    try:
        cur = con.cursor()
        # Desativa todos, ativa o selecionado
        cur.execute("UPDATE nexus.workflows SET active=FALSE WHERE user_email=%s", (current_user["email"],))
        cur.execute(
            "UPDATE nexus.workflows SET active=TRUE, updated_at=NOW() WHERE id=%s AND user_email=%s",
            (workflow_id, current_user["email"])
        )
        con.commit()
        return {"activated": workflow_id}
    finally:
        con.close()


@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: int, current_user: dict = Depends(get_current_user)):
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM nexus.workflows WHERE id=%s AND user_email=%s", (workflow_id, current_user["email"]))
        con.commit()
    finally:
        con.close()
    return {"deleted": workflow_id}


# ── CRM Kanban ────────────────────────────────────────────────────────────────

def _ensure_whatsapp_instances_table():
    con = _crm_conn()
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.whatsapp_instances (
                id            SERIAL PRIMARY KEY,
                user_email    VARCHAR(255) NOT NULL,
                instance_name VARCHAR(255) NOT NULL,
                status        VARCHAR(50)  DEFAULT 'pending',
                created_at    TIMESTAMP    DEFAULT NOW(),
                CONSTRAINT uq_whatsapp_instance UNIQUE (user_email, instance_name)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS whatsapp_instances_user_email_idx ON nexus.whatsapp_instances(user_email)")
    finally:
        con.close()


def _ensure_quick_replies_table():
    con = _crm_conn()
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS nexus")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.quick_replies (
                id         SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                title      VARCHAR(100) NOT NULL,
                content    TEXT         NOT NULL,
                created_at TIMESTAMP    DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS quick_replies_user_email_idx ON nexus.quick_replies(user_email)")
    finally:
        con.close()


def _ensure_sales_goals_table():
    con = _crm_conn()
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.sales_goals (
                id           SERIAL PRIMARY KEY,
                user_email   VARCHAR(255) NOT NULL,
                period       VARCHAR(7) NOT NULL,   -- 'YYYY-MM'
                target_value NUMERIC(14,2) DEFAULT 0,
                target_deals INTEGER DEFAULT 0,
                created_at   TIMESTAMP DEFAULT NOW(),
                updated_at   TIMESTAMP DEFAULT NOW(),
                UNIQUE (user_email, period)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS sales_goals_user_period_idx ON nexus.sales_goals(user_email, period)")
    finally:
        con.close()


def _ensure_kanban_tables():
    con = _crm_conn()
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS nexus")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.pipelines (
                id         SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                name       VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS pipelines_user_email_idx ON nexus.pipelines(user_email)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.pipeline_stages (
                id          SERIAL PRIMARY KEY,
                pipeline_id INTEGER NOT NULL REFERENCES nexus.pipelines(id) ON DELETE CASCADE,
                user_email  VARCHAR(255) NOT NULL,
                name        VARCHAR(255) NOT NULL,
                position    INTEGER NOT NULL DEFAULT 0,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS pipeline_stages_user_email_idx ON nexus.pipeline_stages(user_email)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.deals (
                id          SERIAL PRIMARY KEY,
                stage_id    INTEGER NOT NULL REFERENCES nexus.pipeline_stages(id) ON DELETE RESTRICT,
                user_email  VARCHAR(255) NOT NULL,
                name        VARCHAR(255) NOT NULL,
                contact_jid VARCHAR(255),
                value       NUMERIC(12,2) DEFAULT 0.00,
                status      VARCHAR(50) DEFAULT 'open',
                probability INTEGER DEFAULT NULL,
                close_date  DATE DEFAULT NULL,
                lost_reason TEXT DEFAULT NULL,
                created_at  TIMESTAMP DEFAULT NOW(),
                updated_at  TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS deals_user_email_idx ON nexus.deals(user_email)")
        cur.execute("CREATE INDEX IF NOT EXISTS deals_stage_id_idx ON nexus.deals(stage_id)")
        # Migração idempotente — adiciona colunas se ainda não existirem
        for col, defn in [
            ("probability",  "INTEGER DEFAULT NULL"),
            ("close_date",   "DATE DEFAULT NULL"),
            ("lost_reason",  "TEXT DEFAULT NULL"),
            ("products",     "TEXT DEFAULT '[]'"),   # JSON: [{name, qty, price}]
            ("assigned_to",  "VARCHAR(255) DEFAULT NULL"),
        ]:
            try: cur.execute(f"ALTER TABLE nexus.deals ADD COLUMN IF NOT EXISTS {col} {defn}")
            except Exception: pass
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus.deal_activities (
                id         SERIAL PRIMARY KEY,
                deal_id    INTEGER NOT NULL REFERENCES nexus.deals(id) ON DELETE CASCADE,
                user_email VARCHAR(255) NOT NULL,
                content    TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS deal_activities_deal_id_idx ON nexus.deal_activities(deal_id)")
    finally:
        con.close()


_DEFAULT_STAGES = ["Novo Lead", "Contato Feito", "Proposta Enviada", "Negociação", "Ganho", "Perdido"]


def _seed_default_pipeline(user_email: str) -> None:
    """Cria o pipeline padrão com estágios para uma conta nova."""
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id FROM nexus.pipelines WHERE user_email = %s LIMIT 1",
            (user_email,)
        )
        if cur.fetchone():
            return  # já tem pipeline, não duplicar
        cur.execute(
            "INSERT INTO nexus.pipelines (user_email, name) VALUES (%s, %s) RETURNING id",
            (user_email, "Vendas")
        )
        pipeline_id = cur.fetchone()[0]
        for i, stage_name in enumerate(_DEFAULT_STAGES):
            cur.execute(
                "INSERT INTO nexus.pipeline_stages (pipeline_id, user_email, name, position) VALUES (%s,%s,%s,%s)",
                (pipeline_id, user_email, stage_name, i)
            )
        con.commit()
    except Exception:
        con.rollback()
    finally:
        con.close()


class DealCreate(BaseModel):
    name: str
    stage_id: int
    contact_jid: Optional[str] = None
    value: float = 0.0
    close_date: Optional[str] = None
    assigned_to: Optional[str] = None


class DealMove(BaseModel):
    stage_id: int
    lost_reason: Optional[str] = None   # obrigatório quando destino é "Perdido"


@app.get("/crm/pipelines/list")
async def list_pipelines(current_user: dict = Depends(get_current_user)):
    """Lista todos os funis do usuário."""
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name, created_at FROM nexus.pipelines WHERE user_email = %s ORDER BY created_at", (user_email,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


class PipelineCreate(BaseModel):
    name: str


@app.post("/crm/pipelines", status_code=201)
async def create_pipeline(payload: PipelineCreate, current_user: dict = Depends(get_current_user)):
    """Cria novo funil com os 6 estágios padrão."""
    user_email = current_user["email"]
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Nome obrigatório")
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO nexus.pipelines (user_email, name) VALUES (%s, %s) RETURNING id", (user_email, payload.name.strip()))
        pipeline_id = cur.fetchone()[0]
        for i, stage_name in enumerate(_DEFAULT_STAGES):
            cur.execute("INSERT INTO nexus.pipeline_stages (pipeline_id, user_email, name, position) VALUES (%s,%s,%s,%s)", (pipeline_id, user_email, stage_name, i))
        con.commit()
        return {"id": pipeline_id, "name": payload.name.strip()}
    except Exception as e:
        con.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.delete("/crm/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: int, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM nexus.pipelines WHERE user_email = %s", (user_email,))
        if cur.fetchone()[0] <= 1:
            raise HTTPException(status_code=400, detail="Não é possível deletar o único funil")
        cur.execute("DELETE FROM nexus.pipelines WHERE id = %s AND user_email = %s", (pipeline_id, user_email))
        con.commit()
        return {"deleted": pipeline_id}
    except HTTPException: raise
    except Exception as e:
        con.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.get("/crm/pipelines")
async def get_kanban_board(pipeline_id: Optional[int] = None, vendedor: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Retorna o pipeline completo com estágios e deals. pipeline_id opcional — usa o primeiro se omitido."""
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Garante que o usuário tem pipeline; cria se for conta nova
        cur.execute("SELECT id FROM nexus.pipelines WHERE user_email = %s LIMIT 1", (user_email,))
        if not cur.fetchone():
            con.close()
            await asyncio.to_thread(_seed_default_pipeline, user_email)
            con = _crm_conn()
            cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if pipeline_id:
            cur.execute("SELECT id, name FROM nexus.pipelines WHERE id = %s AND user_email = %s", (pipeline_id, user_email))
        else:
            cur.execute("SELECT id, name FROM nexus.pipelines WHERE user_email = %s ORDER BY created_at LIMIT 1", (user_email,))
        pipeline = cur.fetchone()
        if not pipeline:
            return {"pipeline": None, "stages": []}

        cur.execute(
            "SELECT id, name, position FROM nexus.pipeline_stages WHERE pipeline_id = %s AND user_email = %s ORDER BY position ASC",
            (pipeline["id"], user_email)
        )
        stages_rows = cur.fetchall()

        stages = []
        for s in stages_rows:
            if vendedor:
                cur.execute("""
                    SELECT id, name, contact_jid, value, status, probability, close_date, lost_reason, products, assigned_to, created_at, updated_at,
                           EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400 AS days_stopped
                    FROM nexus.deals
                    WHERE stage_id = %s AND user_email = %s AND status = 'open' AND assigned_to = %s
                    ORDER BY updated_at DESC
                """, (s["id"], user_email, vendedor))
            else:
                cur.execute("""
                    SELECT id, name, contact_jid, value, status, probability, close_date, lost_reason, products, assigned_to, created_at, updated_at,
                           EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400 AS days_stopped
                    FROM nexus.deals
                    WHERE stage_id = %s AND user_email = %s AND status = 'open'
                    ORDER BY updated_at DESC
                """, (s["id"], user_email))
            deals = [{
                "id":           d["id"],
                "name":         d["name"],
                "contact_jid":  d["contact_jid"],
                "value":        float(d["value"] or 0),
                "status":       d["status"],
                "probability":  d["probability"],
                "close_date":   str(d["close_date"]) if d["close_date"] else None,
                "lost_reason":  d["lost_reason"],
                "products":     d["products"] or "[]",
                "assigned_to":  d["assigned_to"],
                "days_stopped": int(d["days_stopped"] or 0),
                "created_at":   d["created_at"].isoformat() if d["created_at"] else None,
                "updated_at":   d["updated_at"].isoformat() if d["updated_at"] else None,
            } for d in cur.fetchall()]
            stages.append({"id": s["id"], "name": s["name"], "position": s["position"], "deals": deals})

        return {"pipeline": dict(pipeline), "stages": stages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.post("/crm/deals", status_code=201)
async def create_deal(payload: DealCreate, current_user: dict = Depends(get_current_user)):
    """Cria um novo deal/lead no estágio indicado."""
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor()
        # garante que o estágio pertence a este usuário
        cur.execute(
            "SELECT id FROM nexus.pipeline_stages WHERE id = %s AND user_email = %s",
            (payload.stage_id, user_email)
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Estágio não encontrado")
        cur.execute("""
            INSERT INTO nexus.deals (stage_id, user_email, name, contact_jid, value, assigned_to)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (payload.stage_id, user_email, payload.name, payload.contact_jid, payload.value, payload.assigned_to))
        deal_id = cur.fetchone()[0]
        con.commit()
        return {"id": deal_id, "name": payload.name, "stage_id": payload.stage_id}
    except HTTPException:
        raise
    except Exception as e:
        con.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


async def _trigger_stage_automations(deal_id: int, stage_id: int, stage_name: str, user_email: str) -> None:
    """Executa automações configuradas para um estágio. Roda em background via create_task."""
    import httpx as _httpx
    evo_url = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
    evo_key = os.getenv("EVOLUTION_API_KEY", "")

    # Mapa de gatilhos: nome do estágio → mensagem automática
    _STAGE_TRIGGERS = {
        "Proposta Enviada": (
            "Olá, *{deal_name}*! 🎉 Sua proposta comercial foi gerada e está sendo revisada pelo nosso consultor. "
            "Em breve entraremos em contato para alinhar os próximos passos!"
        ),
        "Ganho": (
            "Parabéns, *{deal_name}*! ✅ Seu contrato foi fechado com sucesso. "
            "Nossa equipe entrará em contato para iniciar o processo de onboarding."
        ),
    }

    msg_template = _STAGE_TRIGGERS.get(stage_name)
    if not msg_template:
        return  # estágio sem gatilho configurado — nada a fazer

    try:
        # Busca dados do deal (nome + JID do contato)
        con = _crm_conn()
        cur = con.cursor()
        cur.execute(
            "SELECT name, contact_jid FROM nexus.deals WHERE id = %s AND user_email = %s",
            (deal_id, user_email)
        )
        deal_row = cur.fetchone()
        if not deal_row or not deal_row[1]:
            con.close()
            return  # sem contato vinculado — não há para onde mandar

        deal_name, contact_jid = deal_row

        # Resolve instância WhatsApp ativa do usuário
        cur.execute(
            "SELECT instance_name FROM nexus.whatsapp_instances WHERE user_email = %s LIMIT 1",
            (user_email,)
        )
        inst_row = cur.fetchone()
        con.close()
        if not inst_row:
            logger.warning(f"[Automação] Nenhuma instância WA para {user_email} — gatilho ignorado")
            return

        instance_name = inst_row[0]
        # @lid → usa o JID bruto; Evolution API resolve internamente via multi-device
        number = contact_jid.split("@")[0] if "@" in contact_jid else contact_jid
        message = msg_template.format(deal_name=deal_name)

        async with _httpx.AsyncClient(timeout=12) as client:
            resp = await client.post(
                f"{evo_url}/message/sendText/{instance_name}",
                headers={"apikey": evo_key, "Content-Type": "application/json"},
                json={"number": number, "text": message},
            )

        if resp.status_code in (200, 201):
            # Registra no activity log que foi o sistema que enviou
            con2 = _crm_conn()
            cur2 = con2.cursor()
            cur2.execute("""
                INSERT INTO nexus.deal_activities (deal_id, user_email, content)
                VALUES (%s, %s, %s)
            """, (deal_id, user_email, f"[Automação] WhatsApp enviado automaticamente ao entrar em '{stage_name}'"))
            con2.commit()
            con2.close()
            logger.info(f"[Automação] WA disparado para {number} (deal #{deal_id}, estágio '{stage_name}')")
        else:
            logger.error(f"[Automação] Evolution API {resp.status_code}: {resp.text[:200]}")

    except Exception as e:
        logger.error(f"[Automação] Erro no gatilho deal #{deal_id}: {e}")


@app.put("/crm/deals/{deal_id}/move")
async def move_deal(deal_id: int, payload: DealMove, current_user: dict = Depends(get_current_user)):
    """Move um deal de estágio e dispara automações configuradas para o estágio de destino."""
    from datetime import datetime as _dt
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT name FROM nexus.pipeline_stages WHERE id = %s AND user_email = %s",
            (payload.stage_id, user_email)
        )
        stage_row = cur.fetchone()
        if not stage_row:
            raise HTTPException(status_code=404, detail="Estágio de destino não encontrado")
        stage_name = stage_row[0]

        # Calcula probabilidade automática pela posição do estágio
        cur.execute(
            "SELECT position, COUNT(*) OVER() AS total FROM nexus.pipeline_stages WHERE id = %s AND user_email = %s",
            (payload.stage_id, user_email)
        )
        pos_row = cur.fetchone()
        auto_prob = None
        if pos_row:
            pos, total = pos_row
            if stage_name in ("Ganho",): auto_prob = 100
            elif stage_name in ("Perdido",): auto_prob = 0
            else: auto_prob = min(90, int(((pos + 1) / max(total, 1)) * 100))

        # Monta update com lost_reason se for "Perdido"
        extra_sets = ", probability = %s" if auto_prob is not None else ""
        extra_vals = [auto_prob] if auto_prob is not None else []
        if payload.lost_reason and stage_name == "Perdido":
            extra_sets += ", lost_reason = %s"
            extra_vals.append(payload.lost_reason)

        cur.execute(f"""
            UPDATE nexus.deals
            SET stage_id = %s, updated_at = NOW(){extra_sets}
            WHERE id = %s AND user_email = %s
            RETURNING id, name, stage_id
        """, [payload.stage_id] + extra_vals + [deal_id, user_email])
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deal não encontrado ou acesso negado")

        activity_text = f"Movido para '{stage_name}' em {_dt.now().strftime('%d/%m/%Y %H:%M')}"
        if payload.lost_reason:
            activity_text += f" — Motivo: {payload.lost_reason}"
        cur.execute("""
            INSERT INTO nexus.deal_activities (deal_id, user_email, content)
            VALUES (%s, %s, %s)
        """, (deal_id, user_email, activity_text))
        con.commit()

        # Dispara automações em background — não bloqueia a resposta ao frontend
        asyncio.create_task(
            _trigger_stage_automations(deal_id, payload.stage_id, stage_name, user_email)
        )

        return {"id": row[0], "name": row[1], "stage_id": row[2]}
    except HTTPException:
        raise
    except Exception as e:
        con.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.delete("/crm/deals/{deal_id}")
async def delete_deal(deal_id: int, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM nexus.deals WHERE id = %s AND user_email = %s", (deal_id, user_email))
        con.commit()
    finally:
        con.close()
    return {"deleted": deal_id}


@app.get("/crm/deals/{deal_id}/activities")
async def get_deal_activities(deal_id: int, current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, content, created_at FROM nexus.deal_activities
            WHERE deal_id = %s AND user_email = %s
            ORDER BY created_at DESC
        """, (deal_id, user_email))
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


class DealActivityCreate(BaseModel):
    content: str


@app.post("/crm/deals/{deal_id}/activities", status_code=201)
async def add_deal_activity(deal_id: int, payload: DealActivityCreate, current_user: dict = Depends(get_current_user)):
    """Adiciona nota manual ao histórico do deal."""
    user_email = current_user["email"]
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Conteúdo não pode estar vazio")
    con = _crm_conn()
    try:
        cur = con.cursor()
        # Garante que o deal pertence ao usuário
        cur.execute("SELECT id FROM nexus.deals WHERE id = %s AND user_email = %s", (deal_id, user_email))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Deal não encontrado")
        cur.execute("""
            INSERT INTO nexus.deal_activities (deal_id, user_email, content)
            VALUES (%s, %s, %s) RETURNING id, created_at
        """, (deal_id, user_email, payload.content.strip()))
        row = cur.fetchone()
        con.commit()
        return {"id": row[0], "created_at": row[1].isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        con.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


# ── Metas de Vendas ───────────────────────────────────────────────────────────

class SalesGoalUpsert(BaseModel):
    period:       str            # 'YYYY-MM'
    target_value: float = 0.0
    target_deals: int   = 0


@app.get("/crm/goals")
async def get_sales_goal(period: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Retorna meta + realizado do período (padrão: mês atual)."""
    from datetime import datetime as _dt
    import psycopg2.extras
    user_email = current_user["email"]
    if not period:
        period = _dt.utcnow().strftime("%Y-%m")
    period_start = f"{period}-01"
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Meta configurada
        cur.execute(
            "SELECT target_value, target_deals FROM nexus.sales_goals WHERE user_email=%s AND period=%s",
            (user_email, period)
        )
        goal_row = cur.fetchone()
        target_value = float(goal_row["target_value"]) if goal_row else 0.0
        target_deals = int(goal_row["target_deals"])   if goal_row else 0

        # Realizado: deals marcados como Ganho no período
        cur.execute("""
            SELECT COALESCE(SUM(d.value),0) AS won_value, COUNT(*) AS won_deals
            FROM nexus.deals d
            JOIN nexus.pipeline_stages ps ON ps.id = d.stage_id
            WHERE d.user_email = %s
              AND ps.name = 'Ganho'
              AND d.updated_at >= %s::date
              AND d.updated_at < (%s::date + INTERVAL '1 month')
        """, (user_email, period_start, period_start))
        actual = cur.fetchone()
        won_value = float(actual["won_value"]) if actual else 0.0
        won_deals = int(actual["won_deals"])   if actual else 0

        # Deals abertos (em andamento) com seus valores — para forecast
        cur.execute("""
            SELECT COALESCE(SUM(d.value),0) AS pipe_value, COUNT(*) AS pipe_deals
            FROM nexus.deals d
            JOIN nexus.pipeline_stages ps ON ps.id = d.stage_id
            WHERE d.user_email = %s AND d.status = 'open' AND ps.name NOT IN ('Ganho','Perdido')
        """, (user_email,))
        pipe = cur.fetchone()
        pipe_value = float(pipe["pipe_value"]) if pipe else 0.0

        return {
            "period":        period,
            "target_value":  target_value,
            "target_deals":  target_deals,
            "won_value":     won_value,
            "won_deals":     won_deals,
            "pipeline_value": pipe_value,
            "pct_value":     round((won_value / target_value * 100) if target_value > 0 else 0, 1),
            "pct_deals":     round((won_deals / target_deals * 100) if target_deals > 0 else 0, 1),
        }
    finally:
        con.close()


@app.put("/crm/goals")
async def upsert_sales_goal(payload: SalesGoalUpsert, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO nexus.sales_goals (user_email, period, target_value, target_deals)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_email, period) DO UPDATE
              SET target_value = EXCLUDED.target_value,
                  target_deals = EXCLUDED.target_deals,
                  updated_at   = NOW()
        """, (user_email, payload.period, payload.target_value, payload.target_deals))
        con.commit()
        return {"saved": payload.period}
    except Exception as e:
        con.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


# ── Workflow Execution Engine ────────────────────────────────────────────────

class WorkflowRunRequest(BaseModel):
    message: str
    conversation_history: list = []
    contact_jid: str = ""


def _wf_find_start(nodes: dict) -> Optional[dict]:
    for node in nodes.values():
        if node.get("name") == "start":
            return node
    return None


def _wf_next_nodes(node: dict, nodes: dict, output_index: int = 0) -> list:
    """Return list of next node dicts following output_index (0-based)."""
    outputs = node.get("outputs", {})
    output_keys = sorted(outputs.keys())  # output_1, output_2, ...
    if output_index >= len(output_keys):
        return []
    conns = outputs[output_keys[output_index]].get("connections", [])
    result = []
    for c in conns:
        nid = str(c.get("node", c.get("output", "")))
        if nid in nodes:
            result.append(nodes[nid])
    return result


def _wf_execute(drawflow_json: dict, message: str, history: list,
                user_email: str, openai_key: str) -> dict:
    """Traverse and execute the workflow graph, returning reply + trace."""
    from openai import OpenAI
    client = OpenAI(api_key=openai_key)

    nodes = drawflow_json.get("drawflow", {}).get("Home", {}).get("data", {})
    context_meta = drawflow_json.get("context", {})
    company_name = context_meta.get("company_name", "")
    niche = context_meta.get("niche", "")

    # Execution context passed between nodes
    ctx = {
        "message": message,
        "history": list(history),
        "kb_context": "",
        "reply": "",
        "company_name": company_name,
        "niche": niche,
    }
    trace = []
    visited = set()
    MAX_STEPS = 20

    current_node = _wf_find_start(nodes)
    if not current_node:
        return {"reply": "Workflow sem nó Start.", "trace": []}

    steps = 0
    while current_node and steps < MAX_STEPS:
        steps += 1
        nid = str(current_node.get("id", "?"))
        ntype = current_node.get("name", "")
        data = current_node.get("data", {})

        if nid in visited:
            break
        visited.add(nid)

        output_idx = 0  # which output to follow

        if ntype == "start":
            if data.get("company_name"):
                ctx["company_name"] = data["company_name"]
            if data.get("niche"):
                ctx["niche"] = data["niche"]
            trace.append({"node": data.get("label","Start"), "type":"start", "output": f"empresa={ctx['company_name']}"})

        elif ntype == "file_search":
            # Inject KB from agent files into ctx
            try:
                import psycopg2.extras
                con = _crm_conn()
                cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                agent_id_filter = data.get("agent_id", "")
                if agent_id_filter:
                    cur.execute("SELECT filename, content FROM nexus.agent_files WHERE agent_id=%s AND user_email=%s ORDER BY created_at DESC LIMIT 5",
                                (agent_id_filter, user_email))
                else:
                    cur.execute("SELECT filename, content FROM nexus.agent_files WHERE user_email=%s ORDER BY created_at DESC LIMIT 5",
                                (user_email,))
                files = cur.fetchall()
                con.close()
                if files:
                    ctx["kb_context"] = "\n\n".join(
                        f"--- {f['filename']} ---\n{(f['content'] or '')[:4000]}" for f in files)
            except Exception as e:
                ctx["kb_context"] = ""
            trace.append({"node": data.get("label","File Search"), "type":"file_search",
                          "output": f"{len(ctx['kb_context'])} chars de KB injetados"})

        elif ntype == "guardrails":
            rules = data.get("rules", "")
            blocked_reply = data.get("blocked_reply", "Não posso ajudar com isso.")
            if rules:
                check_prompt = (
                    f"Você é um filtro de guardrails. Regras: {rules}\n\n"
                    f"Mensagem: {ctx['message']}\n\n"
                    "Responda apenas: PERMITIDO ou BLOQUEADO"
                )
                try:
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini", max_tokens=10, temperature=0,
                        messages=[{"role":"user","content": check_prompt}]
                    )
                    verdict = resp.choices[0].message.content.strip().upper()
                except Exception:
                    verdict = "PERMITIDO"
                if "BLOQUEADO" in verdict:
                    ctx["reply"] = blocked_reply
                    trace.append({"node": data.get("label","Guardrails"), "type":"guardrails", "output":"BLOQUEADO"})
                    output_idx = 1  # saída bloqueado
                else:
                    trace.append({"node": data.get("label","Guardrails"), "type":"guardrails", "output":"PERMITIDO"})
                    output_idx = 0

        elif ntype == "classify":
            categories = [c.strip() for c in data.get("categories","outro").split(",") if c.strip()]
            instructions = data.get("instructions","Classifique a mensagem.")
            cats_str = ", ".join(categories)
            classify_prompt = (
                f"{instructions}\n\nCategorias disponíveis: {cats_str}\n\n"
                f"Mensagem: {ctx['message']}\n\n"
                f"Responda apenas com uma das categorias: {cats_str}"
            )
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini", max_tokens=20, temperature=0,
                    messages=[{"role":"user","content": classify_prompt}]
                )
                category = resp.choices[0].message.content.strip().lower()
                # Find best matching category index
                output_idx = 0
                for i, cat in enumerate(categories):
                    if cat.lower() in category:
                        output_idx = i
                        break
                else:
                    output_idx = len(categories) - 1  # default to last (outro)
            except Exception:
                output_idx = len(categories) - 1
            trace.append({"node": data.get("label","Classify"), "type":"classify",
                          "output": categories[output_idx] if output_idx < len(categories) else "?"})

        elif ntype == "condition":
            rule = data.get("rule", "")
            if rule:
                check_prompt = (
                    f"Avalie se a regra é verdadeira. Regra: {rule}\n"
                    f"Contexto: mensagem='{ctx['message']}', resposta_anterior='{ctx['reply']}'\n"
                    "Responda apenas: VERDADEIRO ou FALSO"
                )
                try:
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini", max_tokens=10, temperature=0,
                        messages=[{"role":"user","content": check_prompt}]
                    )
                    verdict = resp.choices[0].message.content.strip().upper()
                    output_idx = 0 if "VERDADEIRO" in verdict else 1
                except Exception:
                    output_idx = 1
            trace.append({"node": data.get("label","Condição"), "type":"condition",
                          "output": "saída 1 (Sim)" if output_idx==0 else "saída 2 (Não)"})

        elif ntype == "agent":
            agent_type = data.get("agent_type", "atendimento")
            model = data.get("model", "gpt-4o-mini")
            temperature = float(data.get("temperature", 0.7))
            instructions = data.get("instructions", "")
            include_history = data.get("include_history", True)
            use_file_search = data.get("file_search", False)

            # Load agent config from DB
            try:
                import psycopg2.extras
                con = _crm_conn()
                cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute("SELECT * FROM nexus.agents WHERE user_email=%s AND type=%s",
                            (user_email, agent_type))
                agent_row = cur.fetchone()
                con.close()
            except Exception:
                agent_row = None

            persona = agent_row["persona"] if agent_row else f"Assistente de {agent_type}"
            db_instructions = agent_row["instructions"] if agent_row else ""
            sp_override = agent_row.get("system_prompt","") if agent_row else ""

            company_ctx = ""
            if ctx["company_name"]:
                company_ctx = f"Empresa: {ctx['company_name']}. Setor: {ctx['niche']}.\n\n"

            if sp_override:
                system_prompt = company_ctx + sp_override
            else:
                system_prompt = (
                    f"{company_ctx}{persona}\n\n"
                    f"{db_instructions}\n{instructions}\n\n"
                    "Responda sempre em português."
                ).strip()

            if use_file_search and ctx.get("kb_context"):
                system_prompt += f"\n\n=== BASE DE CONHECIMENTO ===\n{ctx['kb_context']}"
            elif ctx.get("kb_context") and agent_row and agent_row.get("file_search"):
                system_prompt += f"\n\n=== BASE DE CONHECIMENTO ===\n{ctx['kb_context']}"

            messages = [{"role":"system","content": system_prompt}]
            if include_history:
                for h in ctx["history"][-8:]:
                    messages.append({"role": h.get("role","user"), "content": h.get("content","")})
            messages.append({"role":"user","content": ctx["message"]})

            try:
                resp = client.chat.completions.create(
                    model=model, messages=messages, max_tokens=600, temperature=temperature
                )
                ctx["reply"] = resp.choices[0].message.content
                ctx["history"].append({"role":"user","content": ctx["message"]})
                ctx["history"].append({"role":"assistant","content": ctx["reply"]})
            except Exception as e:
                ctx["reply"] = f"Erro no agente: {e}"
            trace.append({"node": data.get("label","Agente"), "type":"agent",
                          "output": ctx["reply"][:80]+"..." if len(ctx["reply"])>80 else ctx["reply"]})

        elif ntype == "action":
            action_type = data.get("action_type", "send_message")
            template = data.get("template", "")
            msg_out = template if template else ctx["reply"]
            trace.append({"node": data.get("label","Ação"), "type":"action",
                          "output": f"{action_type}: {msg_out[:60]}"})

        elif ntype == "end":
            final_msg = data.get("message", "")
            if final_msg:
                ctx["reply"] = final_msg
            trace.append({"node": data.get("label","End"), "type":"end", "output":"fluxo encerrado"})
            break

        # Advance to next node
        next_nodes = _wf_next_nodes(current_node, nodes, output_idx)
        current_node = next_nodes[0] if next_nodes else None

    return {"reply": ctx["reply"] or "Sem resposta do fluxo.", "trace": trace}


@app.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: int, req: WorkflowRunRequest,
                       current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key or openai_key.startswith("sk-proj-SEU"):
        raise HTTPException(status_code=503, detail="OpenAI API key não configurada")
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT drawflow FROM nexus.workflows WHERE id=%s AND user_email=%s",
                    (workflow_id, current_user["email"]))
        row = cur.fetchone()
    finally:
        con.close()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow não encontrado")
    try:
        result = _wf_execute(
            drawflow_json=row["drawflow"],
            message=req.message,
            history=req.conversation_history,
            user_email=current_user["email"],
            openai_key=openai_key,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na execução: {e}")


class OptimizePromptRequest(BaseModel):
    idea: str
    node_type: str = "agent"


@app.post("/workflows/optimize-prompt")
async def optimize_prompt(req: OptimizePromptRequest, current_user: dict = Depends(get_current_user)):
    """Generates a professional structured system prompt from a simple idea,
    enriched with the user's onboarding profile (ramo, objetivo, tom)."""
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key or openai_key.startswith("sk-proj-SEU"):
        raise HTTPException(status_code=503, detail="OpenAI API key não configurada")

    user = _get_user(current_user["email"])
    ramo    = user.get("ramo_empresa", "") or "não informado"
    obj_ia  = user.get("objetivo_ia",  "") or "atendimento_suporte"
    tom     = user.get("tom_de_voz",   "") or "amigavel"
    empresa = user.get("company", "") or "nossa empresa"

    ramo_labels = {
        "saude": "Saúde e Bem-estar", "estetica": "Estética e Beleza",
        "vendas_varejo": "Vendas e Varejo", "educacao": "Educação e Cursos",
        "imoveis": "Imóveis e Construtoras", "juridico": "Jurídico e Advocacia",
        "tecnologia": "Tecnologia e Software", "financeiro": "Financeiro e Contabilidade",
        "alimentacao": "Alimentação e Delivery", "servicos": "Serviços Gerais",
    }
    tom_labels = {
        "formal": "formal, técnico e profissional",
        "amigavel": "descontraído, amigável e próximo",
        "comercial": "direto, comercial e persuasivo",
    }
    ramo_str = ramo_labels.get(ramo, ramo)
    tom_str  = tom_labels.get(tom, tom)

    meta = (
        f"Empresa: {empresa} | Setor: {ramo_str} | "
        f"Objetivo: {obj_ia.replace('_', ' ')} | Tom: {tom_str}"
    )

    system_msg = (
        "Você é um especialista em engenharia de prompts para chatbots de WhatsApp. "
        "Gere um System Prompt profissional, estruturado e pronto para uso imediato. "
        "Use exatamente este formato:\n\n"
        "[PERSONA]\n<Quem é a IA, nome e papel>\n\n"
        "[EMPRESA & NICHO]\n<Contexto da empresa e setor>\n\n"
        "[REGRAS DO NEGÓCIO]\n<Lista de regras de atendimento>\n\n"
        "[FILTROS DE ALUCINAÇÃO]\n<O que a IA NUNCA deve fazer ou inventar>\n\n"
        "[TOM & ESTILO]\n<Como deve se comunicar>\n\n"
        "Use {{empresa.nome}} e {{cliente.nome}} como variáveis de personalização. "
        "O prompt deve ter entre 200 e 400 palavras. "
        "Responda APENAS com o prompt, sem explicações adicionais."
    )

    user_msg = f"Perfil do negócio: {meta}\n\nIdeia do usuário: {req.idea}"

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=600,
            temperature=0.5,
        )
        prompt = resp.choices[0].message.content.strip()
        # Replace template vars with safe escaped versions
        prompt = prompt.replace("{{empresa.nome}}", empresa or "{{empresa.nome}}")
        return {"prompt": prompt, "meta": meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar prompt: {e}")


# ===== Analytics / Metrics Routes =====


@app.get("/metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)):
    """Métricas reais do CRM para o usuário autenticado."""
    import psycopg2.extras
    email = current_user["email"]
    cached = _cache_get(f"metrics:{email}")
    if cached:
        return cached
    try:
        con = _agents_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Total de contatos
        cur.execute("SELECT COUNT(*) AS n FROM nexus.contacts WHERE user_email=%s", (email,))
        total_contacts = cur.fetchone()["n"]

        # Contatos por fonte
        cur.execute("""
            SELECT source, COUNT(*) AS n FROM nexus.contacts
            WHERE user_email=%s GROUP BY source ORDER BY n DESC
        """, (email,))
        by_source = {r["source"]: r["n"] for r in cur.fetchall()}

        # Mensagens IA (enviadas/recebidas)
        cur.execute("""
            SELECT direction, COUNT(*) AS n FROM nexus.messages
            WHERE user_email=%s GROUP BY direction
        """, (email,))
        msg_rows = {r["direction"]: r["n"] for r in cur.fetchall()}
        msgs_in  = msg_rows.get("in", 0)
        msgs_out = msg_rows.get("out", 0)

        # Mensagens dos últimos 7 dias (por dia)
        cur.execute("""
            SELECT DATE(created_at) AS day, direction, COUNT(*) AS n
            FROM nexus.messages WHERE user_email=%s
              AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY day, direction ORDER BY day
        """, (email,))
        daily_rows = cur.fetchall()
        daily: dict = {}
        for r in daily_rows:
            d = str(r["day"])
            if d not in daily:
                daily[d] = {"in": 0, "out": 0}
            daily[d][r["direction"]] = r["n"]

        # Funil Kanban
        cur.execute("""
            SELECT stage, COUNT(*) AS n, COALESCE(SUM(value),0) AS total_value
            FROM nexus.pipeline WHERE user_email=%s GROUP BY stage
        """, (email,))
        pipeline_rows = cur.fetchall()
        stages = {
            "novo": {"count": 0, "value": 0},
            "contato": {"count": 0, "value": 0},
            "proposta": {"count": 0, "value": 0},
            "negociacao": {"count": 0, "value": 0},
            "fechado": {"count": 0, "value": 0},
            "perdido": {"count": 0, "value": 0},
        }
        for r in pipeline_rows:
            stages[r["stage"]] = {"count": r["n"], "value": float(r["total_value"])}

        total_pipeline = sum(s["count"] for s in stages.values())
        total_value    = sum(s["value"] for s in stages.values())
        closed_count   = stages["fechado"]["count"]
        conv_rate      = round(closed_count / total_pipeline * 100, 1) if total_pipeline else 0

        # Agentes ativos
        cur.execute("SELECT COUNT(*) AS n FROM nexus.agents WHERE user_email=%s AND active=TRUE", (email,))
        active_agents = cur.fetchone()["n"]

        # Plano atual + trial_ends_at
        cur.execute("SELECT plan, trial_ends_at FROM nexus.users WHERE email=%s", (email,))
        row = cur.fetchone()
        plan = row["plan"] if row else "trial"
        trial_ends_at = _trial_iso(row["trial_ends_at"]) if row else None

        # Instâncias WhatsApp conectadas
        try:
            cur.execute("SELECT COUNT(*) AS n FROM nexus.whatsapp_instances WHERE user_email=%s", (email,))
            wa_count = cur.fetchone()["n"]
        except Exception:
            wa_count = 0

        # Mensagens IA no mês atual
        try:
            cur.execute("""
                SELECT COUNT(*) AS n FROM nexus.messages
                WHERE user_email=%s AND direction='out'
                  AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())
            """, (email,))
            msgs_out_month = cur.fetchone()["n"]
        except Exception:
            msgs_out_month = msgs_out

        con.close()
        result = {
            "contacts":         {"total": total_contacts, "by_source": by_source},
            "messages":         {"received": msgs_in, "sent": msgs_out, "total": msgs_in + msgs_out, "daily": daily, "sent_month": msgs_out_month},
            "pipeline":         {"stages": stages, "total": total_pipeline, "total_value": total_value, "conversion_rate": conv_rate},
            "agents":           {"active": active_agents},
            "plan":             plan,
            "trial_ends_at":    trial_ends_at,
            "wa_instances":     wa_count,
        }
        _cache_set(f"metrics:{email}", result, ttl=30)
        return result
    except Exception as e:
        return {"error": str(e), "contacts": {"total": 0}, "messages": {"received": 0, "sent": 0, "total": 0, "daily": {}}, "pipeline": {"stages": {}, "total": 0, "total_value": 0, "conversion_rate": 0}, "agents": {"active": 0}, "plan": "trial"}


@app.get("/analytics/summary")
async def get_analytics_summary(current_user: dict = Depends(get_current_user)):
    return await get_metrics(current_user)


@app.get("/metrics/financial")
async def get_financial_metrics(current_user: dict = Depends(get_current_user)):
    """Retorna métricas financeiras: receita por mês, ticket médio, ganhos vs perdidos, forecast."""
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Receita por mês (últimos 6 meses) — deals com status 'won'
        cur.execute("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', updated_at), 'YYYY-MM') AS month,
                SUM(value)::float                                    AS revenue,
                COUNT(*)                                             AS won_count
            FROM nexus.deals
            WHERE user_email = %s AND status = 'won'
              AND updated_at >= NOW() - INTERVAL '6 months'
            GROUP BY 1 ORDER BY 1
        """, (user_email,))
        monthly = [dict(r) for r in cur.fetchall()]

        # Deals perdidos por mês
        cur.execute("""
            SELECT TO_CHAR(DATE_TRUNC('month', updated_at), 'YYYY-MM') AS month, COUNT(*) AS lost_count
            FROM nexus.deals
            WHERE user_email = %s AND status = 'lost'
              AND updated_at >= NOW() - INTERVAL '6 months'
            GROUP BY 1 ORDER BY 1
        """, (user_email,))
        lost_map = {r["month"]: r["lost_count"] for r in cur.fetchall()}

        # Totais gerais
        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN status='won' THEN value ELSE 0 END), 0)::float  AS total_revenue,
                COALESCE(COUNT(CASE WHEN status='won' THEN 1 END), 0)                  AS total_won,
                COALESCE(COUNT(CASE WHEN status='lost' THEN 1 END), 0)                 AS total_lost,
                COALESCE(SUM(CASE WHEN status='open' THEN value ELSE 0 END), 0)::float AS forecast
            FROM nexus.deals WHERE user_email = %s
        """, (user_email,))
        totals = dict(cur.fetchone())

        avg_ticket = (totals["total_revenue"] / totals["total_won"]) if totals["total_won"] > 0 else 0

        months_merged = []
        all_months = sorted(set(list({r["month"] for r in monthly}) | set(lost_map.keys())))
        rev_map = {r["month"]: r for r in monthly}
        for m in all_months:
            months_merged.append({
                "month":     m,
                "revenue":   rev_map.get(m, {}).get("revenue", 0),
                "won":       rev_map.get(m, {}).get("won_count", 0),
                "lost":      lost_map.get(m, 0),
            })

        return {
            "monthly":       months_merged,
            "total_revenue": totals["total_revenue"],
            "total_won":     totals["total_won"],
            "total_lost":    totals["total_lost"],
            "forecast":      totals["forecast"],
            "avg_ticket":    round(avg_ticket, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.get("/metrics/funnel")
async def get_funnel_metrics(pipeline_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """Retorna contagem e valor de deals por estágio para funil de conversão."""
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        pid_filter = "AND ps.pipeline_id = %s" if pipeline_id else ""
        params = (user_email, pipeline_id, user_email) if pipeline_id else (user_email, user_email)
        cur.execute(f"""
            SELECT ps.name AS stage, ps.position,
                   COUNT(d.id) AS deal_count,
                   COALESCE(SUM(d.value), 0)::float AS total_value
            FROM nexus.pipeline_stages ps
            LEFT JOIN nexus.deals d ON d.stage_id = ps.id AND d.user_email = %s AND d.status = 'open'
            WHERE ps.user_email = %s {pid_filter}
            GROUP BY ps.name, ps.position ORDER BY ps.position
        """, params if not pipeline_id else (user_email, user_email, pipeline_id))
        stages = [dict(r) for r in cur.fetchall()]
        # Calcula % de conversão em relação ao estágio anterior
        for i, s in enumerate(stages):
            if i == 0:
                s["pct"] = 100
            else:
                prev = stages[i-1]["deal_count"]
                s["pct"] = round((s["deal_count"] / prev * 100) if prev > 0 else 0, 1)
        return {"stages": stages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


# ===== Inbox Routes =====

def _evo_conn():
    return _evo_conn_pool()


def _get_user_instance_ids(user_email: str) -> list[str]:
    """Retorna os instance IDs das instâncias registradas para este usuário (modo estrito)."""
    try:
        crm = _crm_conn()
        cur = crm.cursor()
        cur.execute(
            "SELECT instance_name FROM nexus.whatsapp_instances WHERE user_email = %s",
            (user_email,)
        )
        names = [r[0] for r in cur.fetchall()]
        crm.close()
        if not names:
            return []
        evo = _evo_conn()
        cur2 = evo.cursor()
        cur2.execute(
            'SELECT id FROM vexus."Instance" WHERE name = ANY(%s)',
            (names,)
        )
        ids = [r[0] for r in cur2.fetchall()]
        evo.close()
        return ids
    except Exception:
        return []


def _extract_media(message: dict) -> tuple[str, str]:
    """Returns (media_url, media_name) from message JSONB."""
    for key in ("imageMessage", "videoMessage", "audioMessage", "ptvMessage", "documentMessage", "stickerMessage"):
        m = message.get(key)
        if m and isinstance(m, dict):
            url = m.get("url") or m.get("mediaUrl") or ""
            name = m.get("fileName") or m.get("caption") or ""
            return url, name
    return "", ""


def _extract_text(message: dict) -> str:
    if not message:
        return ""
    if message.get("conversation"):
        return message["conversation"]
    if message.get("extendedTextMessage", {}).get("text"):
        return message["extendedTextMessage"]["text"]
    if message.get("imageMessage"):
        return message["imageMessage"].get("caption") or "📷 Foto"
    if message.get("videoMessage"):
        return message["videoMessage"].get("caption") or "🎥 Vídeo"
    if message.get("audioMessage") or message.get("ptvMessage"):
        return "🎵 Áudio"
    if message.get("documentMessage"):
        return "📄 " + (message["documentMessage"].get("fileName") or "Documento")
    if message.get("stickerMessage"):
        return "🩷 Sticker"
    if message.get("contactMessage"):
        return "👤 Contato"
    if message.get("locationMessage"):
        return "📍 Localização"
    return ""


@app.get("/inbox/chats")
async def inbox_chats(limit: int = 30, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """Lista paginada de conversas, ordenadas pela mensagem mais recente."""
    import psycopg2.extras
    user_email = current_user.get("email", "")

    # Filtra apenas instâncias do usuário logado
    instance_ids = _get_user_instance_ids(user_email)
    if not instance_ids:
        return {"chats": [], "total": 0, "offset": offset}

    # Resolve o ownerJid (número do próprio usuário) para excluí-lo do inbox.
    # Evolution API v2 armazena o JID do dono em "ownerJid" na tabela Instance.
    owner_jids: list[str] = []
    try:
        _oi_con = _evo_conn()
        _oi_cur = _oi_con.cursor()
        _oi_cur.execute(
            'SELECT "ownerJid" FROM vexus."Instance" WHERE id = ANY(%s) AND "ownerJid" IS NOT NULL',
            (instance_ids,)
        )
        owner_jids = [r[0] for r in _oi_cur.fetchall() if r[0]]
        _oi_con.close()
    except Exception:
        pass  # coluna pode não existir em versões antigas da Evolution API

    # Cache da primeira página por 15s (por usuário)
    if offset == 0:
        ck = f"inbox:{user_email}:{limit}"
        cached = _cache_get(ck)
        if cached:
            return cached
    try:
        con = _evo_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Exclui grupos, JID de sistema e o próprio número do usuário (owner)
        _excluded = ['0@s.whatsapp.net'] + owner_jids
        cur.execute("""
            SELECT COUNT(DISTINCT "remoteJid") AS total FROM vexus."Chat"
            WHERE "remoteJid" NOT LIKE '%%@g.us'
              AND "remoteJid" <> ALL(%s)
              AND "instanceId" = ANY(%s)
        """, (_excluded, instance_ids,))
        total = cur.fetchone()["total"]

        # DISTINCT ON deduplicates Chat rows with same remoteJid (Evolution sometimes inserts duplicates).
        # JOIN Contact for pushName (real WA display name) and profilePicUrl (already cached by Evo).
        # Fallback to Message.pushName for @lid JIDs that lack a Contact row.
        cur.execute("""
            SELECT
                c."remoteJid"                                                               AS jid,
                COALESCE(
                    NULLIF(co.push_name,''),
                    NULLIF(pn.push_name,''),
                    NULLIF(CASE WHEN c."name" NOT LIKE '%%@s.whatsapp.net'
                                 AND c."name" NOT LIKE '%%@lid'
                                 AND c."name" <> split_part(c."remoteJid",'@',1)
                            THEN c."name" END, ''),
                    split_part(c."remoteJid",'@',1))                                        AS name,
                split_part(c."remoteJid",'@',1)                                             AS phone,
                COALESCE(c."unreadMessages", 0)                                             AS unread,
                COALESCE(lm.last_ts,
                         EXTRACT(EPOCH FROM c."updatedAt")::bigint)                         AS last_ts,
                co.photo_url,
                lm.from_me,
                lm.last_message
            FROM (
                SELECT DISTINCT ON (c2."remoteJid") c2.*
                FROM vexus."Chat" c2
                WHERE c2."remoteJid" NOT LIKE '%%@g.us'
                  AND c2."remoteJid" <> ALL(%s)
                  AND c2."instanceId" = ANY(%s)
                ORDER BY c2."remoteJid", c2."updatedAt" DESC NULLS LAST
            ) c
            LEFT JOIN LATERAL (
                SELECT NULLIF(con."pushName",'') AS push_name, con."profilePicUrl" AS photo_url
                FROM vexus."Contact" con
                WHERE con."remoteJid" = c."remoteJid"
                ORDER BY con."updatedAt" DESC
                LIMIT 1
            ) co ON true
            LEFT JOIN LATERAL (
                SELECT m."pushName" AS push_name
                FROM vexus."Message" m
                WHERE m."key"->>'remoteJid' = c."remoteJid"
                  AND m."pushName" IS NOT NULL AND m."pushName" != ''
                ORDER BY m."messageTimestamp" DESC
                LIMIT 1
            ) pn ON true
            LEFT JOIN LATERAL (
                SELECT
                    m."key"->>'fromMe'            AS from_me,
                    m."message"                   AS last_message,
                    m."messageTimestamp"::bigint  AS last_ts
                FROM vexus."Message" m
                WHERE m."key"->>'remoteJid' = c."remoteJid"
                  AND m."messageTimestamp" IS NOT NULL
                ORDER BY m."messageTimestamp" DESC
                LIMIT 1
            ) lm ON true
            ORDER BY COALESCE(lm.last_ts, EXTRACT(EPOCH FROM c."updatedAt")::bigint) DESC NULLS LAST
            LIMIT %s OFFSET %s
        """, (_excluded, instance_ids, limit, offset))
        rows = cur.fetchall()
        con.close()
        chats = [{
            "jid":       r["jid"],
            "name":      r["name"],
            "phone":     r["phone"],
            "from_me":   r["from_me"],
            "last_msg":  _extract_text(r["last_message"] or {}),
            "last_ts":   r["last_ts"],
            "unread":    r["unread"],
            "photo_url": r["photo_url"],
        } for r in rows]

        # CRM name override — usa nome salvo em nexus.contacts quando disponível.
        # Exclui matches cujo nome seja igual ao do usuário logado (evita que o
        # próprio cadastro do usuário contamine o nome de contatos externos).
        try:
            jids  = [c["jid"] for c in chats if c["jid"]]
            phones = [c["phone"] for c in chats if c["phone"]]
            if jids or phones:
                crm = _crm_conn()
                crm_cur = crm.cursor()
                # Busca nome do usuário logado para usar como exclusão
                crm_cur.execute(
                    "SELECT COALESCE(name,'') FROM nexus.users WHERE email = %s LIMIT 1",
                    (current_user["email"],)
                )
                user_row = crm_cur.fetchone()
                owner_name = (user_row[0] or "").strip().lower() if user_row else ""

                crm_cur.execute("""
                    SELECT COALESCE(whatsapp_jid,''), COALESCE(phone,''), name
                    FROM nexus.contacts
                    WHERE user_email = %s
                      AND (whatsapp_jid = ANY(%s) OR phone = ANY(%s))
                      AND name IS NOT NULL AND name <> ''
                """, (current_user["email"], jids, phones))
                cmap = {}
                for wjid, ph, cname in crm_cur.fetchall():
                    # Nunca sobrepõe com o nome do próprio usuário — evita falso override
                    if owner_name and cname.strip().lower() == owner_name:
                        continue
                    if wjid: cmap[wjid] = cname
                    if ph:   cmap[ph]   = cname
                crm.close()
                for c in chats:
                    crm_name = cmap.get(c["jid"]) or cmap.get(c["phone"])
                    if crm_name:
                        c["name"] = crm_name
        except Exception:
            pass

        result = {"total": total, "offset": offset, "limit": limit, "has_more": (offset + limit) < total, "chats": chats}
        if offset == 0:
            _cache_set(f"inbox:{user_email}:{limit}", result, ttl=15)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


_photo_cache: dict = {}  # jid -> {url, ts}

@app.get("/inbox/contact-photo")
async def inbox_contact_photo(jid: str, current_user: dict = Depends(get_current_user)):
    """Retorna URL da foto de perfil. Prioridade: cache → vexus.Contact → Evolution API."""
    now = time.time()
    cached = _photo_cache.get(jid)
    if cached and now - cached["ts"] < 600:
        return {"url": cached["url"], "name": cached.get("name")}

    # Fast path: check vexus.Contact (Evolution already cached the URL there)
    try:
        con = _evo_conn()
        cur = con.cursor()
        cur.execute(
            'SELECT "profilePicUrl", "pushName" FROM vexus."Contact" WHERE "remoteJid" = %s LIMIT 1',
            (jid,)
        )
        row = cur.fetchone()
        con.close()
        if row and row[0]:
            _photo_cache[jid] = {"url": row[0], "name": row[1], "ts": now}
            return {"url": row[0], "name": row[1]}
    except Exception:
        pass

    # Slow path: ask Evolution API (only runs if Contact row has no photo URL)
    try:
        import httpx as _httpx
        evo_url = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
        evo_key = os.getenv("EVOLUTION_API_KEY", "")
        number  = jid.split("@")[0]
        async with _httpx.AsyncClient(timeout=5) as hc:
            inst_r = await hc.get(f"{evo_url}/instance/fetchInstances",
                                   headers={"apikey": evo_key})
            instances = inst_r.json() if inst_r.status_code == 200 else []
            instance_name = None
            for inst in (instances if isinstance(instances, list) else []):
                s = inst.get("connectionStatus") or (inst.get("instance") or {}).get("status") or ""
                if s in ("open", "connected"):
                    instance_name = inst.get("name") or (inst.get("instance") or {}).get("instanceName")
                    break
            if not instance_name:
                _photo_cache[jid] = {"url": None, "ts": now}
                return {"url": None}
            pic_r = await hc.post(
                f"{evo_url}/chat/fetchProfilePicture/{instance_name}",
                headers={"apikey": evo_key, "Content-Type": "application/json"},
                json={"number": number}
            )
            url = None
            if pic_r.status_code == 200:
                url = pic_r.json().get("profilePictureUrl") or pic_r.json().get("picture")
        _photo_cache[jid] = {"url": url, "ts": now}
        return {"url": url}
    except Exception:
        return {"url": None}


@app.get("/inbox/chats/{jid}/messages")
async def inbox_messages(jid: str, limit: int = 100, before_ts: int = None, current_user: dict = Depends(get_current_user)):
    """Histórico de mensagens de uma conversa. before_ts carrega mensagens anteriores ao timestamp dado."""
    import psycopg2.extras
    # Verifica se o JID pertence a uma instância do usuário
    user_email = current_user.get("email", "")
    instance_ids = _get_user_instance_ids(user_email)
    # Sem instâncias registradas = sem acesso ao inbox
    if not instance_ids:
        raise HTTPException(status_code=403, detail="Nenhuma instância WhatsApp registrada para este usuário")
    # Valida que o JID pertence a uma das instâncias do usuário — sem fallback silencioso
    try:
        con_chk = _evo_conn()
        cur_chk = con_chk.cursor()
        cur_chk.execute(
            'SELECT 1 FROM vexus."Chat" WHERE "remoteJid" = %s AND "instanceId" = ANY(%s) LIMIT 1',
            (jid, instance_ids)
        )
        owns = cur_chk.fetchone()
        con_chk.close()
        if not owns:
            raise HTTPException(status_code=403, detail="Acesso negado a esta conversa")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar propriedade da conversa: {e}")
    try:
        con = _evo_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if before_ts:
            cur.execute("""
                SELECT
                    m."key"->>'id'        AS msg_id,
                    m."key"->>'fromMe'    AS from_me,
                    m."key"->>'remoteJid' AS remote_jid,
                    m."pushName"          AS push_name,
                    m."message"           AS message,
                    m."messageTimestamp"  AS ts,
                    m."messageType"       AS msg_type
                FROM vexus."Message" m
                WHERE m."key"->>'remoteJid' = %s
                  AND m."messageTimestamp" IS NOT NULL
                  AND m."messageTimestamp" < %s
                ORDER BY m."messageTimestamp" DESC
                LIMIT %s
            """, (jid, before_ts, limit))
            rows = list(reversed(cur.fetchall()))
        else:
            cur.execute("""
                SELECT
                    m."key"->>'id'        AS msg_id,
                    m."key"->>'fromMe'    AS from_me,
                    m."key"->>'remoteJid' AS remote_jid,
                    m."pushName"          AS push_name,
                    m."message"           AS message,
                    m."messageTimestamp"  AS ts,
                    m."messageType"       AS msg_type
                FROM vexus."Message" m
                WHERE m."key"->>'remoteJid' = %s
                  AND m."messageTimestamp" IS NOT NULL
                ORDER BY m."messageTimestamp" DESC
                LIMIT %s
            """, (jid, limit))
            rows = list(reversed(cur.fetchall()))
        con.close()

        # Busca também respostas da IA no nexus.messages
        try:
            crm_con = _agents_conn()
            crm_cur = crm_con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            crm_cur.execute("""
                SELECT direction, content, agent_type,
                       EXTRACT(EPOCH FROM created_at)::int AS ts
                FROM nexus.messages
                WHERE contact_jid = %s AND user_email = %s
                ORDER BY created_at ASC
            """, (jid, user_email))
            ai_rows = {r["ts"]: r for r in crm_cur.fetchall()}
            crm_con.close()
        except Exception:
            ai_rows = {}

        result = []
        for r in rows:
            ts   = r["ts"]
            msg  = r["message"] or {}
            text = _extract_text(msg)
            media_url, media_name = _extract_media(msg)
            agent_type = ""
            if ai_rows.get(ts):
                agent_type = ai_rows[ts].get("agent_type", "")
            result.append({
                "from_me":    r["from_me"] == "true" or r["from_me"] is True,
                "text":       text,
                "ts":         ts,
                "msg_type":   r["msg_type"],
                "agent_type": agent_type,
                "media_url":  media_url,
                "media_name": media_name,
                "msg_id":     r["msg_id"],
                "remote_jid": r["remote_jid"],
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/inbox/media/{msg_id}")
async def inbox_media(msg_id: str, jid: str, current_user: dict = Depends(get_current_user)):
    """Descriptografa e serve mídia do WhatsApp via Evolution API."""
    import httpx, base64
    from fastapi.responses import Response as FastResponse
    evo_url = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
    evo_key = os.getenv("EVOLUTION_API_KEY", "vexus_evolution_key_change_me")

    # Busca o tipo e nome do arquivo no banco
    try:
        con = _evo_conn()
        cur = con.cursor()
        cur.execute("""
            SELECT "messageType", "message"
            FROM vexus."Message"
            WHERE "key"->>'id' = %s AND "key"->>'remoteJid' = %s
            LIMIT 1
        """, (msg_id, jid))
        row = cur.fetchone()
        con.close()
        if not row:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        msg_type, message = row
        from_me_flag = False  # já temos o jid, não precisa
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Resolve o nome real da instância para este JID (evita hardcode)
    instance_name = "victor"  # fallback
    try:
        con_i = _evo_conn()
        cur_i = con_i.cursor()
        cur_i.execute("""
            SELECT i.name FROM vexus."Instance" i
            JOIN vexus."Chat" c ON c."instanceId" = i.id
            WHERE c."remoteJid" = %s
            LIMIT 1
        """, (jid,))
        row_i = cur_i.fetchone()
        con_i.close()
        if row_i:
            instance_name = row_i[0]
        else:
            crm_i = _crm_conn()
            cur_i2 = crm_i.cursor()
            cur_i2.execute(
                "SELECT instance_name FROM nexus.whatsapp_instances WHERE user_email = %s LIMIT 1",
                (current_user["email"],)
            )
            fb = cur_i2.fetchone()
            crm_i.close()
            if fb:
                instance_name = fb[0]
    except Exception:
        pass

    # Chama Evolution API para descriptografar
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{evo_url}/chat/getBase64FromMediaMessage/{instance_name}",
                headers={"apikey": evo_key, "Content-Type": "application/json"},
                json={"message": {"key": {"id": msg_id, "remoteJid": jid, "fromMe": False}, "messageType": msg_type}, "convertToMp4": False}
            )
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Evolution API: {resp.text[:200]}")
        data = resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    b64 = data.get("base64", "")
    if not b64:
        raise HTTPException(status_code=502, detail="Mídia não disponível")

    file_bytes = base64.b64decode(b64)
    mimetype = data.get("mimetype", "application/octet-stream")
    filename = data.get("fileName") or f"media.{mimetype.split('/')[-1]}"

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return FastResponse(content=file_bytes, media_type=mimetype, headers=headers)


class SendMessageRequest(BaseModel):
    jid: str
    number: str
    text: str


@app.post("/inbox/send")
async def inbox_send(req: SendMessageRequest, current_user: dict = Depends(get_current_user)):
    """Envia mensagem manual via Evolution API."""
    import httpx
    evo_url = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
    evo_key = os.getenv("EVOLUTION_API_KEY", "vexus_evolution_key_change_me")
    user_email = current_user["email"]

    # 1. Busca instância do usuário logado em nexus.whatsapp_instances
    instance = None
    try:
        con = _crm_conn()
        cur = con.cursor()
        cur.execute(
            "SELECT instance_name FROM nexus.whatsapp_instances WHERE user_email = %s ORDER BY created_at DESC LIMIT 1",
            (user_email,)
        )
        row = cur.fetchone()
        con.close()
        if row:
            instance = row[0]
    except Exception:
        pass

    # 2. Fallback: qualquer instância aberta na Evolution API
    if not instance:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{evo_url}/instance/fetchInstances", headers={"apikey": evo_key})
                if r.status_code == 200:
                    insts = r.json()
                    if not isinstance(insts, list):
                        insts = [insts]
                    for inst in insts:
                        if inst.get("connectionStatus") == "open":
                            instance = inst.get("name")
                            break
        except Exception:
            pass

    if not instance:
        raise HTTPException(status_code=503, detail="Nenhuma instância WhatsApp encontrada. Conecte um número em Integrações → WhatsApp.")

    try:
        # @lid = protocolo multi-device do WhatsApp, precisamos do número real
        if req.jid.endswith("@lid"):
            # Tenta encontrar número @s.whatsapp.net pelo nome do contato
            try:
                evo_con = _evo_conn()
                evo_cur = evo_con.cursor()
                # Resolve instância do usuário para filtrar corretamente
                _inst_ids_send = _get_user_instance_ids(current_user["email"])
                evo_cur.execute("""
                    SELECT c2."remoteJid"
                    FROM vexus."Contact" c2
                    JOIN vexus."Contact" c1 ON c1."instanceId" = c2."instanceId"
                       AND c1."remoteJid" = %s
                       AND c1."pushName" IS NOT NULL
                       AND LOWER(c2."pushName") = LOWER(c1."pushName")
                    WHERE c2."instanceId" = ANY(%s)
                      AND c2."remoteJid" LIKE '%%@s.whatsapp.net'
                    LIMIT 1
                """, (req.jid, _inst_ids_send))
                row = evo_cur.fetchone()
                evo_con.close()
                if row:
                    recipient = row[0].split("@")[0]
                else:
                    raise HTTPException(status_code=422,
                        detail="Contato @lid não tem número cadastrado. Aguarde ele enviar uma nova mensagem.")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(status_code=422,
                    detail="Contato @lid — não foi possível resolver o número. Aguarde nova mensagem do contato.")
        else:
            recipient = req.number

        # Garante formato correto do número (sem @s.whatsapp.net, sem @lid)
        clean_number = recipient.split("@")[0] if "@" in recipient else recipient
        # Remove caracteres não numéricos exceto +
        import re as _re
        clean_number = _re.sub(r"[^\d]", "", clean_number)

        logger.info(f"📤 inbox_send: instance={instance} number={clean_number} text={req.text[:40]}")

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{evo_url}/message/sendText/{instance}",
                headers={"apikey": evo_key, "Content-Type": "application/json"},
                json={"number": clean_number, "text": req.text}
            )
        if resp.status_code in (200, 201):
            return {"status": "sent"}
        # Extrai mensagem de erro da Evolution API
        try:
            err_body = resp.json()
            err_msg  = err_body.get("message") or err_body.get("error") or resp.text[:200]
        except Exception:
            err_msg = resp.text[:200]
        logger.error(f"❌ inbox_send Evolution API {resp.status_code}: {err_msg}")
        raise HTTPException(status_code=502, detail=f"WhatsApp erro: {err_msg}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Stripe / Billing Routes =====

STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Price IDs por plano × período
_STRIPE_PRICES = {
    ("starter",    "monthly"): os.getenv("STRIPE_PRICE_STARTER_MONTHLY", ""),
    ("starter",    "annual"):  os.getenv("STRIPE_PRICE_STARTER_ANNUAL",  ""),
    ("pro",        "monthly"): os.getenv("STRIPE_PRICE_PRO_MONTHLY",     ""),
    ("pro",        "annual"):  os.getenv("STRIPE_PRICE_PRO_ANNUAL",      ""),
    ("enterprise", "monthly"): os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", ""),
    ("enterprise", "annual"):  os.getenv("STRIPE_PRICE_ENTERPRISE_ANNUAL",  ""),
}

# Mapa inverso: price_id → nome do plano (para webhook)
_PRICE_TO_PLAN = {v: k[0] for k, v in _STRIPE_PRICES.items() if v}


# ─── Quick Replies ─────────────────────────────────────────────────────────────

class QuickReplyCreate(BaseModel):
    title: str
    content: str


@app.get("/inbox/quick-replies")
async def list_quick_replies(current_user: dict = Depends(get_current_user)):
    import psycopg2.extras
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, title, content, created_at FROM nexus.quick_replies WHERE user_email = %s ORDER BY title ASC",
            (user_email,)
        )
        rows = cur.fetchall()
        return [{"id": r["id"], "title": r["title"], "content": r["content"]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.post("/inbox/quick-replies", status_code=201)
async def create_quick_reply(payload: QuickReplyCreate, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    if not payload.title.strip() or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Título e conteúdo são obrigatórios")
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO nexus.quick_replies (user_email, title, content) VALUES (%s, %s, %s) RETURNING id",
            (user_email, payload.title.strip(), payload.content.strip())
        )
        new_id = cur.fetchone()[0]
        con.commit()
        return {"id": new_id, "title": payload.title.strip(), "content": payload.content.strip()}
    except Exception as e:
        con.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


@app.delete("/inbox/quick-replies/{reply_id}", status_code=204)
async def delete_quick_reply(reply_id: int, current_user: dict = Depends(get_current_user)):
    user_email = current_user["email"]
    con = _crm_conn()
    try:
        cur = con.cursor()
        cur.execute(
            "DELETE FROM nexus.quick_replies WHERE id = %s AND user_email = %s",
            (reply_id, user_email)
        )
        con.commit()
    except Exception as e:
        con.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        con.close()


class CheckoutRequest(BaseModel):
    tier: str = "pro"       # starter | pro | enterprise
    plan: str = "monthly"   # monthly | annual
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@app.post("/billing/checkout")
async def create_checkout(req: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    """Gera uma sessão de Checkout Stripe para upgrade de plano."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe não configurado. Configure STRIPE_SECRET_KEY no servidor.")
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        tier = req.tier.lower()
        period = req.plan.lower()
        price_id = _STRIPE_PRICES.get((tier, period), "")
        if not price_id:
            raise HTTPException(status_code=503, detail=f"Price ID não configurado para {tier}/{period}.")

        base = os.getenv("APP_BASE_URL", "https://api.nexuscrm.tech")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=current_user["email"],
            metadata={"user_email": current_user["email"], "tier": tier, "plan": period},
            success_url=req.success_url or f"{base}/dashboard?upgrade=success",
            cancel_url=req.cancel_url  or f"{base}/payment",
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/billing/webhook")
async def stripe_webhook(request: Request):
    """Recebe eventos do Stripe e atualiza o plano do usuário."""
    if not STRIPE_SECRET_KEY:
        return {"status": "stripe not configured"}
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        payload    = await request.body()
        sig_header = request.headers.get("stripe-signature", "")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET) if STRIPE_WEBHOOK_SECRET else stripe.Event.construct_from({"type": "unknown"}, stripe.api_key)
        except Exception:
            raise HTTPException(status_code=400, detail="Assinatura inválida")

        if event["type"] in ("checkout.session.completed", "invoice.paid"):
            obj        = event["data"]["object"]
            user_email = obj.get("customer_email") or obj.get("metadata", {}).get("user_email", "")
            if user_email:
                # Descobre o tier pelo price_id da linha (invoice) ou metadata (checkout)
                meta = obj.get("metadata", {})
                tier = meta.get("tier", "")
                if not tier:
                    lines = obj.get("lines", {}).get("data", []) or []
                    price_id = lines[0].get("price", {}).get("id", "") if lines else ""
                    tier = _PRICE_TO_PLAN.get(price_id, "pro")
                con = _agents_conn()
                cur = con.cursor()
                cur.execute("UPDATE nexus.users SET plan=%s WHERE email=%s", (tier, user_email))
                con.commit()
                con.close()
                logger.info(f"✅ Stripe: plano atualizado para '{tier}' → {user_email}")

        elif event["type"] in ("customer.subscription.deleted", "invoice.payment_failed"):
            obj        = event["data"]["object"]
            user_email = obj.get("customer_email") or obj.get("metadata", {}).get("user_email", "")
            if user_email:
                import psycopg2
                con = _agents_conn()
                cur = con.cursor()
                cur.execute("UPDATE nexus.users SET plan='trial' WHERE email=%s", (user_email,))
                con.commit()
                con.close()
                logger.info(f"⚠️  Stripe: plano revertido para 'trial' → {user_email}")

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"status": "error", "detail": str(e)}


# ===== Appointments Routes =====


@app.get("/appointments")
async def get_appointments():
    """Get all appointments (no auth required for demo)."""
    return [
        {
            "id": 1,
            "patient_name": "João Silva",
            "service": "Consulta Geral",
            "date": "2026-02-23",
            "time": "14:00",
            "status": "confirmado",
        },
        {
            "id": 2,
            "patient_name": "Maria Santos",
            "service": "Limpeza",
            "date": "2026-02-23",
            "time": "15:30",
            "status": "pendente",
        },
        {
            "id": 3,
            "patient_name": "Carlos Mendes",
            "service": "Extração",
            "date": "2026-02-24",
            "time": "09:00",
            "status": "confirmado",
        },
    ]


@app.post("/api/send_message")
async def send_whatsapp_message(request: dict):
    """Send WhatsApp message (for testing)."""
    phone = request.get("phone")
    message = request.get("message")
    clinic_id = request.get("clinic_id")

    if not phone or not message:
        raise HTTPException(status_code=400, detail="phone and message are required")

    # Mock WhatsApp response
    response_text = f"Mensagem recebida: {message}\n\nResposta automática: Obrigado por entrar em contato conosco!"

    return {
        "status": "sent",
        "phone": phone,
        "message": message,
        "response": response_text,
        "timestamp": datetime.utcnow(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
