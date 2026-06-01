"""
Nexus CRM — Webhook Receiver
Recebe mensagens do WhatsApp (Evolution API), Telegram, Instagram e Email.
Para WhatsApp: se o agente tiver auto_respond=True, chama OpenAI e responde automaticamente.
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict
import logging
import os
import asyncio
import time
import httpx
from collections import defaultdict

logger = logging.getLogger(__name__)
router = APIRouter()

# Histórico de conversa por JID (em memória — últimas 20 mensagens por contato)
_conversation_history: Dict[str, list] = defaultdict(list)

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:3000")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "vexus_evolution_key_change_me")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL      = os.getenv("DATABASE_URL", "postgresql://vexus:vexus_password_123@localhost/vexus_crm")
# Banco da Evolution API (vexus."Chat", vexus."Message", vexus."Contact")
EVO_DB_URL        = os.getenv("EVOLUTION_DB_URL", "postgresql://vexus:vexus_password_123@localhost/vexus_crm")

# ── Persistent HTTP client (reused across all requests — no per-call overhead) ──
_http: httpx.AsyncClient | None = None

def _get_http() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(timeout=15)
    return _http

# ── AsyncOpenAI client (non-blocking — won't stall the event loop) ─────────────
_openai_client = None

def _get_openai():
    global _openai_client
    if _openai_client is None and OPENAI_API_KEY:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _openai_client

# ── Agent cache (30s TTL — avoids a DB query on every incoming message) ─────────
_agent_cache: dict = {"ts": 0.0, "agent": None}

# ── Context summarization — compressed history per JID ───────────────────────────
_context_cache: dict = {}          # jid -> summary string
_msg_counts: dict = defaultdict(int)  # jid -> total messages received
_doc_context_cache: dict = {}      # jid -> extracted PDF text (consumed once)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _db_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def _get_auto_respond_agent() -> dict | None:
    """Retorna o agente com auto_respond=True vinculado a esta instância, ou None."""
    try:
        import psycopg2.extras
        con = _db_conn()
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Qualquer agente ativo + auto_respond ligado serve; usa atendimento como padrão
        cur.execute("""
            SELECT a.* FROM nexus.agents a
            WHERE a.auto_respond = TRUE AND a.active = TRUE
            ORDER BY CASE a.type WHEN 'atendimento' THEN 1 WHEN 'vendas' THEN 2 ELSE 3 END
            LIMIT 1
        """)
        row = cur.fetchone()
        con.close()
        return dict(row) if row else None
    except Exception as e:
        logger.warning(f"⚠️  Não foi possível buscar agente: {e}")
        return None


async def _update_context_summary(jid: str) -> None:
    """Comprime o histórico da conversa em ~150 palavras e armazena no cache."""
    client = _get_openai()
    history = _conversation_history.get(jid, [])
    if not client or len(history) < 6:
        return
    try:
        text = "\n".join([
            f"{'Cliente' if m['role']=='user' else 'IA'}: {m['content'][:300]}"
            for m in history[-20:]
        ])
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Resuma a conversa em no máximo 150 palavras. Capture: intenção do cliente, informações pessoais, estágio do atendimento, objeções mencionadas."},
                {"role": "user", "content": text},
            ],
            max_tokens=200,
        )
        summary = resp.choices[0].message.content.strip()
        _context_cache[jid] = summary
        logger.debug(f"🧠 Contexto sintetizado para {jid}: {summary[:80]}...")
    except Exception as e:
        logger.debug(f"Context summary error: {e}")


async def _extract_lead_entities(jid: str, user_message: str) -> None:
    """Extrai dados estruturados da mensagem e enriquece o lead no PostgreSQL."""
    import json
    client = _get_openai()
    if not client:
        return
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": 'Extraia dados do cliente. Responda SOMENTE com JSON: {"nome": null, "telefone": null, "interesse": null, "objecao": null}. Use null se não encontrar.'},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            max_tokens=80,
        )
        data = json.loads(resp.choices[0].message.content)
        if any(v for v in data.values() if v):
            await asyncio.to_thread(_update_lead_from_entities, jid, data)
    except Exception as e:
        logger.debug(f"Entity extraction: {e}")


def _update_lead_from_entities(jid: str, entities: dict) -> None:
    """Atualiza o perfil do lead com entidades extraídas pela IA."""
    try:
        number = jid.split("@")[0]
        con = _db_conn()
        cur = con.cursor()
        cur.execute("SELECT id FROM nexus.leads WHERE phone = %s LIMIT 1", (number,))
        row = cur.fetchone()
        if not row:
            con.close()
            return
        lead_id = row[0]
        parts, vals = [], []
        if entities.get("nome"):
            parts.append("name = COALESCE(NULLIF(name, ''), %s)")
            vals.append(entities["nome"])
        notes_append = []
        if entities.get("interesse"):
            notes_append.append(f"[IA] Interesse: {entities['interesse']}")
        if entities.get("objecao"):
            notes_append.append(f"[IA] Objeção: {entities['objecao']}")
        if notes_append:
            parts.append("notes = CONCAT(COALESCE(notes,''), %s)")
            vals.append("\n" + "\n".join(notes_append))
        if parts:
            vals.append(lead_id)
            cur.execute(f"UPDATE nexus.leads SET {', '.join(parts)} WHERE id = %s", vals)
            con.commit()
            logger.info(f"✅ Lead #{lead_id} enriquecido automaticamente")
        con.close()
    except Exception as e:
        logger.debug(f"Lead entity update: {e}")


async def _get_agent_cached() -> dict | None:
    """Retorna agente ativo com cache de 30s para evitar query a cada mensagem."""
    now = time.monotonic()
    if now - _agent_cache["ts"] < 30:
        return _agent_cache["agent"]
    agent = await asyncio.to_thread(_get_auto_respond_agent)
    _agent_cache["ts"] = now
    _agent_cache["agent"] = agent
    return agent


async def _call_openai(agent: dict, jid: str, user_message: str,
                      image_url: str | None = None) -> str | None:
    """Chama OpenAI de forma totalmente async. Suporta visão (image_url) quando fornecido."""
    client = _get_openai()
    if not client:
        return None
    try:
        custom = (agent.get("system_prompt") or "").strip()
        if custom:
            system_prompt = custom + "\n\nVocê responde via WhatsApp. Seja breve e natural."
        else:
            system_prompt = (
                f"{agent.get('persona', 'Assistente cordial')}\n\n"
                f"{agent.get('instructions', 'Responda de forma clara e objetiva.')}\n\n"
                "Você responde via WhatsApp. Seja breve e natural. Responda sempre em português."
            )

        # Injeta contexto de documentos PDF processados em background
        doc_ctx = _doc_context_cache.get(jid, "")

        summary = _context_cache.get(jid, "")
        history = _conversation_history[jid][-6:]
        messages: list = [{"role": "system", "content": system_prompt}]
        if summary:
            messages.append({"role": "system", "content": f"Contexto anterior:\n{summary}"})
        if doc_ctx:
            messages.append({"role": "system", "content": f"Documento enviado pelo cliente:\n{doc_ctx}"})
            _doc_context_cache.pop(jid, None)  # usar apenas uma vez
        messages.extend(history)

        # Monta conteúdo do usuário — multimodal se houver imagem
        if image_url:
            model = "gpt-4o"  # vision requer gpt-4o ou superior
            user_content: list = []
            if user_message and user_message != "[Foto recebida]":
                user_content.append({"type": "text", "text": user_message})
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_url, "detail": "low"},
            })
            messages.append({"role": "user", "content": user_content})
        else:
            model = agent.get("model", "gpt-4o-mini")
            messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()

        _conversation_history[jid].append({"role": "user", "content": user_message})
        _conversation_history[jid].append({"role": "assistant", "content": reply})
        _conversation_history[jid] = _conversation_history[jid][-40:]
        return reply
    except Exception as e:
        logger.error(f"❌ OpenAI error: {e}")
        return None


async def _process_pdf_background(jid: str, pdf_url: str, filename: str) -> None:
    """Downloads a PDF from Evolution API media URL and extracts text into _doc_context_cache."""
    try:
        resp = await _get_http().get(pdf_url, follow_redirects=True)
        if resp.status_code != 200:
            return
        pdf_bytes = resp.content
        text_parts: list[str] = []
        try:
            import io
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages[:10]:  # cap at 10 pages
                    t = page.extract_text()
                    if t:
                        text_parts.append(t.strip())
            except ImportError:
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                        for page in pdf.pages[:10]:
                            t = page.extract_text()
                            if t:
                                text_parts.append(t.strip())
                except ImportError:
                    logger.debug("PDF parsing skipped — install pypdf or pdfplumber")
                    return
        except Exception as ex:
            logger.debug(f"PDF parse error: {ex}")
            return
        if text_parts:
            extracted = "\n\n".join(text_parts)[:3000]
            _doc_context_cache[jid] = f"[{filename}]\n{extracted}"
            logger.info(f"📄 PDF extraído para {jid}: {len(extracted)} chars")
    except Exception as e:
        logger.debug(f"PDF background error: {e}")


def _save_chat_name(jid: str, name: str) -> None:
    """Persists pushName into vexus.Chat.name if currently empty (best-effort)."""
    if not name:
        return
    try:
        con = _db_conn()
        cur = con.cursor()
        cur.execute("""
            UPDATE vexus."Chat" SET name = %s
            WHERE "remoteJid" = %s AND (name IS NULL OR name = '')
        """, (name, jid))
        con.commit()
        con.close()
    except Exception as e:
        logger.debug(f"Chat name save: {e}")


def _resolve_instance_id(instance_name: str) -> str | None:
    """Resolve o UUID da instância pelo nome consultando vexus.Instance."""
    try:
        import psycopg2 as _pg2
        con = _pg2.connect(EVO_DB_URL)
        cur = con.cursor()
        cur.execute('SELECT id FROM vexus."Instance" WHERE name = %s LIMIT 1', (instance_name,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else None
    except Exception:
        return None


# Cache de instance_name → instanceId para não ir ao banco a cada mensagem
_instance_id_cache: dict[str, str] = {}


def _upsert_chat(jid: str, name: str, instance_name: str = "") -> None:
    """Cria ou atualiza registro na vexus.Chat para que o contato apareça no inbox."""
    if not jid:
        return
    try:
        import uuid, psycopg2 as _pg2

        # Resolve instanceId dinamicamente — sem hardcode
        instance_id = None
        if instance_name:
            if instance_name not in _instance_id_cache:
                _instance_id_cache[instance_name] = _resolve_instance_id(instance_name) or ""
            instance_id = _instance_id_cache[instance_name] or None

        con = _pg2.connect(EVO_DB_URL)
        cur = con.cursor()
        if instance_id:
            cur.execute(
                'UPDATE vexus."Chat" SET "updatedAt" = NOW(), "unreadMessages" = "unreadMessages" + 1 '
                'WHERE "remoteJid" = %s AND "instanceId" = %s',
                (jid, instance_id)
            )
        else:
            cur.execute(
                'UPDATE vexus."Chat" SET "updatedAt" = NOW(), "unreadMessages" = "unreadMessages" + 1 '
                'WHERE "remoteJid" = %s',
                (jid,)
            )
        if cur.rowcount == 0 and instance_id:
            cur.execute(
                'INSERT INTO vexus."Chat" (id, "remoteJid", "instanceId", "unreadMessages", "createdAt", "updatedAt", name) '
                'VALUES (%s, %s, %s, 1, NOW(), NOW(), %s) ON CONFLICT DO NOTHING',
                (str(uuid.uuid4()), jid, instance_id, name or None)
            )
        con.commit()
        con.close()
    except Exception as e:
        logger.warning(f"Chat upsert failed for {jid}: {e}")


def _upsert_contact(jid: str, name: str) -> None:
    """Upsert pushName into vexus.Contact so @lid JIDs get a name for the inbox JOIN."""
    if not name or not jid:
        return
    try:
        con = _db_conn()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO vexus."Contact" ("remoteJid", "pushName", "updatedAt")
            VALUES (%s, %s, NOW())
            ON CONFLICT ("remoteJid") DO UPDATE
              SET "pushName" = EXCLUDED."pushName",
                  "updatedAt" = NOW()
            WHERE vexus."Contact"."pushName" IS NULL
               OR vexus."Contact"."pushName" = ''
        """, (jid, name))
        con.commit()
        con.close()
    except Exception as e:
        logger.debug(f"Contact upsert: {e}")


