/**
 * VexusClient - Cliente JavaScript para integração com Vexus Backend
 * Fornece métodos para Chat, Knowledge Lab, Proposals e mais
 */

export class VexusClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('vexus_token') || ''}`
    };
  }

  // ==================== KNOWLEDGE LAB ====================

  /**
   * Upload PDF para Knowledge Lab
   * @param {File} file - Arquivo PDF
   * @param {string} docType - Tipo do documento (product_manual, pricing, etc)
   * @returns {Promise} { id, name, chunks, size, indexed_at }
   */
  async uploadDocument(file, docType = 'general') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);

    try {
      const response = await fetch(`${this.baseURL}/api/knowledge-lab/upload`, {
        method: 'POST',
        headers: { 'Authorization': this.headers['Authorization'] },
        body: formData
      });

      if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('Upload Document Error:', error);
      throw error;
    }
  }

  /**
   * Query Knowledge Lab com RAG
   * @param {string} query - Pergunta do usuário
   * @param {number} k - Número de chunks a retornar (default: 3)
   * @returns {Promise} { response, confidence, source_document, chunks_used }
   */
  async queryKnowledgeBase(query, k = 3) {
    try {
      const response = await fetch(`${this.baseURL}/api/knowledge-lab/query`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ query, k })
      });

      if (!response.ok) throw new Error(`Query failed: ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('Query KB Error:', error);
      throw error;
    }
  }

  /**
   * Listar todos os documentos indexados
   * @returns {Promise} Array de documentos
   */
  async listDocuments() {
    try {
      const response = await fetch(`${this.baseURL}/api/knowledge-lab/documents`, {
        method: 'GET',
        headers: this.headers
      });

      if (!response.ok) throw new Error('Failed to list documents');
      return await response.json();
    } catch (error) {
      console.error('List Documents Error:', error);
      throw error;
    }
  }

  /**
   * Deletar documento
   * @param {number} docId - ID do documento
   * @returns {Promise}
   */
  async deleteDocument(docId) {
    try {
      const response = await fetch(`${this.baseURL}/api/knowledge-lab/documents/${docId}`, {
        method: 'DELETE',
        headers: this.headers
      });

      if (!response.ok) throw new Error('Failed to delete document');
      return await response.json();
    } catch (error) {
      console.error('Delete Document Error:', error);
      throw error;
    }
  }

  /**
   * Obter histórico de queries
   * @param {number} limit - Limite de resultados (default: 10)
   * @returns {Promise} Array de queries
   */
  async getQueryHistory(limit = 10) {
    try {
      const response = await fetch(
        `${this.baseURL}/api/knowledge-lab/history?limit=${limit}`,
        { method: 'GET', headers: this.headers }
      );

      if (!response.ok) throw new Error('Failed to get history');
      return await response.json();
    } catch (error) {
      console.error('Get History Error:', error);
      throw error;
    }
  }

  /**
   * Health check
   * @returns {Promise} { status, knowledge_base_ready, documents_count }
   */
  async getHealth() {
    try {
      const response = await fetch(`${this.baseURL}/api/knowledge-lab/health`, {
        method: 'GET',
        headers: this.headers
      });

      if (!response.ok) throw new Error('Health check failed');
      return await response.json();
    } catch (error) {
      console.error('Health Check Error:', error);
      throw error;
    }
  }

  // ==================== CHAT & MESSAGING ====================

  /**
   * Enviar mensagem de chat
   * @param {number} chatId - ID da conversa
   * @param {string} message - Conteúdo da mensagem
   * @param {string} mode - Modo IA (Assistente, Humano, Autônoma)
   * @returns {Promise} { id, response, confidence, mode }
   */
  async sendMessage(chatId, message, mode = 'Assistente') {
    try {
      const response = await fetch(`${this.baseURL}/api/chat/send`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ chat_id: chatId, message, mode })
      });

      if (!response.ok) throw new Error('Failed to send message');
      return await response.json();
    } catch (error) {
      console.error('Send Message Error:', error);
      throw error;
    }
  }

  /**
   * Obter mensagens de uma conversa
   * @param {number} chatId - ID da conversa
   * @param {number} limit - Limite de mensagens (default: 50)
   * @returns {Promise} Array de mensagens
   */
  async getMessages(chatId, limit = 50) {
    try {
      const response = await fetch(
        `${this.baseURL}/api/chat/${chatId}/messages?limit=${limit}`,
        { method: 'GET', headers: this.headers }
      );

      if (!response.ok) throw new Error('Failed to get messages');
      return await response.json();
    } catch (error) {
      console.error('Get Messages Error:', error);
      throw error;
    }
  }

  // ==================== LEADS & CONTACTS ====================

  /**
   * Calcular lead score
   * @param {number} leadId - ID do lead
   * @returns {Promise} { score, factors, recommendation }
   */
  async calculateLeadScore(leadId) {
    try {
      const response = await fetch(`${this.baseURL}/api/leads/${leadId}/score`, {
        method: 'GET',
        headers: this.headers
      });

      if (!response.ok) throw new Error('Failed to calculate score');
      return await response.json();
    } catch (error) {
      console.error('Calculate Score Error:', error);
      throw error;
    }
  }

  /**
   * Obter recomendações (Whisper Mode)
   * @param {number} leadId - ID do lead
   * @returns {Promise} { recommendation, confidence, actions }
   */
  async getWhisperRecommendation(leadId) {
    try {
      const response = await fetch(`${this.baseURL}/api/leads/${leadId}/whisper`, {
        method: 'GET',
        headers: this.headers
      });

      if (!response.ok) throw new Error('Failed to get recommendation');
      return await response.json();
    } catch (error) {
      console.error('Get Whisper Error:', error);
      throw error;
    }
  }

  // ==================== PROPOSALS ====================

  /**
   * Gerar proposta automática
   * @param {number} leadId - ID do lead
   * @param {string} productType - Tipo de produto
   * @returns {Promise} { id, html, pdf_url, estimated_value }
   */
  async generateProposal(leadId, productType) {
    try {
      const response = await fetch(`${this.baseURL}/api/proposals/generate`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ lead_id: leadId, product_type: productType })
      });

      if (!response.ok) throw new Error('Failed to generate proposal');
      return await response.json();
    } catch (error) {
      console.error('Generate Proposal Error:', error);
      throw error;
    }
  }

  /**
   * Enviar proposta
   * @param {number} proposalId - ID da proposta
   * @param {string} channel - Canal (whatsapp, email, etc)
   * @returns {Promise}
   */
  async sendProposal(proposalId, channel = 'whatsapp') {
    try {
      const response = await fetch(`${this.baseURL}/api/proposals/${proposalId}/send`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ channel })
      });

      if (!response.ok) throw new Error('Failed to send proposal');
      return await response.json();
    } catch (error) {
      console.error('Send Proposal Error:', error);
      throw error;
    }
  }

  // ==================== UTILITIES ====================

  /**
   * Upload com progress callback
   * @param {File} file - Arquivo
   * @param {Function} onProgress - Callback com { loaded, total }
   * @returns {Promise}
   */
  async uploadWithProgress(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append('file', file);

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress({
            loaded: e.loaded,
            total: e.total,
            percent: Math.round((e.loaded / e.total) * 100)
          });
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Upload failed')));

      xhr.open('POST', `${this.baseURL}/api/knowledge-lab/upload`);
      xhr.setRequestHeader('Authorization', this.headers['Authorization']);
      xhr.send(formData);
    });
  }

  /**
   * Definir token de autenticação
   * @param {string} token - JWT token
   */
  setAuthToken(token) {
    this.headers['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('vexus_token', token);
  }

  /**
   * Limpar token
   */
  clearAuthToken() {
    delete this.headers['Authorization'];
    localStorage.removeItem('vexus_token');
  }
}

// Singleton instance
export const vexusClient = new VexusClient();

export default vexusClient;
