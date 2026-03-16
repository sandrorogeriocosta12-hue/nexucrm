# 📱 WhatsApp Business API - Guia de Configuração

## 🚀 Configuração Rápida

### 1. Criar Aplicativo no Facebook Developers
1. Acesse [Facebook Developers](https://developers.facebook.com/)
2. Crie um novo aplicativo
3. Selecione "Business" como tipo
4. Adicione o produto "WhatsApp"

### 2. Configurar WhatsApp Business API
1. No painel do aplicativo, vá para "WhatsApp"
2. Adicione um número de telefone de teste
3. Copie o `Access Token` temporário
4. Anote o `Phone Number ID`

### 3. Configurar Webhook
1. No painel WhatsApp, configure o webhook URL:
   ```
   https://web-production-c726e.up.railway.app/api/whatsapp/webhook
   ```
2. Defina um `Verify Token` (ex: "vexus_crm_webhook_2024")
3. Selecione os eventos: `messages`

### 4. Configurar no Vexus CRM
```bash
# Definir variáveis de ambiente no Railway
railway variables set WHATSAPP_ACCESS_TOKEN="seu_access_token_aqui"
railway variables set WHATSAPP_PHONE_NUMBER_ID="seu_phone_number_id_aqui"
railway variables set WHATSAPP_VERIFY_TOKEN="seu_verify_token_aqui"
```

### 5. Testar Configuração
```bash
# Verificar status da configuração
curl -X GET "https://web-production-c726e.up.railway.app/api/whatsapp/config" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Testar envio de mensagem
curl -X POST "https://web-production-c726e.up.railway.app/api/whatsapp/send-message" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "to": "5511999999999",
    "message": "Olá! Teste do Vexus CRM WhatsApp API"
  }'
```

## 📋 APIs Disponíveis

### Envio de Mensagens
```http
POST /api/whatsapp/send-message
Content-Type: application/json
Authorization: Bearer <token>

{
  "to": "5511999999999",
  "message": "Sua mensagem aqui",
  "lead_id": "optional_lead_id"
}
```

### Templates Automáticos
```http
POST /api/whatsapp/send-template
Content-Type: application/json
Authorization: Bearer <token>

{
  "to": "5511999999999",
  "template_name": "welcome_message",
  "language_code": "pt_BR",
  "components": [...],
  "lead_id": "optional_lead_id"
}
```

### Mensagens Automatizadas
```http
POST /api/whatsapp/automated/welcome/{lead_id}
POST /api/whatsapp/automated/followup/{lead_id}
```

### Configuração
```http
GET /api/whatsapp/config
POST /api/whatsapp/config
```

## 🔧 Configuração de Produção

### 1. Número de Produção
1. No painel WhatsApp, solicite um número de produção
2. Aguarde aprovação do Facebook (pode levar dias)
3. Configure o número aprovado

### 2. Templates Aprovados
1. Crie templates de mensagem no painel WhatsApp
2. Aguarde aprovação (24-48 horas)
3. Use os templates aprovados nas automações

### 3. Limites e Custos
- **Mensagens de Conversação**: Gratuitas por 24h após resposta do usuário
- **Mensagens de Template**: Cobradas por envio
- **Limite**: 250 mensagens/dia para teste, ilimitado para produção

## 🐛 Troubleshooting

### Erro: "Access Token inválido"
- Verifique se o token não expirou
- Gere um novo token no painel do Facebook

### Erro: "Número não encontrado"
- Verifique o formato: deve incluir código do país (55 para Brasil)
- Exemplo: 5511999999999

### Webhook não recebe mensagens
- Verifique se o URL do webhook está correto
- Confirme se o Verify Token está configurado
- Teste o webhook com o botão "Test" no painel

### Mensagens não são entregues
- Verifique se o número do destinatário tem WhatsApp
- Confirme se não há bloqueios ou restrições

## 📚 Referências

- [Documentação Oficial WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/)
- [Guia de Configuração Meta](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Referência da API](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)

---

*Configuração WhatsApp Business API - Vexus CRM* 📱