def _save_message(direction: str, contact_jid: str, contact_name: str, content: str, agent_type: str):
    """Persiste mensagem na tabela nexus.messages (best-effort, nunca quebra o webhook)."""
    try:
        import psycopg2
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        # Descobre user_email pelo agente ativo (ou usa 'system' como fallback)
        cur.execute("""
            SELECT user_email FROM nexus.agents
            WHERE auto_respond = TRUE AND active = TRUE LIMIT 1
        """)
        row = cur.fetchone()
        user_email = row[0] if row else "system"
        cur.execute("""
            INSERT INTO nexus.messages (user_email, direction, channel, contact_jid, contact_name, content, agent_type)
            VALUES (%s, %s, 'whatsapp', %s, %s, %s, %s)
        """, (user_email, direction, contact_jid, contact_name, content, agent_type))
        con.commit()
        con.close()
    except Exception as e:
        logger.warning(f"⚠️  Não foi possível salvar mensagem: {e}")


async def _send_whatsapp_text(instance_name: str, number: str, text: str) -> bool:
    """Envia mensagem de texto via Evolution API usando cliente HTTP persistente."""
    url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": number, "text": text}
    try:
        resp = await _get_http().post(url, headers=headers, json=payload)
        ok = resp.status_code in (200, 201)
        if ok:
            logger.info(f"✅ WA enviado para {number}")
        else:
            logger.warning(f"⚠️  Evolution API {resp.status_code}: {resp.text[:200]}")
        return ok
    except Exception as e:
        logger.error(f"❌ Erro ao enviar WA: {e}")
        return False


