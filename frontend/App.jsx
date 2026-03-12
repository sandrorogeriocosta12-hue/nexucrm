/**
 * App.jsx - Exemplo de uso do Vexus Dashboard
 * Integrando com VexusClient para funcionalidade real
 */

import React, { useEffect, useState } from 'react';
import VexusDashboard from './components/VexusDashboard';
import { vexusClient } from './utils/VexusClient';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Verificar autenticação ao carregar
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('vexus_token');
      
      if (!token) {
        // Redirecionar para login
        // window.location.href = '/login';
        setLoading(false);
        return;
      }

      // Definir token no cliente
      vexusClient.setAuthToken(token);

      // Verificar health do Knowledge Lab
      const health = await vexusClient.getHealth();
      console.log('✅ Knowledge Lab Status:', health);

      // Recuperar histórico do usuário (mock)
      setUser({
        id: 1,
        name: 'Vendedor 1',
        email: 'vendedor@vexus.com',
        plan: 'premium'
      });

      setIsAuthenticated(true);
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="w-full h-screen bg-gradient-to-br from-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg mx-auto mb-4 flex items-center justify-center text-white font-bold text-4xl animate-pulse">
            V
          </div>
          <p className="text-gray-400">Carregando Vexus CRM...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div>
      <VexusDashboard />
    </div>
  );
}

/**
 * LoginPage - Página de login (placeholder)
 */
function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Mock login - alterar para API real
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const { token } = await response.json();
      localStorage.setItem('vexus_token', token);
      onLogin(token);
    } catch (err) {
      setError('Email ou senha incorretos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full h-screen bg-gradient-to-br from-slate-900 to-slate-950 flex items-center justify-center">
      <div className="w-96 p-8 bg-slate-800 rounded-lg shadow-2xl border border-slate-700">
        <div className="flex justify-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center text-white font-bold text-4xl">
            V
          </div>
        </div>

        <h1 className="text-3xl font-bold text-white text-center mb-2">Vexus CRM</h1>
        <p className="text-gray-400 text-center mb-8">Login na sua conta</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-900 border border-red-700 rounded-lg text-red-200 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold rounded-lg transition disabled:opacity-50"
          >
            {loading ? 'Carregando...' : 'Entrar'}
          </button>
        </form>

        <p className="text-center text-gray-400 text-sm mt-6">
          Não tem conta? <a href="/register" className="text-purple-400 hover:text-purple-300">Registre-se</a>
        </p>
      </div>
    </div>
  );
}
