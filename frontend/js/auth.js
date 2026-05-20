// Login usando cookie HttpOnly
console.log('auth.js loaded');

async function login(email, password) {
    const data = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
    // servidor retorna token JWT; armazenar apenas para chamadas autenticadas
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify({ user_id: data.user_id, email: data.email, name: data.name }));
    return data;
}

// Logout
function logout() {
    if (!confirm('Deseja realmente sair?')) return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login-nexus.html';
}

// Ajusta caminhos de redirecionamento também
async function checkAuth() {
    try {
        const user = await apiFetch('/auth/me');
        // Atualiza dados do usuário no menu
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) {
            userNameEl.textContent = user.email;
        }
        const userInitialEl = document.getElementById('user-initial');
        if (userInitialEl) {
            userInitialEl.textContent = user.email.charAt(0).toUpperCase();
        }
    } catch (err) {
        console.error('Auth check failed:', err);
        window.location.href = '/login-nexus.html';
    }
}

