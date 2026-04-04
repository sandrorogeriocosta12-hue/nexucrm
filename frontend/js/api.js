// Configuração da API
const API_BASE_URL = 'http://localhost:8002'; // mude para seu domínio em produção

console.log('api.js loaded, API_BASE_URL:', API_BASE_URL);

async function apiFetch(endpoint, options = {}) {
    // usa cookies para autenticação; envia credenciais automaticamente
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        credentials: 'include',
        ...options,
        headers,
    });

    if (response.status === 401) {
        // Token inválido ou expirado – redireciona para login
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login.html';
        throw new Error('Não autenticado');
    }

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'Erro na requisição');
    }
    return data;
}
