import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

/**
 * VEXUS PREMIUM DASHBOARD v2.0
 * 🚀 Totalmente Melhorado com Knowledge Lab, Proposals e IA Features
 * 
 * Features:
 * ✨ Integração completa com Knowledge Lab (RAG)
 * 🎯 Lead Scoring inteligente com visualização
 * 💡 Whisper Mode (sugestões só para você)
 * 📚 Upload e gerenciamento de documentos
 * 📄 Geração de propostas automática
 * 🤖 3 modos de IA (Assistente, Humano, Autônomo)
 * 📊 Análise em tempo real
 */

const VexusDashboard = () => {
  // ==================== KNOWLEDGE LAB STATE ====================
  const [kbDocuments, setKbDocuments] = useState([
    { id: 1, name: 'Catálogo 2026.pdf', chunks: 24, type: 'product_manual', date: '2026-02-08', size: '2.3MB' },
    { id: 2, name: 'Tabela de Preços.pdf', chunks: 5, type: 'pricing', date: '2026-02-07', size: '0.8MB' },
  ]);
  
  const [kbQuery, setKbQuery] = useState('');
  const [kbResults, setKbResults] = useState(null);
  const [showKBPanel, setShowKBPanel] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // ==================== CHAT STATE ====================
  const [chats, setChats] = useState([
    {
      id: 1,
      name: 'João Silva',
      lastMessage: 'Ótimo! Qual é o valor da consultoria?',
      time: '14:32',
      channel: 'whatsapp',
      score: 85,
      aiMode: 'Assistente',
      active: true,
      online: true
    },
    {
      id: 2,
      name: 'Maria Santos',
      lastMessage: 'Preciso fazer uma cotação para 50 unidades',
      time: '11:20',
      channel: 'instagram',
      score: 62,
      aiMode: 'Humano',
      active: false,
      online: false
    }
  ]);

  const [activeChat, setActiveChat] = useState(chats[0]);
  const [messages, setMessages] = useState([
    { type: 'client', text: 'Oi! Gostaria de saber mais sobre a consultoria de 3 meses', time: '14:28' },
    { type: 'ai', text: 'Perfeito! 🎯 Nossa consultoria de 3 meses é ideal para empresas que querem escalar.\n\nInclui:\n• Diagnóstico completo\n• Implementação de processos\n• Treinamento da equipe\n\nInvestimento: R$ 15.000 | Parcelado: 3x R$ 5.000', time: '14:30' },
    { type: 'human', text: 'Vou gerar uma proposta com todos os detalhes!', time: '14:31' },
    { type: 'client', text: 'Ótimo! Qual é o valor da consultoria?', time: '14:32' }
  ]);

  const [messageInput, setMessageInput] = useState('');
  const [filter, setFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('chat'); // chat, kb, proposals
  const [showWhisperMode, setShowWhisperMode] = useState(false);
  const [selectedTab, setSelectedTab] = useState('chat');
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (!messageInput.trim()) return;

    setMessages([...messages, { 
      type: 'human', 
      text: messageInput, 
      time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) 
    }]);
    setMessageInput('');

    // Simular resposta da IA após 800ms
    setTimeout(() => {
      setMessages(prev => [...prev, {
        type: 'ai',
        text: '🧠 Processando com Knowledge Lab...\n\n📚 Encontrado em: Catálogo 2026.pdf\n\nA informação que você procura está documentada. Deixe-me preparar uma resposta completa!',
        time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
        source: 'Knowledge Lab',
        confidence: 0.92
      }]);
    }, 800);
  };

  // ==================== KNOWLEDGE LAB FUNCTIONS ====================
  const handleKBQuery = async () => {
    if (!kbQuery.trim()) return;

    try {
      // Simular query ao Knowledge Lab
      const response = {
        response: `📚 Encontrado em "Catálogo 2026.pdf"\n\nSua pergunta: "${kbQuery}"\n\n✅ Resposta: A informação está disponível em nossa documentação. Confira os detalhes no documento e aproveite a oferta especial!`,
        confidence: 0.92,
        source_document: 'Catálogo 2026.pdf',
        use_knowledge_base: true,
        chunks_used: 3
      };

      setKbResults(response);

      // Adicionar como mensagem no chat
      setMessages(prev => [...prev, {
        type: 'ai',
        text: response.response,
        time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
        source: 'Knowledge Lab',
        confidence: response.confidence
      }]);

      setKbQuery('');
    } catch (error) {
      console.error('Erro na query:', error);
      alert('❌ Erro ao consultar Knowledge Lab');
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      // Simular upload
      setTimeout(() => {
        const newDoc = {
          id: kbDocuments.length + 1,
          name: file.name,
          chunks: Math.floor(Math.random() * 30) + 5,
          type: 'custom',
          date: new Date().toISOString().split('T')[0],
          size: (file.size / 1024 / 1024).toFixed(2) + 'MB'
        };
        
        setKbDocuments([...kbDocuments, newDoc]);
        setUploadFile(null);
        setIsUploading(false);
        
        // Mensagem de sucesso
        setMessages(prev => [...prev, {
          type: 'ai',
          text: `✅ Documento "${file.name}" indexado com sucesso!\n\nAgora você pode fazer perguntas sobre este documento.`,
          time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
          source: 'Sistema'
        }]);
      }, 1500);
    } catch (error) {
      console.error('Erro no upload:', error);
      setIsUploading(false);
      alert('❌ Erro ao fazer upload');
    }
  };

  // ==================== UTILITY FUNCTIONS ====================
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 50) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getChannelIcon = (channel) => {
    const icons = { whatsapp: '💬', instagram: '📷', email: '📧', facebook: '👍' };
    return icons[channel] || '💬';
  };

  const filteredChats = chats.filter(chat => {
    if (filter === 'hot') return chat.score > 75;
    if (filter === 'waiting') return chat.aiMode === 'Assistente';
    return true;
  });

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 to-slate-950 text-gray-100 font-sans overflow-hidden">

      {/* ===== COLUNA 1: MINI-SIDEBAR ===== */}
      <nav className="w-16 bg-slate-950 border-r border-slate-700 flex flex-col items-center py-4 space-y-6 shadow-2xl">
        {/* Logo */}
        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center font-bold text-white text-lg shadow-lg hover:shadow-purple-500/50 transition-all cursor-pointer">
          V
        </div>

        {/* Navigation */}
        <NavIcon icon="💬" title="Inbox" active={true} />
        <NavIcon icon="📊" title="Pipeline" />
        <NavIcon icon="🤖" title="Agentes" />
        <NavIcon icon="👥" title="Contatos" />
        <NavIcon icon="📈" title="Analytics" />
        <NavIcon icon="📚" title="Knowledge Lab" onClick={() => setShowKBPanel(!showKBPanel)} />

        <div className="flex-1"></div>
        <NavIcon icon="⚙️" title="Config" />
      </nav>

      {/* ===== COLUNA 2: LISTA DE CONVERSAS ===== */}
      <aside className="w-80 bg-slate-800 border-r border-slate-700 flex flex-col shadow-lg">
        {/* Header */}
        <div className="p-4 border-b border-slate-700 bg-gradient-to-r from-slate-800 to-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">Conversas Ativas</h2>
            <div className="flex gap-2">
              <button className="p-2 hover:bg-slate-600 rounded-lg text-gray-400 hover:text-gray-200 transition">
                <span>➕</span>
              </button>
            </div>
          </div>

          {/* Search */}
          <input
            type="text"
            placeholder="🔍 Buscar..."
            className="w-full bg-slate-700 text-white placeholder-gray-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Filters */}
        <div className="px-4 py-3 border-b border-slate-700 flex gap-2 bg-slate-750">
          {['all', 'waiting', 'hot'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded-full font-semibold transition ${
                filter === f 
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/50' 
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              {f === 'all' ? 'Todos' : f === 'waiting' ? '⏳ Aguard.' : '🔥 Quentes'}
            </button>
          ))}
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto">
          {filteredChats.map(chat => (
            <ChatListItem
              key={chat.id}
              chat={chat}
              active={activeChat.id === chat.id}
              onClick={() => setActiveChat(chat)}
            />
          ))}
        </div>
      </aside>

      {/* ===== COLUNA 3: ÁREA PRINCIPAL (CHAT + TABS) ===== */}
      <main className="flex-1 flex flex-col bg-slate-900">
        {/* Header com Info do Chat */}
        <header className="bg-gradient-to-r from-slate-800 to-slate-750 border-b border-slate-700 px-6 py-4 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg ${ activeChat.score >= 80 ? 'bg-gradient-to-br from-green-500 to-emerald-600' : activeChat.score >= 50 ? 'bg-gradient-to-br from-yellow-500 to-orange-600' : 'bg-gradient-to-br from-blue-500 to-blue-600'}`}>
              {activeChat.name.split(' ').map(n => n[0]).join('')}
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">{activeChat.name}</h1>
              <p className="text-sm text-gray-400">
                {getChannelIcon(activeChat.channel)} {activeChat.channel} • {activeChat.online ? '🟢 Online' : '🔴 Offline'}
              </p>
            </div>
          </div>

          {/* Actions Header */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowWhisperMode(!showWhisperMode)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition ${
                showWhisperMode
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              🎙️ Whisper Mode {showWhisperMode ? 'ON' : 'OFF'}
            </button>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-700 bg-slate-800 px-6">
          {['chat', 'kb', 'proposals'].map((tab) => (
            <button
              key={tab}
              onClick={() => setSelectedTab(tab)}
              className={`px-4 py-3 font-semibold transition ${
                selectedTab === tab
                  ? 'border-b-2 border-purple-500 text-purple-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab === 'chat' ? '💬 Chat' : tab === 'kb' ? '📚 Knowledge Lab' : '📄 Propostas'}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {selectedTab === 'chat' && renderChatTab()}
          {selectedTab === 'kb' && renderKBTab()}
          {selectedTab === 'proposals' && renderProposalsTab()}
        </div>
      </main>

      {/* ===== COLUNA 4: PAINEL DE INTELIGÊNCIA ===== */}
      <aside className="w-96 bg-gradient-to-b from-slate-800 to-slate-850 border-l border-slate-700 flex flex-col shadow-2xl overflow-y-auto">
        {/* Lead Score */}
        <div className="p-4 border-b border-slate-700">
          <h3 className="text-sm font-bold text-white mb-4">🎯 Lead Score Inteligente</h3>
          <LeadScoreVisualization score={activeChat.score} />
          
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Interesse</span>
              <div className="flex gap-1">
                {'★★★★★'.split('').map((_, i) => (
                  <span key={i} className={i < Math.round(activeChat.score / 20) ? 'text-yellow-400' : 'text-gray-600'}>★</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* IA Summary */}
        <div className="p-4 border-b border-slate-700">
          <h3 className="text-sm font-bold text-white mb-3">🧠 Resumo IA (Últimos 10 min)</h3>
          <div className="bg-slate-700 rounded-lg p-3 text-sm text-gray-300 leading-relaxed">
            <p>💡 <strong>{activeChat.name}</strong> demonstrou <span className="text-emerald-400">alto interesse</span> em consultoria.</p>
            <p className="mt-2">📌 Perguntou sobre: preço, timeline e detalhes.</p>
            <p className="mt-2 text-emerald-400 font-semibold">✅ Recomendação: Enviar proposta com desconto!</p>
          </div>
        </div>

        {/* Ações Rápidas */}
        <div className="p-4 border-b border-slate-700">
          <h3 className="text-sm font-bold text-white mb-3">⚡ Ações Rápidas</h3>
          <div className="space-y-2">
            <QuickActionButton icon="📄" text="Gerar Proposta" bg="bg-purple-600 hover:bg-purple-700" />
            <QuickActionButton icon="📅" text="Agendar Reunião" bg="bg-blue-600 hover:bg-blue-700" />
            <QuickActionButton icon="✅" text="Próxima Etapa" bg="bg-green-600 hover:bg-green-700" />
          </div>
        </div>

        {/* Dados do Contato */}
        <div className="p-4 border-b border-slate-700">
          <h3 className="text-sm font-bold text-white mb-3">📋 Dados do Contato</h3>
          <div className="space-y-3 text-sm">
            <div>
              <label className="text-xs text-gray-400">Email</label>
              <p className="text-gray-200 truncate">joao.silva@empresa.com</p>
            </div>
            <div>
              <label className="text-xs text-gray-400">Telefone</label>
              <p className="text-gray-200">(11) 99999-9999</p>
            </div>
            <div>
              <label className="text-xs text-gray-400">Empresa</label>
              <p className="text-gray-200">TechFlow Solutions</p>
            </div>
            <div>
              <label className="text-xs text-gray-400">Origem</label>
              <p className="text-gray-200">LinkedIn | Inbound</p>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="p-4">
          <h3 className="text-sm font-bold text-white mb-3">📜 Timeline</h3>
          <div className="space-y-2 text-xs">
            <TimelineItem icon="✓" text="Proposta enviada" time="14:31" color="emerald" />
            <TimelineItem icon="→" text="Conversa iniciada" time="14:25" color="blue" />
            <TimelineItem icon="○" text="Lead criado" time="13 fev 10:15" color="gray" />
          </div>
        </div>
      </aside>

    </div>
  );

  // ==================== RENDER FUNCTIONS ====================
  function renderChatTab() {
    return (
      <div className="flex flex-col h-full gap-4 p-6">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 bg-slate-800 rounded-lg p-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p>Nenhuma mensagem ainda. Comece a conversa!</p>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Whisper Mode */}
        {showWhisperMode && (
          <div className="bg-blue-900 border-l-4 border-blue-500 p-4 rounded-lg">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold text-blue-300 mb-2">💡 Modo Whisper Ativado</p>
                <p className="text-sm text-blue-200">
                  "Lead com score 85. Cliente urgente! Ofereça 15% de desconto se fechar hoje."
                </p>
              </div>
              <button
                onClick={() => setShowWhisperMode(false)}
                className="text-blue-400 hover:text-blue-300 ml-2"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="flex gap-2">
          <input
            type="text"
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Digite sua mensagem ou pergunta..."
            className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 text-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={handleSendMessage}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-semibold transition shadow-lg hover:shadow-purple-500/50"
          >
            Enviar
          </button>
        </div>
      </div>
    );
  }

  function renderKBTab() {
    return (
      <div className="flex flex-col h-full gap-4 p-6">
        {/* Upload Section */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-lg">📚 Knowledge Lab Management</h3>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="bg-white text-purple-600 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-gray-100 disabled:opacity-50 transition"
            >
              {isUploading ? '⏳ Indexando...' : '📄 + Upload PDF'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
          <p className="text-sm opacity-90">Faça upload de seus documentos para que a IA responda perguntas baseada neles.</p>
        </div>

        {/* Documents */}
        <div className="flex-1 overflow-y-auto space-y-2">
          <h4 className="font-semibold text-gray-300 mb-3">Documentos Indexados ({kbDocuments.length})</h4>
          {kbDocuments.map((doc) => (
            <div key={doc.id} className="bg-slate-800 p-4 rounded-lg border border-slate-700 hover:border-purple-500 hover:shadow-lg hover:shadow-purple-500/20 transition-all">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold text-white flex items-center gap-2">
                    📄 {doc.name}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {doc.chunks} chunks • {doc.size} • {doc.date}
                  </p>
                </div>
                <span className="text-xs px-3 py-1 bg-blue-900 text-blue-300 rounded-full font-semibold">
                  {doc.type.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Query Section */}
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <label className="text-sm font-semibold text-white block mb-2">🔍 Faça uma pergunta:</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={kbQuery}
              onChange={(e) => setKbQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleKBQuery()}
              placeholder="Ex: Qual é o preço do plano premium?"
              className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 text-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              onClick={handleKBQuery}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold transition"
            >
              Buscar
            </button>
          </div>

          {kbResults && (
            <div className="mt-3 bg-slate-700 p-3 rounded-lg border-l-4 border-green-500">
              <p className="text-sm text-gray-200">{kbResults.response}</p>
              <div className="flex gap-2 mt-2 text-xs text-gray-500">
                <span>✓ Confiança: {Math.round(kbResults.confidence * 100)}%</span>
                <span>📚 {kbResults.source_document}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  function renderProposalsTab() {
    return (
      <div className="flex items-center justify-center h-full flex-col gap-4">
        <div className="text-6xl">📋</div>
        <h3 className="font-bold text-2xl text-white">Gerador de Propostas</h3>
        <p className="text-gray-400 text-center max-w-md">
          Gere propostas inteligentes baseadas em Knowledge Lab e histórico do cliente
        </p>
        <button className="mt-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-semibold transition shadow-lg">
          ✨ Gerar Proposta Agora
        </button>
      </div>
    );
  }

};

// Componentes auxiliares
const NavIcon = ({ icon, title, active = false }) => (
  <button
    title={title}
    className={`p-3 rounded-lg transition ${
      active
        ? 'bg-purple-600 text-white'
        : 'text-gray-400 hover:bg-slate-700 hover:text-gray-300'
    }`}
  >
    <span className="text-xl">{icon}</span>
  </button>
);

const ChatListItem = ({ chat, active, onClick }) => (
  <div
    onClick={onClick}
    className={`mx-2 mt-2 p-3 rounded-lg cursor-pointer transition ${
      active
        ? 'bg-slate-700 border-l-4 border-purple-500'
        : 'bg-slate-700 hover:bg-slate-600'
    }`}
  >
    <div className="flex items-start justify-between mb-2">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${chat.online ? 'bg-green-500' : 'bg-gray-500'}`}></div>
        <span className="text-sm font-semibold text-white">{chat.name}</span>
        <span className="text-xs bg-purple-600 px-2 py-0.5 rounded text-white">
          {chat.aiMode === 'Assistente' ? '🤖' : '👤'} {chat.aiMode}
        </span>
      </div>
      <span className="text-xs text-gray-400">{chat.time}</span>
    </div>
    <p className="text-xs text-gray-300 line-clamp-2">{chat.lastMessage}</p>
    <div className="mt-2 flex items-center justify-between">
      <span className="text-xs text-gray-400 capitalize">{chat.channel}</span>
      <div className="flex items-center gap-1">
        <span className="text-lg">🔥</span>
        <span className={`text-xs font-semibold ${
          chat.score > 75 ? 'text-emerald-400' : chat.score > 50 ? 'text-yellow-400' : 'text-gray-400'
        }`}>
          {chat.score}
        </span>
      </div>
    </div>
  </div>
);

const MessageBubble = ({ message }) => {
  const isClient = message.type === 'client';
  const isAI = message.type === 'ai';

  return (
    <div className={`flex ${isClient ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-md rounded-lg px-4 py-2 ${
          isClient
            ? 'bg-slate-700 rounded-tl-none'
            : isAI
            ? 'bg-purple-600 rounded-tr-none'
            : 'bg-emerald-600 rounded-tr-none'
        }`}
      >
        <p className="text-sm text-white whitespace-pre-wrap">{message.text}</p>
        <p className={`text-xs mt-1 ${isAI ? 'text-purple-200' : isClient ? 'text-gray-400' : 'text-gray-300'}`}>
          {message.time}
        </p>
      </div>
    </div>
  );
};

const QuickActionButton = ({ icon, text }) => (
  <button className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg font-medium transition flex items-center justify-center gap-2">
    <span>{icon}</span>
    {text}
  </button>
);

const ContactField = ({ label, value }) => (
  <div>
    <label className="text-xs text-gray-400">{label}</label>
    <p className="text-sm text-gray-200">{value}</p>
  </div>
);

// ==================== HELPER COMPONENTS ====================

/**
 * ChatListItem - Exibe cada conversa na lista lateral
 */
function ChatListItem({ chat, active, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`p-3 cursor-pointer border-l-4 transition-all ${
        active
          ? 'bg-slate-700 border-l-purple-500 shadow-lg shadow-purple-600/20'
          : 'border-l-transparent hover:bg-slate-750'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <p className="font-semibold text-white text-sm">{chat.name}</p>
          <p className="text-xs text-gray-400 line-clamp-1">{chat.lastMessage}</p>
        </div>
        <div className="flex items-center gap-1">
          {chat.score > 75 && <span className="text-sm">🔥</span>}
          <span className="text-xs text-gray-500">{chat.time}</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <span className="text-xs px-2 py-1 rounded-full bg-slate-600 text-gray-300 font-semibold">
          {getChannelIcon(chat.channel)} {chat.channel}
        </span>
        <div className="flex items-center gap-1">
          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${getScoreBg(chat.score)} text-white`}>
            {chat.score}
          </span>
          {chat.aiMode === 'Autônoma' && <span className="text-xs" title="IA Autônoma Ativa">🤖</span>}
        </div>
      </div>
    </div>
  );
}

/**
 * MessageBubble - Exibe cada mensagem com styling apropriado
 */
function MessageBubble({ message }) {
  const isClientMessage = message.type === 'client';
  const isAIMessage = message.type === 'ai';

  return (
    <div className={`flex ${isClientMessage ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs p-3 rounded-lg ${
          isClientMessage
            ? 'bg-purple-600 text-white rounded-br-none'
            : isAIMessage
              ? 'bg-slate-700 text-gray-100 rounded-bl-none border border-slate-600'
              : 'bg-blue-900 text-blue-100 rounded-bl-none border border-blue-700'
        }`}
      >
        <p className="text-sm">{message.text}</p>

        {/* Source Attribution (KB) */}
        {message.source && (
          <div className="mt-2 pt-2 border-t border-opacity-30 border-current">
            <p className="text-xs opacity-80">
              📚 Fonte: <strong>{message.source}</strong>
            </p>
            {message.confidence && (
              <p className="text-xs opacity-70">
                ✓ Confiança: {Math.round(message.confidence * 100)}%
              </p>
            )}
          </div>
        )}

        <p className="text-xs opacity-70 mt-1">{message.time}</p>
      </div>
    </div>
  );
}

/**
 * LeadScoreVisualization - Circular SVG indicator
 */
function LeadScoreVisualization({ score }) {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;
  const scoreColor = score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#3b82f6';

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-32 h-32">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle cx="50" cy="50" r="45" fill="none" stroke="#475569" strokeWidth="8" opacity="0.3" />

          {/* Progress circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={scoreColor}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color: scoreColor }}>
            {score}
          </span>
          <span className="text-xs text-gray-400">Score</span>
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
          <span className="text-gray-300">Pronto para fechar</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <span className="text-gray-300">Em progresso</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span className="text-gray-300">Iniciante</span>
        </div>
      </div>
    </div>
  );
}

/**
 * QuickActionButton - Botão de ação rápida
 */
function QuickActionButton({ icon, text, bg = 'bg-purple-600 hover:bg-purple-700' }) {
  return (
    <button
      className={`w-full flex items-center justify-center gap-2 py-3 ${bg} text-white rounded-lg font-semibold transition shadow-lg hover:shadow-lg`}
    >
      <span className="text-lg">{icon}</span>
      {text}
    </button>
  );
}

/**
 * TimelineItem - Item do timeline
 */
function TimelineItem({ icon, text, time, color }) {
  const colorClass = {
    emerald: 'text-emerald-400',
    blue: 'text-blue-400',
    gray: 'text-gray-500'
  }[color] || 'text-gray-500';

  return (
    <div className="flex gap-2 items-start">
      <span className={`${colorClass} font-bold text-lg mt-0.5`}>{icon}</span>
      <div className="flex-1">
        <p className="text-gray-300 text-sm">{text}</p>
        <p className="text-gray-500 text-xs">{time}</p>
      </div>
    </div>
  );
}

/**
 * NavIcon - Ícone de navegação lateral
 */
function NavIcon({ icon, title, active = false, onClick }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`w-12 h-12 flex items-center justify-center rounded-lg transition-all ${
        active
          ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/50 scale-110'
          : 'text-gray-400 hover:bg-slate-700 hover:text-gray-200'
      }`}
    >
      <span className="text-2xl">{icon}</span>
    </button>
  );
}

export default VexusDashboard;
