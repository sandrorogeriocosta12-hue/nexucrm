// Login usando cookie HttpOnly
console.log('auth.js loaded');

async function login(email, password) {
    const data = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username: email, password }),
    });
    // servidor define cookie; não armazenamos no localStorage
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
}

// Logout
function logout() {
    if (!confirm('Deseja realmente sair?')) return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    // não temos cookie JS, backend pode limpar se precisar
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

