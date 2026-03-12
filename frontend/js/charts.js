// Funções auxiliares para gráficos

// Formatação de valores monetários
function formatCurrency(value) {
    return value.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    });
}

// Formatação de números
function formatNumber(value) {
    return value.toLocaleString('pt-BR');
}

// Cores para gráficos
const chartColors = {
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#0ea5e9'
};

// Paleta de cores para gráficos
const colorPalette = [
    '#6366f1',
    '#8b5cf6',
    '#a78bfa',
    '#c4b5fd',
    '#e9d5ff',
    '#10b981',
    '#34d399',
    '#6ee7b7',
    '#a7f3d0'
];
