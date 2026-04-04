// Funções auxiliares para calendário

// Formatação de datas
function formatDate(dateString) {
    const options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    return new Date(dateString).toLocaleDateString('pt-BR', options);
}

function formatTime(dateString) {
    return new Date(dateString).toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Verifica se data está vencida
function isOverdue(dateString) {
    return new Date(dateString) < new Date();
}

// Calcula dias até a data
function daysUntil(dateString) {
    const target = new Date(dateString);
    const today = new Date();
    const diff = target - today;
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}
