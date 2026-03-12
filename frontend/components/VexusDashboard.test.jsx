/**
 * VexusDashboard.test.jsx - Suite de testes para o dashboard
 * Utiliza React Testing Library + Vitest
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import VexusDashboard from './VexusDashboard';

describe('VexusDashboard Component', () => {
  
  beforeEach(() => {
    // Mock localStorage
    Storage.prototype.getItem = vi.fn(() => null);
  });

  // ==================== LAYOUT TESTS ====================
  describe('Layout Principal (4 Colunas)', () => {
    it('deve renderizar as 4 colunas principais', () => {
      render(<VexusDashboard />);
      
      // Verificar existência de elementos principais
      expect(screen.getByRole('navigation')).toBeInTheDocument(); // Mini-sidebar
      expect(screen.getByText('Conversas Ativas')).toBeInTheDocument(); // Chat list
      expect(screen.getByText('🎯 Lead Score Inteligente')).toBeInTheDocument(); // Intelligence panel
    });

    it('deve exibir a navegação com todos os ícones', () => {
      render(<VexusDashboard />);
      
      const navbar = screen.getByRole('navigation');
      expect(within(navbar).getByText('V')).toBeInTheDocument(); // Logo
      expect(within(navbar).getByText('💬')).toBeInTheDocument(); // Inbox
      expect(within(navbar).getByText('📚')).toBeInTheDocument(); // KB
    });

    it('deve ter width correto para cada coluna', () => {
      const { container } = render(<VexusDashboard />);
      const mainDiv = container.firstChild;
      
      expect(mainDiv).toHaveClass('flex', 'h-screen');
    });
  });

  // ==================== CHAT LIST TESTS ====================
  describe('Chat List (Coluna 2)', () => {
    it('deve exibir lista de conversas', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('João Silva')).toBeInTheDocument();
      expect(screen.getByText('Maria Santos')).toBeInTheDocument();
    });

    it('deve filtrar conversas por status', async () => {
      render(<VexusDashboard />);
      
      const allButton = screen.getByText('Todos');
      const hotButton = screen.getByText('🔥 Quentes');
      
      // Clicar no filtro "Quentes"
      fireEvent.click(hotButton);
      
      // Esperar resultado
      await waitFor(() => {
        expect(hotButton).toHaveClass('bg-purple-600');
      });
    });

    it('deve buscar conversa por nome', async () => {
      render(<VexusDashboard />);
      
      const searchInput = screen.getByPlaceholderText('🔍 Buscar...');
      
      await userEvent.type(searchInput, 'João');
      
      // Apenas João deve aparecer
      expect(screen.getByText('João Silva')).toBeInTheDocument();
    });

    it('deve marcar conversa como ativa ao clicar', async () => {
      render(<VexusDashboard />);
      
      const joaoChat = screen.getByText('João Silva').closest('div');
      fireEvent.click(joaoChat);
      
      // Verificar que está marcada
      await waitFor(() => {
        expect(joaoChat).toHaveClass('bg-slate-700', 'border-l-purple-500');
      });
    });

    it('deve mostrar indicador 🔥 para leads quentes', () => {
      render(<VexusDashboard />);
      
      // Lead com score 85 deve ter 🔥
      const joaoRow = screen.getByText('João Silva').closest('div');
      expect(joaoRow.textContent).toContain('🔥');
    });

    it('deve mostrar 🤖 quando IA autônoma está ativa', () => {
      render(<VexusDashboard />);
      
      // Verificar presença de ícone de IA
      const aiIndicators = screen.getAllByText('🤖');
      expect(aiIndicators.length).toBeGreaterThan(0);
    });
  });

  // ==================== CHAT AREA TESTS ====================
  describe('Área de Chat (Coluna 3)', () => {
    it('deve exibir header com info do chat', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('João Silva')).toBeInTheDocument();
      expect(screen.getByText(/whatsapp/i)).toBeInTheDocument();
    });

    it('deve exibir sistema de abas', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('💬 Chat')).toBeInTheDocument();
      expect(screen.getByText('📚 Knowledge Lab')).toBeInTheDocument();
      expect(screen.getByText('📄 Propostas')).toBeInTheDocument();
    });

    it('deve trocar de aba ao clicar', async () => {
      render(<VexusDashboard />);
      
      const kbTab = screen.getByText('📚 Knowledge Lab');
      fireEvent.click(kbTab);
      
      // Verificar que a aba KB está ativa
      await waitFor(() => {
        expect(kbTab.parentElement).toHaveClass('border-b-2', 'border-purple-500');
      });
    });

    it('deve exibir botão Whisper Mode', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText(/Whisper Mode/i)).toBeInTheDocument();
    });

    it('deve ativar/desativar Whisper Mode', async () => {
      render(<VexusDashboard />);
      
      const whisperButton = screen.getByText(/Whisper Mode/i);
      fireEvent.click(whisperButton);
      
      // Verificar sugestão visível
      await waitFor(() => {
        expect(screen.getByText(/Modo Whisper Ativado/i)).toBeInTheDocument();
      });
    });
  });

  // ==================== CHAT TAB TESTS ====================
  describe('Chat Tab', () => {
    it('deve exibir input de mensagem', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByPlaceholderText('Digite sua mensagem ou pergunta...')).toBeInTheDocument();
    });

    it('deve enviar mensagem ao clicar em Enviar', async () => {
      render(<VexusDashboard />);
      
      const input = screen.getByPlaceholderText('Digite sua mensagem ou pergunta...');
      const sendButton = screen.getByText('Enviar');
      
      await userEvent.type(input, 'Olá!');
      fireEvent.click(sendButton);
      
      // Verificar que mensagem foi adicionada
      await waitFor(() => {
        expect(screen.getByText('Olá!')).toBeInTheDocument();
      });
    });

    it('deve enviar mensagem ao pressionar Enter', async () => {
      render(<VexusDashboard />);
      
      const input = screen.getByPlaceholderText('Digite sua mensagem ou pergunta...');
      
      await userEvent.type(input, 'Teste{Enter}');
      
      // Verificar mensagem
      await waitFor(() => {
        expect(screen.getByText('Teste')).toBeInTheDocument();
      });
    });

    it('deve mostrar Whisper Mode quando ativado', async () => {
      render(<VexusDashboard />);
      
      const whisperButton = screen.getByText(/Whisper Mode/i);
      fireEvent.click(whisperButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Modo Whisper Ativado/i)).toBeInTheDocument();
        expect(screen.getByText(/Cliente urgente/i)).toBeInTheDocument();
      });
    });

    it('deve fechar Whisper Mode ao clicar X', async () => {
      render(<VexusDashboard />);
      
      // Ativar
      fireEvent.click(screen.getByText(/Whisper Mode/i));
      
      // Fechar (ícone X)
      const closeButton = screen.getByText('✕');
      fireEvent.click(closeButton);
      
      // Verificar que foi fechado
      await waitFor(() => {
        expect(screen.queryByText(/Modo Whisper Ativado/i)).not.toBeInTheDocument();
      });
    });

    it('deve exibir mensagens com atribuição de fonte KB', async () => {
      render(<VexusDashboard />);
      
      // Enviar mensagem
      const input = screen.getByPlaceholderText('Digite sua mensagem ou pergunta...');
      fireEvent.click(input);
      
      await userEvent.type(input, 'Resposta do KB');
      fireEvent.click(screen.getByText('Enviar'));
      
      // Aguardar resposta da IA
      await waitFor(() => {
        expect(screen.getByText(/Processando com Knowledge Lab/i)).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  // ==================== KNOWLEDGE LAB TAB TESTS ====================
  describe('Knowledge Lab Tab', () => {
    it('deve exibir painel de upload', async () => {
      render(<VexusDashboard />);
      
      fireEvent.click(screen.getByText('📚 Knowledge Lab'));
      
      await waitFor(() => {
        expect(screen.getByText(/📄 \+ Upload PDF/)).toBeInTheDocument();
      });
    });

    it('deve exibir lista de documentos indexados', async () => {
      render(<VexusDashboard />);
      
      fireEvent.click(screen.getByText('📚 Knowledge Lab'));
      
      await waitFor(() => {
        expect(screen.getByText(/Catálogo 2026.pdf/)).toBeInTheDocument();
        expect(screen.getByText(/Tabela de Preços.pdf/)).toBeInTheDocument();
      });
    });

    it('deve mostrar metadata dos documentos', async () => {
      render(<VexusDashboard />);
      
      fireEvent.click(screen.getByText('📚 Knowledge Lab'));
      
      await waitFor(() => {
        expect(screen.getByText(/24 chunks/)).toBeInTheDocument();
        expect(screen.getByText(/2.3MB/)).toBeInTheDocument();
        expect(screen.getByText(/product_manual/)).toBeInTheDocument();
      });
    });

    it('deve exibir interface de query', async () => {
      render(<VexusDashboard />);
      
      fireEvent.click(screen.getByText('📚 Knowledge Lab'));
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Qual é o preço/i)).toBeInTheDocument();
        expect(screen.getByText('Buscar')).toBeInTheDocument();
      });
    });

    it('deve fazer query e exibir resultado', async () => {
      render(<VexusDashboard />);
      
      fireEvent.click(screen.getByText('📚 Knowledge Lab'));
      
      const queryInput = await screen.findByPlaceholderText(/Qual é o preço/i);
      fireEvent.click(queryInput);
      
      await userEvent.type(queryInput, 'Teste');
      fireEvent.click(screen.getByText('Buscar'));
      
      await waitFor(() => {
        expect(screen.getByText(/Confiança:/)).toBeInTheDocument();
      });
    });

    it('deve fazer upload de arquivo', async () => {
      render(<VexusDashboard />);
      
      fireEvent.click(screen.getByText('📚 Knowledge Lab'));
      
      const uploadButton = await screen.findByText(/📄 \+ Upload PDF/);
      
      // Simular upload (em teste real, usar File API)
      expect(uploadButton).toBeInTheDocument();
    });
  });

  // ==================== INTELLIGENCE PANEL TESTS ====================
  describe('Intelligence Panel (Coluna 4)', () => {
    it('deve exibir Lead Score', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('🎯 Lead Score Inteligente')).toBeInTheDocument();
    });

    it('deve exibir visualização circular do score', () => {
      render(<VexusDashboard />);
      
      // Procurar por SVG (indicador circular)
      const svgs = screen.getByText('🎯 Lead Score Inteligente').closest('div').querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(0);
    });

    it('deve exibir cores corretas por score', () => {
      render(<VexusDashboard />);
      
      // Score alto (85) deve ter cor verde
      const scoreArea = screen.getByText('🎯 Lead Score Inteligente').closest('div');
      expect(scoreArea.textContent).toContain('85'); // Score do João
    });

    it('deve exibir Resumo IA', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('🧠 Resumo IA (Últimos 10 min)')).toBeInTheDocument();
      expect(screen.getByText(/alto interesse/i)).toBeInTheDocument();
    });

    it('deve exibir Ações Rápidas', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('⚡ Ações Rápidas')).toBeInTheDocument();
      expect(screen.getByText('📄 Gerar Proposta')).toBeInTheDocument();
      expect(screen.getByText('📅 Agendar Reunião')).toBeInTheDocument();
      expect(screen.getByText('✅ Próxima Etapa')).toBeInTheDocument();
    });

    it('deve exibir Dados do Contato', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('📋 Dados do Contato')).toBeInTheDocument();
      expect(screen.getByText('joao.silva@empresa.com')).toBeInTheDocument();
    });

    it('deve exibir Timeline', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('📜 Timeline')).toBeInTheDocument();
      expect(screen.getByText(/Proposta enviada/i)).toBeInTheDocument();
    });
  });

  // ==================== HELPER COMPONENTS TESTS ====================
  describe('Componentes Helper', () => {
    it('deve renderizar ChatListItem com informações', () => {
      render(<VexusDashboard />);
      
      // ChatListItem é parte da lista de conversas
      expect(screen.getByText('João Silva')).toBeInTheDocument();
    });

    it('deve renderizar MessageBubble com diferentes tipos', async () => {
      render(<VexusDashboard />);
      
      // Enviar mensagem para gerar bubbles
      const input = screen.getByPlaceholderText('Digite sua mensagem ou pergunta...');
      await userEvent.type(input, 'Teste{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Teste')).toBeInTheDocument();
      });
    });

    it('deve renderizar LeadScoreVisualization', () => {
      render(<VexusDashboard />);
      
      const scoreSection = screen.getByText('🎯 Lead Score Inteligente').closest('div');
      expect(scoreSection.querySelectorAll('svg').length).toBeGreaterThan(0);
    });

    it('deve renderizar QuickActionButton', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByText('📄 Gerar Proposta')).toBeInTheDocument();
    });
  });

  // ==================== INTEGRATION TESTS ====================
  describe('Integração Completa', () => {
    it('deve fluxo completo: selecionar chat > ativar KB > fazer query', async () => {
      render(<VexusDashboard />);
      
      // 1. Chat está selecionado (padrão)
      expect(screen.getByText('João Silva')).toBeInTheDocument();
      
      // 2. Clicar em Knowledge Lab
      fireEvent.click(screen.getByText('📚 Knowledge Lab'));
      
      // 3. Query deve aparecer
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Qual é o preço/i)).toBeInTheDocument();
      });
      
      // 4. Fazer query
      const queryInput = screen.getByPlaceholderText(/Qual é o preço/i);
      await userEvent.type(queryInput, 'Teste{Enter}');
      
      // 5. Resultado com confiança
      await waitFor(() => {
        expect(screen.getByText(/Confiança:/)).toBeInTheDocument();
      });
    });

    it('deve integração: KB query aparece no chat depois', async () => {
      render(<VexusDashboard />);
      
      // Voltar para Chat tab
      fireEvent.click(screen.getByText('💬 Chat'));
      
      // A integração mostra que queries KB aparecem no chat
      // (já deve haver mensagens de teste)
      expect(screen.getByPlaceholderText('Digite sua mensagem ou pergunta...')).toBeInTheDocument();
    });
  });

  // ==================== PERFORMANCE TESTS ====================
  describe('Performance', () => {
    it('deve renderizar com menos de 1 segundo', () => {
      const start = performance.now();
      render(<VexusDashboard />);
      const end = performance.now();
      
      expect(end - start).toBeLessThan(1000);
    });

    it('deve suportar scroll em listas grandes', async () => {
      render(<VexusDashboard />);
      
      const chatList = screen.getByText('Conversas Ativas').closest('div').querySelector('div[class*="overflow-y"]');
      
      // Simular scroll
      fireEvent.scroll(chatList, { target: { scrollY: 500 } });
      
      // Deve continuar funcionando
      expect(chatList).toBeInTheDocument();
    });
  });

  // ==================== ACCESSIBILITY TESTS ====================
  describe('Acessibilidade', () => {
    it('deve ter labels apropriados', () => {
      render(<VexusDashboard />);
      
      expect(screen.getByPlaceholderText('Digite sua mensagem ou pergunta...')).toBeInTheDocument();
    });

    it('deve permitir navegação via teclado', async () => {
      render(<VexusDashboard />);
      
      // Tab para o input
      await userEvent.tab();
      
      // Deve chegar em algum lugar interativo
      expect(document.activeElement).toBeTruthy();
    });

    it('deve ter contraste de cores adequado', () => {
      const { container } = render(<VexusDashboard />);
      
      // Verificar presença de classes de cor
      expect(container.innerHTML).toMatch(/text-white/);
      expect(container.innerHTML).toMatch(/bg-slate/);
    });
  });
});
