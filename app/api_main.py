"""
FastAPI main application with routers.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.authentication import AuthCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

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


# ===== Mock Database =====
mock_users = {
    "admin@vexus.com": {
        "id": 1,
        "email": "admin@vexus.com",
        "password_hash": get_password_hash("admin123"),
        "name": "Admin Vexus",
        "role": "admin",
    },
    "victor226942@gmail.com": {
        "id": 2,
        "email": "victor226942@gmail.com",
        "password_hash": get_password_hash("226942Hd$"),
        "name": "Victor",
        "role": "user",
    }
}

def clear_user_from_mock(email: str):
    """Remove usuário da memória"""
    if email in mock_users:
        del mock_users[email]

# Mock companies and subscriptions (simple in-memory)
mock_companies = {}
mock_subscriptions = {}

mock_chats = {}
mock_leads = {}
mock_proposals = {}


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
    if request.email in mock_users:
        raise HTTPException(status_code=400, detail="User already exists")

    user = {
        "id": len(mock_users) + 1,
        "email": request.email,
        "password_hash": get_password_hash(request.password),
        "name": request.name,
        "role": "user",
    }
    mock_users[request.email] = user

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
    if request.email not in mock_users:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = mock_users[request.email]
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
    user = mock_users.get(current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
    }


@app.get("/verify-email")
async def verify_email(token: str):
    """Verify an email verification token."""
    email = verify_email_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = mock_users.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user["is_verified"] = True
    return {"msg": "E-mail verificado com sucesso"}


@app.post("/resend-verification")
async def resend_verification(current_user: dict = Depends(get_current_user)):
    """Resend email verification to current user."""
    user = mock_users.get(current_user["email"])
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
async def forgot_password(email: str):
    """Initiate password reset flow."""
    # Do not reveal whether user exists
    user = mock_users.get(email)
    if not user:
        return {"msg": "Se o e‑mail estiver cadastrado, você receberá um link"}

    token = create_password_reset_token(email)
    link = f"https://{os.getenv('DOMAIN','localhost')}/reset-password?token={token}"
    html = template_password_reset(link)
    await send_email(to=[email], subject="Redefinição de senha", html=html)
    return {"msg": "Se o e‑mail estiver cadastrado, você receberá um link"}


@app.post("/reset-password")
async def reset_password(token: str, new_password: str):
    """Reset password using token."""
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = mock_users.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user["password_hash"] = get_password_hash(new_password)
    return {"msg": "Senha redefinida com sucesso"}


@app.post("/company/invite")
async def invite_user(
    email: str, role: str = "member", current_user: dict = Depends(get_current_user)
):
    """Invite a user to current user's company."""
    inviter = mock_users.get(current_user["email"])
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
    if email in mock_users:
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
    if email in mock_users:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")

    user = {
        "id": len(mock_users) + 1,
        "email": email,
        "password_hash": get_password_hash(password),
        "name": email.split("@")[0],
        "role": payload.get("role", "member"),
        "company_id": payload.get("company_id"),
        "is_verified": True,
    }
    mock_users[email] = user
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
    user = mock_users.get(current_user["email"])
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
    user = mock_users.get(current_user["email"])
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


@app.post("/kb/upload")
async def upload_document(
    file_name: str, current_user: dict = Depends(get_current_user)
):
    """Upload document to knowledge base."""
    return {
        "status": "uploaded",
        "file": file_name,
        "user": current_user["email"],
        "timestamp": datetime.utcnow(),
    }


@app.post("/kb/query")
async def query_kb(query: KBQuery, current_user: dict = Depends(get_current_user)):
    """Query knowledge base."""
    # Mock response
    return {
        "query": query.query,
        "results": [
            {
                "id": 1,
                "source": "Tabela de Preços.pdf",
                "confidence": 0.94,
                "text": "Os planos disponíveis incluem Básico (R$500/mês), Premium (R$1500/mês) e Enterprise com customização...",
            },
            {
                "id": 2,
                "source": "Catálogo 2026.pdf",
                "confidence": 0.87,
                "text": "Para empresas em crescimento, recomendamos o plano Premium que inclui suporte prioritário...",
            },
        ],
        "timestamp": datetime.utcnow(),
    }


# ===== Leads/Pipeline Routes =====


@app.get("/leads")
async def get_leads(current_user: dict = Depends(get_current_user)):
    """Get all leads."""
    return {
        "leads": [
            {
                "id": 1,
                "name": "João Silva",
                "email": "joao@example.com",
                "score": 85,
                "stage": "Negociação",
            },
            {
                "id": 2,
                "name": "Maria Santos",
                "email": "maria@example.com",
                "score": 75,
                "stage": "Proposta",
            },
            {
                "id": 3,
                "name": "Carlos Mendes",
                "email": "carlos@example.com",
                "score": 62,
                "stage": "Qualificação",
            },
        ]
    }


@app.get("/leads/{lead_id}")
async def get_lead(lead_id: int, current_user: dict = Depends(get_current_user)):
    """Get lead details."""
    return {
        "id": lead_id,
        "name": f"Lead {lead_id}",
        "email": f"lead{lead_id}@example.com",
        "score": 85,
        "stage": "Negociação",
        "history": ["Contato", "Email enviado", "Proposta enviada"],
    }


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


@app.get("/agents")
async def get_agents(current_user: dict = Depends(get_current_user)):
    """Get all agents."""
    return {
        "agents": [
            {
                "id": 1,
                "name": "Agente Vendas",
                "model": "GPT-4",
                "status": "ativo",
                "performance": 0.87,
            },
            {
                "id": 2,
                "name": "Agente Knowledge",
                "model": "GPT-4",
                "status": "ativo",
                "performance": 0.94,
            },
            {
                "id": 3,
                "name": "Agente Email",
                "model": "GPT-3.5",
                "status": "ativo",
                "performance": 0.82,
            },
        ]
    }


@app.put("/agents/{agent_id}/config")
async def update_agent_config(
    agent_id: int, config: AgentConfig, current_user: dict = Depends(get_current_user)
):
    """Update agent configuration."""
    return {
        "id": agent_id,
        "config": config,
        "status": "atualizado",
        "timestamp": datetime.utcnow(),
    }


# ===== Analytics Routes =====


@app.get("/analytics/summary")
async def get_analytics_summary(current_user: dict = Depends(get_current_user)):
    """Get analytics summary."""
    return {
        "total_leads": 1247,
        "conversion_rate": 0.32,
        "avg_cycle_days": 18,
        "revenue_month": 127000,
        "leads_by_source": {
            "whatsapp": 0.35,
            "linkedin": 0.28,
            "website": 0.22,
            "email": 0.15,
        },
    }


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