# ─── WhatsApp Webhook ──────────────────────────────────────────────────────────

@router.post("/webhooks/whatsapp/{instance_name}")
async def webhook_whatsapp(instance_name: str, request: Request):
    """
    Recebe eventos da Evolution API.
    Formato v2:  { "event": "messages.upsert", "instance": "...", "data": { "key": {...}, "message": {...} } }
    Também suporta o formato legado com data.messages[].
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}  # corpo vazio/inválido — não quebrar

    event = payload.get("event", "")

    # Só processa mensagens recebidas
    if event not in ("messages.upsert", "message.upsert"):
        return {"status": "ok", "event": event}

    data = payload.get("data", {})

    # Suporte a ambos os formatos (objeto único ou lista)
    if isinstance(data, list):
        msgs = data
    elif "messages" in data:
        msgs = data["messages"]
    else:
        msgs = [data]

    for msg in msgs:
        key = msg.get("key", {})

        # Ignora mensagens enviadas pelo próprio bot
        if key.get("fromMe"):
            continue

        jid = key.get("remoteJid", "")
        # Ignora grupos
        if jid.endswith("@g.us"):
            continue

        # Extrai número limpo (sem @s.whatsapp.net)
        number = jid.split("@")[0] if "@" in jid else jid

        push_name = msg.get("pushName", "")

        # Extrai texto e mídia
        raw_msg  = msg.get("message", {})
        img_msg  = raw_msg.get("imageMessage")
        doc_msg  = raw_msg.get("documentMessage")
        vid_msg  = raw_msg.get("videoMessage")

        text = (
            raw_msg.get("conversation")
            or raw_msg.get("extendedTextMessage", {}).get("text")
            or msg.get("text")
            or msg.get("body")
            or ""
        ).strip()

        # Detecta imagem: usa legenda como texto, marca para vision
        image_url: str | None = None
        if img_msg:
            text      = (img_msg.get("caption") or text or "").strip()
            image_url = img_msg.get("mediaUrl") or img_msg.get("url") or img_msg.get("jpegThumbnail") or ""
            if not text:
                text = "[Foto recebida]"
            logger.info(f"📸 WA [{instance_name}] imagem de {push_name} ({number}): caption={text[:60]}")

        # Detecta documento PDF: extrai texto em background para injetar no contexto
        elif doc_msg:
            doc_caption = doc_msg.get("caption") or doc_msg.get("fileName") or "documento"
            pdf_url     = doc_msg.get("mediaUrl") or doc_msg.get("url") or ""
            if pdf_url:
                asyncio.create_task(_process_pdf_background(jid, pdf_url, doc_caption))
            text = text or f"[Documento recebido: {doc_caption}]"
            logger.info(f"📄 WA [{instance_name}] doc de {push_name} ({number}): {doc_caption}")

        elif vid_msg:
            text = (vid_msg.get("caption") or text or "[Vídeo recebido]").strip()

        if not text and not image_url:
            continue  # sticker ou mídia sem conteúdo útil

        logger.info(f"📥 WA [{instance_name}] de {push_name} ({number}): {text[:80]}")

        # Garante que o chat existe no inbox e salva nome/contato
        asyncio.create_task(asyncio.to_thread(_upsert_chat, jid, push_name, instance_name))
        if push_name:
            asyncio.create_task(asyncio.to_thread(_save_chat_name, jid, push_name))
            asyncio.create_task(asyncio.to_thread(_upsert_contact, jid, push_name))

        # Salva em background — não bloqueia a resposta ao webhook
        asyncio.create_task(asyncio.to_thread(_save_message, "in", jid, push_name, text, ""))

        # Contagem e triggers de inteligência em background
        _msg_counts[jid] += 1
        if _msg_counts[jid] % 10 == 0:
            asyncio.create_task(_update_context_summary(jid))
        if len(text) > 25:
            asyncio.create_task(_extract_lead_entities(jid, text))

        # Busca agente via cache (evita query ao banco a cada mensagem)
        agent = await _get_agent_cached()
        if not agent:
            logger.info(f"ℹ️  Nenhum agente com auto_respond ativo — mensagem registrada")
            continue

        logger.info(f"🤖 Agente [{agent['name']}] respondendo para {number}...")

        # Gera resposta com OpenAI (passa image_url para visão multimodal)
        reply = await _call_openai(agent, jid, text, image_url=image_url)
        if not reply:
            logger.warning(f"⚠️  IA não retornou resposta para {number}")
            continue

        logger.info(f"💬 Resposta IA → {number}: {reply[:100]}")
        asyncio.create_task(asyncio.to_thread(_save_message, "out", jid, push_name, reply, agent["type"]))

        # Envia via Evolution API
        sent = await _send_whatsapp_text(instance_name, number, reply)
        if not sent:
            logger.error(f"❌ Falha ao enviar resposta para {number}")

    return {"status": "ok"}


# ─── Telegram Webhook ──────────────────────────────────────────────────────────

@router.post("/webhooks/telegram/{chat_id}")
async def webhook_telegram(chat_id: str, request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    if "message" in payload:
        msg = payload["message"]
        if not msg.get("text", "").startswith("/"):
            logger.info(f"🤖 Telegram [{chat_id}] de {msg.get('chat',{}).get('first_name','?')}: {msg.get('text','')[:80]}")
    return {"status": "ok"}


# ─── Instagram Webhook ─────────────────────────────────────────────────────────

@router.get("/webhooks/instagram")
async def verify_instagram(request: Request):
    """Verificação do webhook pela Meta."""
    mode      = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token     = request.query_params.get("hub.verify_token")
    verify    = os.getenv("INSTAGRAM_VERIFY_TOKEN", "nexus_verify_token")
    if mode == "subscribe" and token == verify:
        logger.info("✅ Webhook Instagram verificado")
        return int(challenge)
    raise HTTPException(status_code=403, detail="Token inválido")


@router.post("/webhooks/instagram")
async def webhook_instagram(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                logger.info(f"📸 Instagram de {msg.get('from','?')}: {msg.get('text','')[:80]}")
    return {"status": "ok"}


# ─── Email Webhook ─────────────────────────────────────────────────────────────

@router.post("/webhooks/email")
async def webhook_email(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = dict(await request.form())
    logger.info(f"📧 Email de {payload.get('email','?')}: {payload.get('subject','')[:80]}")
    return {"status": "ok"}


# ─── Monitor (últimas mensagens recebidas) ────────────────────────────────────

_recent_events: list = []

@router.get("/api/webhooks/recent")
async def get_recent_webhooks(limit: int = 20):
    return {"total": len(_recent_events), "recent": _recent_events[-limit:]}


def create_webhook_router():
    return router
