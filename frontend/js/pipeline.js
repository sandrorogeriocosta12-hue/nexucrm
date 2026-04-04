// Scripts auxiliares para pipeline

// Funcionalidades extra para o drag & drop
function initSortable(element, onDropCallback) {
    if (typeof Sortable !== 'undefined') {
        new Sortable(element, {
            group: 'shared',
            animation: 150,
            ghostClass: 'opacity-50',
            dragClass: 'shadow-lg',
            onEnd: onDropCallback
        });
    }
}

// Suporte para busca em tempo real nas colunas
function filterPipelineCards(searchTerm) {
    const cards = document.querySelectorAll('.kanban-card');
    cards.forEach(card => {
        const title = card.querySelector('.font-medium')?.textContent || '';
        const contact = card.querySelector('.text-xs')?.textContent || '';
        const match = title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                      contact.toLowerCase().includes(searchTerm.toLowerCase());
        card.style.display = match ? '' : 'none';
    });
}
