const API_PIPELINE_ENDPOINT = '/v1/pipeline';

function formatCurrencyBRL(value) {
    return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
}

function buildDealCard(deal) {
    const card = document.createElement('div');
    card.className = 'card';
    card.dataset.dealId = deal.id;
    card.dataset.stageId = deal.stage_id;
    card.innerHTML = `
        <div class="card-title">${deal.title}</div>
        <div class="flex gap-2 mb-2">
            <span class="card-score ${deal.probability > 0.75 ? 'score-hot' : deal.probability > 0.45 ? 'score-warm' : 'score-cold'}">
                ${deal.probability.toFixed(2)}
            </span>
            <span class="text-xs text-gray-400">${new Date(deal.updated_at).toLocaleString('pt-BR')}</span>
        </div>
        <p class="card-contact">${deal.contact_id || 'Contato não informado'}</p>
    `;
    card.addEventListener('dblclick', () => openDealModal(deal));
    return card;
}

function updateStageCounts() {
    document.querySelectorAll('.kanban-column').forEach(column => {
        const cards = column.querySelectorAll('.kanban-cards .card');
        const countElement = column.querySelector('.kanban-count');
        if (countElement) {
            countElement.textContent = cards.length;
        }
    });
}

let pipelineStageMap = {};

function openDealModal(deal) {
    const modal = document.getElementById('deal-modal');
    if (!modal) return;

    const stageName = pipelineStageMap[deal.stage_id] || deal.stage_id;

    document.getElementById('deal-modal-title').textContent = deal.title;
    document.getElementById('deal-modal-stage').textContent = stageName;
    document.getElementById('deal-modal-contact').textContent = deal.contact_id || 'Não informado';
    document.getElementById('deal-modal-value').textContent = formatCurrencyBRL(deal.value);
    document.getElementById('deal-modal-probability').textContent = `${(deal.probability * 100).toFixed(0)}%`;
    document.getElementById('deal-modal-updated').textContent = new Date(deal.updated_at).toLocaleString('pt-BR');
    document.getElementById('deal-modal-notes').textContent = deal.notes || 'Nenhuma observação disponível.';
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeDealModal() {
    const modal = document.getElementById('deal-modal');
    if (!modal) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function createStageColumn(stage) {
    const column = document.createElement('div');
    column.className = 'kanban-column';
    column.dataset.stageId = stage.id;
    column.innerHTML = `
        <div class="kanban-header">
            <span class="kanban-title">${stage.name}</span>
            <span class="kanban-count">0</span>
        </div>
        <div class="kanban-cards" data-stage-id="${stage.id}"></div>
    `;
    return column;
}

function renderPipelineBoard(stages, deals) {
    const board = document.getElementById('kanban-board');
    if (!board) return;
    board.innerHTML = '';

    pipelineStageMap = Object.fromEntries(stages.map(stage => [stage.id, stage.name]));

    stages.forEach(stage => {
        const stageDeals = deals.filter(deal => deal.stage_id === stage.id);
        const column = createStageColumn(stage);
        const cardsContainer = column.querySelector('.kanban-cards');
        stageDeals.forEach(deal => cardsContainer.appendChild(buildDealCard(deal)));
        board.appendChild(column);
    });

    initDragAndDrop();
    updateStageCounts();
}

function initDragAndDrop() {
    if (typeof Sortable === 'undefined') {
        console.warn('SortableJS não está disponível');
        return;
    }

    document.querySelectorAll('.kanban-cards').forEach(container => {
        new Sortable(container, {
            group: 'pipeline-board',
            animation: 180,
            ghostClass: 'opacity-50',
            dragClass: 'shadow-lg',
            onAdd: async evt => {
                const card = evt.item;
                const dealId = card.dataset.dealId;
                const fromStageId = evt.from.dataset.stageId;
                const toStageId = evt.to.dataset.stageId;

                card.dataset.stageId = toStageId;
                try {
                    await apiFetch(`${API_PIPELINE_ENDPOINT}/deals/${dealId}/move`, {
                        method: 'PUT',
                        body: JSON.stringify({
                            deal_id: dealId,
                            from_stage_id: fromStageId,
                            to_stage_id: toStageId,
                            new_position: evt.newIndex
                        })
                    });
                } catch (error) {
                    console.error('Falha ao mover negócio:', error);
                    evt.from.appendChild(card);
                } finally {
                    updateStageCounts();
                }
            }
        });
    });
}

async function initializePipelinePage() {
    try {
        const data = await apiFetch(API_PIPELINE_ENDPOINT);
        renderPipelineBoard(data.stages, data.deals);
    } catch (error) {
        console.error('Falha ao carregar o pipeline:', error);
        const board = document.getElementById('kanban-board');
        if (board) {
            board.innerHTML = `
                <div class="w-full text-center text-gray-300 py-16">
                    Não foi possível carregar o pipeline no momento.
                </div>
            `;
        }
    }

    const modalClose = document.getElementById('deal-modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', closeDealModal);
    }

    const modal = document.getElementById('deal-modal');
    if (modal) {
        modal.addEventListener('click', event => {
            if (event.target === modal) {
                closeDealModal();
            }
        });
    }
}
