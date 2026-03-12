// Common UI behaviors for Nexus Service demo pages
// Requires auth.js and api.js already loaded (apiFetch/ login/ logout etc.)

async function sendMessage() {
    const input = document.querySelector('main input[type="text"]');
    const text = input.value.trim();
    if (!text) return;

    // append outgoing bubble
    const chatArea = document.querySelector('.chat-message') ? document.querySelector('.chat-message').parentNode : null;
    if (chatArea) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-message chat-outgoing';
        bubble.innerHTML = `<p class="text-sm"></p><p class="text-xs text-gray-300 mt-1"></p>`;
        bubble.querySelector('p').textContent = text;
        bubble.querySelector('p.text-xs').textContent = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
        chatArea.appendChild(bubble);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    input.value = '';

    // if the message contains a phone number, create lead via API
    const phoneRegex = /(\+?[0-9][0-9\-(). ]{6,})/g;
    const match = phoneRegex.exec(text);
    if (match) {
        try {
            await apiFetch('/leads', {
                method: 'POST',
                body: JSON.stringify({ phone: match[0], status: 'new' })
            });
            alert('Telefone registrado como lead!');
        } catch (err) {
            console.error('Failed to create lead:', err);
        }
    }
}


// KPI dashboard helper
async function loadDashboard() {
    const statuses = ['new','qualified','proposal','contract'];
    for (let status of statuses) {
        try {
            const items = await apiFetch(`/leads?status=${status}`);
            const countEl = document.querySelector(`.kpi-count[data-status="${status}"]`);
            if (countEl) {
                countEl.textContent = items.length;
            }
        } catch (err) {
            console.warn('dashboard load error', err);
        }
    }
}

// Pipeline helper: click card moves to next column
function enablePipeline() {
    const order = ['new','qualified','proposal','contract'];
    document.querySelectorAll('.kanban-cards .card').forEach(card => {
        card.style.cursor = 'pointer';
        card.addEventListener('click', async () => {
            const current = card.dataset.status || 'new';
            const idx = order.indexOf(current);
            const next = order[idx+1] || order[idx];
            card.dataset.status = next;
            card.style.opacity = '0.5';
            // move DOM element to next column container if exists
            const nextCol = document.querySelector(`.kanban-column:nth-child(${idx+2}) .kanban-cards`);
            if (nextCol) {
                nextCol.appendChild(card);
            }
            try {
                if (card.dataset.leadId) {
                    await apiFetch(`/leads/${card.dataset.leadId}`, {
                        method: 'PUT',
                        body: JSON.stringify({status: next})
                    });
                }
                setTimeout(()=>card.style.opacity='1',200);
            } catch(e){ console.error(e); }
        });
    });
}

// initialization for each page
function initPage() {
    if (typeof checkAuth === 'function') {
        checkAuth(); // will redirect to login if not authenticated
    }
    if (document.body.classList.contains('inbox-page')) {
        const sendBtn = document.getElementById('send-button');
        if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    }
    if (document.body.classList.contains('kpi-page')) {
        loadDashboard();
    }
    if (document.body.classList.contains('pipeline-page')) {
        enablePipeline();
    }
}

document.addEventListener('DOMContentLoaded', initPage);
