"""
🚀 ADMIN DASHBOARD BACKEND - Gerenciar Tokens e Configurações
Sistema para clientes adicionar suas credenciais/tokens
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import json
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

# Database imports
from sqlalchemy.orm import Session
from ..database import SessionLocal, engine
import importlib.util
import os

# Import models directly
models_path = os.path.join(os.path.dirname(__file__), '..', 'models.py')
spec = importlib.util.spec_from_file_location("models", models_path)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
User = models.User
Base = models.Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# ═════════════════════════════════════════════════════════════════════════════
# SEGURANÇA
# ═════════════════════════════════════════════════════════════════════════════

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nexus-crm-secret-key")
ALGORITHM = "HS256"

# ═════════════════════════════════════════════════════════════════════════════
# MODELOS
# ═════════════════════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokensConfig(BaseModel):
    whatsapp_token: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None
    telegram_token: Optional[str] = None
    sendgrid_key: Optional[str] = None
    email_from: Optional[str] = None
    meta_token: Optional[str] = None
    instagram_id: Optional[str] = None
    facebook_id: Optional[str] = None

# ═════════════════════════════════════════════════════════════════════════════
# DATABASE SIMULADO - REMOVIDO PARA PERSISTÊNCIA
# ═════════════════════════════════════════════════════════════════════════════

# USERS_DB = {}  # Removido - agora usa PostgreSQL
# TOKENS_DB = {}  # Removido - tokens armazenados no campo JSON do usuário

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI dependency
from fastapi import Depends

def get_password_hash(password):
    # Truncate password string to reasonable length before encoding for bcrypt
    if password and len(password) > 50:  # truncate to 50 chars to be safe
        password = password[:50]
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    # Truncate password string to reasonable length before encoding for bcrypt
    if plain_password and len(plain_password) > 50:  # truncate to 50 chars to be safe
        plain_password = plain_password[:50]
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(email: str, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        return email
    except:
        return None

def get_current_user(token: str):
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    return email

# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    """Registrar novo cliente"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        company_name=user.company_name,
        tokens={}
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(user.email)
    
    return {
        "success": True,
        "message": "Usuário registrado com sucesso!",
        "token": token,
        "user": {
            "email": user.email,
            "company_name": user.company_name,
            "full_name": user.full_name
        }
    }

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Fazer login"""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    token = create_access_token(credentials.email)
    
    return {
        "success": True,
        "token": token,
        "user": {
            "email": credentials.email,
            "company_name": user.company_name,
            "full_name": user.name
        }
    }

@router.post("/tokens")
def add_tokens(tokens: TokensConfig, token: str = Query(...), db: Session = Depends(get_db)):
    """Adicionar/atualizar tokens do cliente"""
    email = get_current_user(token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    tokens_dict = {}
    if tokens.whatsapp_token:
        tokens_dict["WHATSAPP_ACCESS_TOKEN"] = tokens.whatsapp_token
    if tokens.whatsapp_phone_id:
        tokens_dict["WHATSAPP_PHONE_ID"] = tokens.whatsapp_phone_id
    if tokens.telegram_token:
        tokens_dict["TELEGRAM_BOT_TOKEN"] = tokens.telegram_token
    if tokens.sendgrid_key:
        tokens_dict["SENDGRID_API_KEY"] = tokens.sendgrid_key
    if tokens.email_from:
        tokens_dict["EMAIL_FROM"] = tokens.email_from
    if tokens.meta_token:
        tokens_dict["META_BUSINESS_TOKEN"] = tokens.meta_token
    if tokens.instagram_id:
        tokens_dict["INSTAGRAM_BUSINESS_ID"] = tokens.instagram_id
    if tokens.facebook_id:
        tokens_dict["FACEBOOK_PAGE_ID"] = tokens.facebook_id
    
    user.tokens = tokens_dict
    db.commit()
    
    return {
        "success": True,
        "message": "Tokens salvos com sucesso!",
        "tokens_count": len(tokens_dict)
    }

@router.get("/tokens")
def get_tokens(token: str = Query(...), db: Session = Depends(get_db)):
    """Obter tokens do cliente (mascarados)"""
    email = get_current_user(token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    tokens = user.tokens or {}
    
    masked_tokens = {}
    for key, value in tokens.items():
        if value and len(value) > 10:
            masked_tokens[key] = value[:5] + "***" + value[-5:]
        else:
            masked_tokens[key] = "***"
    
    return {
        "tokens": masked_tokens,
        "configured": len(tokens),
        "total_channels": 4
    }

@router.get("/status")
def get_status(token: str = Query(...), db: Session = Depends(get_db)):
    """Obter status de configuração do cliente"""
    email = get_current_user(token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    tokens = user.tokens or {}
    
    channels = {
        "whatsapp": "WHATSAPP_ACCESS_TOKEN" in tokens,
        "telegram": "TELEGRAM_BOT_TOKEN" in tokens,
        "email": "SENDGRID_API_KEY" in tokens,
        "meta": "META_BUSINESS_TOKEN" in tokens
    }
    
    return {
        "user": {
            "email": email,
            "company": user.company_name,
            "name": user.name,
            "created_at": user.created_at.isoformat()
        },
        "channels": channels,
        "configured_count": sum(channels.values()),
        "total_channels": len(channels),
        "apis_status": {
            "crm": "operational",
            "webhook": "operational",
            "send_message": "operational"
        }
    }

@router.delete("/tokens/{channel}")
def delete_token(channel: str, token: str = Query(...), db: Session = Depends(get_db)):
    """Deletar um token específico"""
    email = get_current_user(token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    channel_key_map = {
        "whatsapp": "WHATSAPP_ACCESS_TOKEN",
        "telegram": "TELEGRAM_BOT_TOKEN",
        "email": "SENDGRID_API_KEY",
        "meta": "META_BUSINESS_TOKEN"
    }
    
    channel_key = channel_key_map.get(channel)
    tokens = user.tokens or {}
    if not channel_key or channel_key not in tokens:
        raise HTTPException(status_code=404, detail="Token não encontrado")
    
    del tokens[channel_key]
    user.tokens = tokens
    db.commit()
    
    return {"success": True, "message": f"Token de {channel} deletado"}

@router.get("/user")
def get_user_profile(token: str = Query(...), db: Session = Depends(get_db)):
    """Obter perfil do usuário"""
    email = get_current_user(token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {
        "email": email,
        "company_name": user.company_name,
        "full_name": user.name,
        "created_at": user.created_at.isoformat(),
        "tokens_configured": len(user.tokens or {})
    }

@router.post("/refresh")
def refresh_token(token: str = Query(...)):
    """Renovar token JWT"""
    email = get_current_user(token)
    new_token = create_access_token(email)
    return {
        "success": True,
        "message": "Token renovado com sucesso!",
        "token": new_token,
        "user": {"email": email}
    }

@router.post("/logout")
def logout(token: str = Query(...)):
    """Fazer logout"""
    email = get_current_user(token)
    
    return {
        "success": True,
        "message": "Logout realizado com sucesso!",
        "email": email
    }

# ═════════════════════════════════════════════════════════════════════════════
# FRONTEND HTML/CSS/JS
# ═════════════════════════════════════════════════════════════════════════════

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus CRM - Painel de Controle</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .header h1 { color: #333; margin-bottom: 10px; }
        .header p { color: #666; }
        .card { background: white; border-radius: 10px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .channel-icon { font-size: 40px; margin-bottom: 15px; }
        .channel-name { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }
        .channel-status { display: inline-block; padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 15px; }
        .status-active { background: #d4edda; color: #155724; }
        .status-inactive { background: #f8d7da; color: #721c24; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        input, textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; font-size: 13px; }
        input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px; }
        button.danger { background: #f5576c; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .success-message, .error-message { padding: 15px; border-radius: 5px; margin-bottom: 20px; display: none; }
        .success-message { background: #d4edda; color: #155724; }
        .error-message { background: #f8d7da; color: #721c24; }
        .tab-buttons { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { padding: 10px 20px; background: #f0f0f0; border: none; border-radius: 5px; cursor: pointer; font-weight: 500; }
        .tab-btn.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 20px; }
        .stat { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-value { font-size: 28px; font-weight: bold; color: #667eea; }
        .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Nexus CRM - Painel de Controle</h1>
            <p>Gerencie seus tokens e configure seus canais de comunicação</p>
            <div style="margin-top: 15px;">
                <button onclick="logout()" class="danger">Logout</button>
            </div>
        </div>
        
        <div class="success-message" id="successMsg"></div>
        <div class="error-message" id="errorMsg"></div>
        
        <div class="card">
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="switchTab(event, 'status')">Status</button>
                <button class="tab-btn" onclick="switchTab(event, 'tokens')">Tokens</button>
                <button class="tab-btn" onclick="switchTab(event, 'profile')">Perfil</button>
            </div>
            
            <div id="status" class="tab-content active">
                <h2>Status dos Canais</h2>
                <div class="grid" id="channelsGrid"><p>Carregando...</p></div>
            </div>
            
            <div id="tokens" class="tab-content">
                <h2>Adicionar/Atualizar Tokens</h2>
                <form onsubmit="saveTokens(event)">
                    <div class="form-row">
                        <div class="form-group">
                            <label>🟢 WhatsApp Access Token</label>
                            <input type="text" id="whatsapp_token" placeholder="EAA..." />
                        </div>
                        <div class="form-group">
                            <label>📱 WhatsApp Phone ID</label>
                            <input type="text" id="whatsapp_phone_id" placeholder="123456789" />
                        </div>
                    </div>
                    <div class="form-group">
                        <label>🤖 Telegram Bot Token</label>
                        <input type="text" id="telegram_token" placeholder="123456:ABC-DEF..." />
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>📧 SendGrid API Key</label>
                            <input type="password" id="sendgrid_key" placeholder="SG.sk_live_..." />
                        </div>
                        <div class="form-group">
                            <label>📨 Email From</label>
                            <input type="email" id="email_from" placeholder="noreply@seudominio.com" />
                        </div>
                    </div>
                    <button type="submit">💾 Salvar Tokens</button>
                </form>
            </div>
            
            <div id="profile" class="tab-content">
                <h2>Meu Perfil</h2>
                <div class="form-group">
                    <label>Nome Completo:</label>
                    <input type="text" id="full_name" readonly style="background: #f0f0f0;" />
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" id="email" readonly style="background: #f0f0f0;" />
                </div>
                <div class="form-group">
                    <label>Empresa:</label>
                    <input type="text" id="company" readonly style="background: #f0f0f0;" />
                </div>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value" id="stat_tokens">0</div>
                        <div class="stat-label">Tokens Configurados</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">4</div>
                        <div class="stat-label">Canais Disponíveis</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">17</div>
                        <div class="stat-label">APIs Ativas</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const API_URL = "/api/admin";
        const token = localStorage.getItem("auth_token");
        
        if (!token) window.location.href = "/login";
        
        function switchTab(event, tabName) {
            document.querySelectorAll(".tab-content").forEach(tab => tab.classList.remove("active"));
            document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
            document.getElementById(tabName).classList.add("active");
            event.target.classList.add("active");
            
            if (tabName === "status") loadStatus();
            if (tabName === "profile") loadProfile();
        }
        
        function showSuccess(message) {
            document.getElementById("successMsg").innerHTML = message;
            document.getElementById("successMsg").style.display = "block";
            setTimeout(() => document.getElementById("successMsg").style.display = "none", 5000);
        }
        
        function showError(message) {
            document.getElementById("errorMsg").innerHTML = message;
            document.getElementById("errorMsg").style.display = "block";
            setTimeout(() => document.getElementById("errorMsg").style.display = "none", 5000);
        }
        
        async function loadStatus() {
            try {
                const response = await fetch(`${API_URL}/status?token=${token}`);
                const data = await response.json();
                
                let html = '';
                const icons = { whatsapp: '🟢', telegram: '🤖', email: '📧', meta: '📸' };
                
                for (const [channel, active] of Object.entries(data.channels)) {
                    const status = active ? 'status-active' : 'status-inactive';
                    const text = active ? 'Ativo' : 'Inativo';
                    
                    html += `
                        <div class="card">
                            <div class="channel-icon">${icons[channel]}</div>
                            <div class="channel-name">${channel.charAt(0).toUpperCase() + channel.slice(1)}</div>
                            <span class="channel-status ${status}">${text}</span>
                            <button onclick="deleteToken('${channel}')" class="danger" style="width: 100%; margin-top: 10px; font-size: 12px;">Deletar Token</button>
                        </div>
                    `;
                }
                document.getElementById("channelsGrid").innerHTML = html;
            } catch (error) {
                showError("Erro ao carregar status");
            }
        }
        
        async function loadProfile() {
            try {
                const response = await fetch(`${API_URL}/user?token=${token}`);
                const data = await response.json();
                
                document.getElementById("full_name").value = data.full_name;
                document.getElementById("email").value = data.email;
                document.getElementById("company").value = data.company_name;
                document.getElementById("stat_tokens").textContent = data.tokens_configured;
            } catch (error) {
                showError("Erro ao carregar perfil");
            }
        }
        
        async function saveTokens(event) {
            event.preventDefault();
            
            const tokens = {
                whatsapp_token: document.getElementById("whatsapp_token").value || null,
                whatsapp_phone_id: document.getElementById("whatsapp_phone_id").value || null,
                telegram_token: document.getElementById("telegram_token").value || null,
                sendgrid_key: document.getElementById("sendgrid_key").value || null,
                email_from: document.getElementById("email_from").value || null
            };
            
            try {
                const response = await fetch(`${API_URL}/tokens?token=${token}`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(tokens)
                });
                
                const data = await response.json();
                showSuccess(`✅ ${data.tokens_count} token(s) salvos!`);
                setTimeout(() => loadStatus(), 2000);
            } catch (error) {
                showError("Erro ao salvar: " + error.message);
            }
        }
        
        async function deleteToken(channel) {
            if (!confirm(`Deletar token do ${channel}?`)) return;
            
            try {
                const response = await fetch(`${API_URL}/tokens/${channel}?token=${token}`, {
                    method: "DELETE"
                });
                const data = await response.json();
                showSuccess("✅ Token deletado!");
                loadStatus();
            } catch (error) {
                showError("Erro ao deletar token");
            }
        }
        
        function logout() {
            localStorage.removeItem("auth_token");
            window.location.href = "/login";
        }
        
        window.addEventListener("load", () => {
            loadStatus();
            loadProfile();
        });
    </script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus CRM - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { width: 100%; max-width: 400px; padding: 20px; }
        .card { background: white; border-radius: 10px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        .card h1 { color: #333; margin-bottom: 10px; font-size: 28px; }
        .card p { color: #666; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        .password-container { position: relative; }
        .password-container input { padding-right: 40px; }
        .toggle-password { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 16px; color: #666; }
        .toggle-password:hover { color: #333; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 10px; }
        .link { text-align: center; margin-top: 20px; color: #666; }
        .link a { color: #667eea; text-decoration: none; font-weight: bold; }
        .error { background: #f8d7da; color: #721c24; padding: 12px; border-radius: 5px; margin-bottom: 20px; display: none; }
        .success { background: #d4edda; color: #155724; padding: 12px; border-radius: 5px; margin-bottom: 20px; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🚀 Nexus CRM</h1>
            <p>Painel de Controle</p>
            
            <div class="error" id="errorMsg"></div>
            <div class="success" id="successMsg"></div>
            
            <div id="loginForm">
                <form onsubmit="handleLogin(event)">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="email" required />
                    </div>
                    <div class="form-group">
                        <label>Senha</label>
                        <div class="password-container">
                            <input type="password" id="password" required />
                            <button type="button" class="toggle-password" onclick="togglePassword('password')" title="Mostrar senha">
                                👁️
                            </button>
                        </div>
                    </div>
                    <button type="submit">Entrar</button>
                </form>
                <div class="link">
                    Não tem conta? <a onclick="switchMode()">Criar Conta</a>
                </div>
            </div>
            
            <div id="registerForm" style="display: none;">
                <form onsubmit="handleRegister(event)">
                    <div class="form-group">
                        <label>Nome Completo</label>
                        <input type="text" id="fullName" required />
                    </div>
                    <div class="form-group">
                        <label>Empresa</label>
                        <input type="text" id="company" required />
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="emailReg" required />
                    </div>
                    <div class="form-group">
                        <label>Senha</label>
                        <div class="password-container">
                            <input type="password" id="passwordReg" required />
                            <button type="button" class="toggle-password" onclick="togglePassword('passwordReg')" title="Mostrar senha">
                                👁️
                            </button>
                        </div>
                    </div>
                    <button type="submit">Criar Conta</button>
                </form>
                <div class="link">
                    Já tem conta? <a onclick="switchMode()">Entrar</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const API_URL = "/api/admin";
        
        function togglePassword(inputId) {
            const input = document.getElementById(inputId);
            const button = input.nextElementSibling;
            
            if (input.type === "password") {
                input.type = "text";
                button.textContent = "🙈";
                button.title = "Ocultar senha";
            } else {
                input.type = "password";
                button.textContent = "👁️";
                button.title = "Mostrar senha";
            }
        }
        
        function switchMode() {
            document.getElementById("loginForm").style.display = document.getElementById("loginForm").style.display === "none" ? "block" : "none";
            document.getElementById("registerForm").style.display = document.getElementById("registerForm").style.display === "none" ? "block" : "none";
        }
        
        function showError(message) {
            document.getElementById("errorMsg").innerHTML = message;
            document.getElementById("errorMsg").style.display = "block";
            setTimeout(() => document.getElementById("errorMsg").style.display = "none", 5000);
        }
        
        function showSuccess(message) {
            document.getElementById("successMsg").innerHTML = message;
            document.getElementById("successMsg").style.display = "block";
        }
        
        async function handleLogin(event) {
            event.preventDefault();
            
            try {
                const response = await fetch(`${API_URL}/login`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        email: document.getElementById("email").value,
                        password: document.getElementById("password").value
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.token) {
                    localStorage.setItem("auth_token", data.token);
                    showSuccess("✅ Login realizado! Redirecionando...");
                    setTimeout(() => window.location.href = "/dashboard", 1500);
                } else {
                    showError(data.detail || "Erro ao fazer login");
                }
            } catch (error) {
                showError("Erro: " + error.message);
            }
        }
        
        async function handleRegister(event) {
            event.preventDefault();
            
            try {
                const response = await fetch(`${API_URL}/register`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        email: document.getElementById("emailReg").value,
                        password: document.getElementById("passwordReg").value,
                        company_name: document.getElementById("company").value,
                        full_name: document.getElementById("fullName").value
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.token) {
                    localStorage.setItem("auth_token", data.token);
                    showSuccess("✅ Conta criada! Redirecionando...");
                    setTimeout(() => window.location.href = "/dashboard", 1500);
                } else {
                    showError(data.detail || "Erro ao criar conta");
                }
            } catch (error) {
                showError("Erro: " + error.message);
            }
        }
        
        if (localStorage.getItem("auth_token")) {
            window.location.href = "/dashboard";
        }
    </script>
</body>
</html>
"""

@router.get("/dashboard")
def dashboard():
    """Servir dashboard HTML"""
    return HTMLResponse(content=DASHBOARD_HTML)

@router.get("/login")
def login_page():
    """Servir página de login"""
    return HTMLResponse(content=LOGIN_HTML)
