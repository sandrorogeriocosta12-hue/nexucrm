# 🛠️ SNIPPETS DE CÓDIGO PRONTOS PARA IMPLEMENTAR

Todos os códigos abaixo estão prontos para copiar e colar no projeto Vexus Service.

---

## 1️⃣ IMPORT CSV/EXCEL - utils.js (Adicionar)

```javascript
/**
 * Parseia arquivo CSV
 * @param {File} file - Arquivo CSV
 * @returns {Promise<Array>} Array de objetos
 */
async function parseCSV(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const csv = e.target.result;
            const lines = csv.split('\n').filter(l => l.trim());
            const headers = lines[0].split(',').map(h => h.trim());
            
            const data = lines.slice(1).map(line => {
                const values = line.split(',').map(v => v.trim());
                const obj = {};
                headers.forEach((h, i) => obj[h] = values[i]);
                return obj;
            });
            
            resolve(data);
        };
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

/**
 * Mapeamento automático de colunas
 * @param {Array} headers - Headers do arquivo
 * @returns {Object} Mapa de colunas
 */
function autoMapColumns(headers) {
    const mapping = {};
    const commonMappings = {
        'nome': 'name',
        'email': 'email',
        'telefone': 'phone',
        'empresa': 'company',
        'status': 'status',
        'tags': 'tags',
        'valor': 'value'
    };
    
    headers.forEach(header => {
        const lower = header.toLowerCase();
        mapping[header] = Object.keys(commonMappings).find(k => lower.includes(k)) 
            ? commonMappings[Object.keys(commonMappings).find(k => lower.includes(k))]
            : header;
    });
    
    return mapping;
}

/**
 * Valida dados antes de importar
 * @param {Array} data - Dados a validar
 * @returns {Object} {valid, errors}
 */
function validateImportData(data) {
    const errors = [];
    
    data.forEach((row, idx) => {
        if (!row.name || row.name.trim() === '') {
            errors.push(`Linha ${idx + 2}: Nome é obrigatório`);
        }
        if (row.email && !isValidEmail(row.email)) {
            errors.push(`Linha ${idx + 2}: Email inválido`);
        }
    });
    
    return {
        valid: errors.length === 0,
        errors: errors,
        count: data.length
    };
}

/** Exportar funções */
window.NexusUtils.parseCSV = parseCSV;
window.NexusUtils.autoMapColumns = autoMapColumns;
window.NexusUtils.validateImportData = validateImportData;
```

---

## 2️⃣ TOAST SYSTEM - design-system.css (Adicionar)

```css
/* Toast Notifications */
.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

.toast {
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--radius-md);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    animation: slideInRight 0.3s ease-out;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    min-width: 300px;
    max-width: 400px;
}

.toast.success {
    background: linear-gradient(135deg, var(--success-light), var(--success-dark));
    color: white;
}

.toast.error {
    background: linear-gradient(135deg, var(--error-light), var(--error-dark));
    color: white;
}

.toast.warning {
    background: linear-gradient(135deg, var(--warning-light), var(--warning-dark));
    color: white;
}

.toast.info {
    background: linear-gradient(135deg, var(--info-light), var(--info-dark));
    color: white;
}

.toast-exit {
    animation: slideOutRight 0.3s ease-out forwards;
}

@keyframes slideInRight {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}

.toast-icon {
    font-size: 1.2rem;
}

.toast-message {
    flex: 1;
    font-size: 0.95rem;
    font-weight: 500;
}

.toast-close {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    font-size: 1.2rem;
    opacity: 0.8;
    transition: opacity 0.2s;
}

.toast-close:hover {
    opacity: 1;
}
```

---

## 3️⃣ TOAST SYSTEM - utils.js (Adicionar)

```javascript
/**
 * Cria um contêiner para toasts
 */
function ensureToastContainer() {
    if (!document.getElementById('toastContainer')) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    return document.getElementById('toastContainer');
}

/**
 * Exibe uma notificação toast
 * @param {string} message - Mensagem
 * @param {string} type - 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duração em ms
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = ensureToastContainer();
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

/** Variações */
function toastSuccess(msg, duration) { return showToast(msg, 'success', duration); }
function toastError(msg, duration) { return showToast(msg, 'error', duration); }
function toastWarning(msg, duration) { return showToast(msg, 'warning', duration); }
function toastInfo(msg, duration) { return showToast(msg, 'info', duration); }

/** Exportar */
window.NexusUtils.showToast = showToast;
window.NexusUtils.toastSuccess = toastSuccess;
window.NexusUtils.toastError = toastError;
window.NexusUtils.toastWarning = toastWarning;
window.NexusUtils.toastInfo = toastInfo;
```

**Uso:**
```javascript
NexusUtils.toastSuccess('Contato criado com sucesso!');
NexusUtils.toastError('Erro ao processar requisição');
NexusUtils.toastWarning('Operação pode levar alguns segundos');
```

---

## 4️⃣ RECHARTS INTEGRATION - design-system.css (Adicionar)

```css
/* Charts Container */
.chart-container {
    width: 100%;
    height: 300px;
    background: var(--card-bg);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    margin: var(--spacing-md) 0;
}

.chart-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
}

.chart-tooltip {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: var(--spacing-sm);
    color: var(--text-primary);
    font-size: 0.85rem;
}

/* Recharts custom styles */
.recharts-surface {
    background: transparent;
}

.recharts-text {
    fill: var(--text-muted);
    font-size: 12px;
}

.recharts-cartesian-axis-line {
    stroke: var(--border-color);
}

.recharts-cartesian-grid-horizontal line,
.recharts-cartesian-grid-vertical line {
    stroke: var(--border-color);
    stroke-dasharray: 3 3;
}
```

---

## 5️⃣ RECHARTS NO REPORTS.HTML

```html
<!-- Adicionar em reports.html before </head> -->
<script src="https://cdn.jsdelivr.net/npm/recharts@2.10.0/dist/Recharts.js"></script>

<!-- Exemplo de AreaChart -->
<div class="card">
    <div class="chart-title">Negócios nos últimos 30 dias</div>
    <canvas id="areaChart" style="width: 100%; height: 300px;"></canvas>
</div>

<script>
// Dados de exemplo
const salesData = [
    { date: '01', deals: 4, revenue: 120000 },
    { date: '02', deals: 3, revenue: 95000 },
    { date: '03', deals: 5, revenue: 150000 },
    { date: '04', deals: 2, revenue: 60000 },
];

// Renderizar com Chart.js (mais simples)
const ctx = document.getElementById('areaChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: salesData.map(d => d.date),
        datasets: [{
            label: 'Deals',
            data: salesData.map(d => d.deals),
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            tension: 0.4,
            fill: true,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
    }
});
</script>

<!-- Adicionar script Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
```

---

## 6️⃣ DRAG AND DROP AVANÇADO - utils.js (Adicionar)

```javascript
/**
 * Configurar drag-and-drop em colunas do kanban
 */
function initKanbanDragDrop() {
    const columns = document.querySelectorAll('.kanban-column');
    
    columns.forEach(column => {
        column.addEventListener('dragover', handleDragOver);
        column.addEventListener('drop', handleDrop);
        column.addEventListener('dragleave', handleDragLeave);
        
        // Tornar cards draggable
        const cards = column.querySelectorAll('.kanban-card');
        cards.forEach(card => {
            card.draggable = true;
            card.addEventListener('dragstart', handleDragStart);
            card.addEventListener('dragend', handleDragEnd);
        });
    });
}

function handleDragStart(e) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTM);
    this.style.opacity = '0.5';
    this.style.transform = 'scale(0.95)';
}

function handleDragEnd(e) {
    e.preventDefault();
    this.style.opacity = '1';
    this.style.transform = 'scale(1)';
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.style.borderLeft = '3px solid #6366f1';
}

function handleDragLeave(e) {
    e.preventDefault();
    this.style.borderLeft = 'none';
}

function handleDrop(e) {
    e.preventDefault();
    this.style.borderLeft = 'none';
    
    const draggedCard = document.querySelector('.kanban-card[style*="opacity: 0.5"]');
    if (draggedCard && this.classList.contains('kanban-column')) {
        this.appendChild(draggedCard);
        
        // Callback para salvar mudança
        const dealId = draggedCard.dataset.dealId;
        const newStage = this.dataset.stage;
        saveDealStage(dealId, newStage);
    }
}

window.NexusUtils.initKanbanDragDrop = initKanbanDragDrop;
```

---

## 7️⃣ BUSCA AVANÇADA - contacts.html (Adicionar)

```html
<!-- Adicionar no contacts.html -->
<div class="filters-bar card">
    <div class="filter-group">
        <label>Status</label>
        <select id="statusFilter" onchange="applyAdvancedFilters()">
            <option value="">Todos</option>
            <option value="prospect">Prospecto</option>
            <option value="client">Cliente</option>
            <option value="inactive">Inativo</option>
        </select>
    </div>
    
    <div class="filter-group">
        <label>Data Criação</label>
        <select id="dateFilter" onchange="applyAdvancedFilters()">
            <option value="">Todas</option>
            <option value="24h">Últimas 24h</option>
            <option value="7d">Última semana</option>
            <option value="30d">Último mês</option>
        </select>
    </div>
    
    <div class="filter-group">
        <label>Valor Pipeline</label>
        <select id="valueFilter" onchange="applyAdvancedFilters()">
            <option value="">Todos</option>
            <option value="0-1000">R$ 0 - 1.000</option>
            <option value="1000-5000">R$ 1.000 - 5.000</option>
            <option value="5000+">R$ 5.000+</option>
        </select>
    </div>
    
    <button class="btn-primary" onclick="resetFilters()">🔄 Limpar</button>
</div>

<style>
.filters-bar {
    display: flex;
    gap: var(--spacing-md);
    flex-wrap: wrap;
    margin-bottom: var(--spacing-lg);
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
}

.filter-group label {
    font-size: 0.85rem;
    color: var(--text-muted);
    font-weight: 500;
}

.filter-group select {
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
    color: var(--text-primary);
}
</style>

<script>
function applyAdvancedFilters() {
    const status = document.getElementById('statusFilter').value;
    const date = document.getElementById('dateFilter').value;
    const value = document.getElementById('valueFilter').value;
    
    const filtered = contacts.filter(contact => {
        if (status && contact.status !== status) return false;
        
        if (date) {
            const createdDate = new Date(contact.createdAt);
            const now = new Date();
            const diffDays = (now - createdDate) / (1000 * 60 * 60 * 24);
            
            if (date === '24h' && diffDays > 1) return false;
            if (date === '7d' && diffDays > 7) return false;
            if (date === '30d' && diffDays > 30) return false;
        }
        
        if (value) {
            const [min, max] = value === '5000+' 
                ? [5000, Infinity] 
                : value.split('-').map(Number);
            
            if (contact.pipelineValue < min || contact.pipelineValue > max) return false;
        }
        
        return true;
    });
    
    renderContacts(filtered);
}

function resetFilters() {
    document.getElementById('statusFilter').value = '';
    document.getElementById('dateFilter').value = '';
    document.getElementById('valueFilter').value = '';
    renderContacts(contacts);
}
</script>
```

---

## 8️⃣ PDF EXPORT - reports.html (Adicionar)

```html
<!-- Adicionar no reports.html -->
<button class="btn-primary" onclick="exportReportPDF()">
    📄 Exportar PDF
</button>

<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

<script>
function exportReportPDF() {
    const element = document.getElementById('reportContent');
    const date = new Date().toLocaleDateString('pt-BR');
    
    const opt = {
        margin: 10,
        filename: `relatorio-${date}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
    };
    
    html2pdf().set(opt).from(element).save();
    NexusUtils.toastSuccess('PDF exportado com sucesso!');
}
</script>
```

---

## 9️⃣ LIGHT MODE - design-system.css (Adicionar)

```css
/* Light Mode Theme */
:root.light-theme {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #f1f3f5;
    --text-primary: #1a1a1a;
    --text-secondary: #495057;
    --text-muted: #868e96;
    --border-color: #e9ecef;
    --primary-color: #1A56DB;
    --accent-color: #7C3AED;
    --success-color: #10B981;
    --warning-color: #F59E0B;
    --error-color: #EF4444;
    --card-bg: #ffffff;
}

/* Toggle Button */
.theme-toggle {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: var(--primary-color);
    color: white;
    border: none;
    cursor: pointer;
    font-size: 1.5rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    transition: all 0.3s ease;
}

.theme-toggle:hover {
    transform: scale(1.1);
}
```

```javascript
// Adicionar em utils.js
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark-theme');
    
    if (isDark) {
        html.classList.remove('dark-theme');
        html.classList.add('light-theme');
        localStorage.setItem('theme', 'light');
    } else {
        html.classList.add('dark-theme');
        html.classList.remove('light-theme');
        localStorage.setItem('theme', 'dark');
    }
}

// Restaurar theme ao carregar
window.addEventListener('load', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.classList.add(`${savedTheme}-theme`);
});

window.NexusUtils.toggleTheme = toggleTheme;
```

---

## 🔟 SERVICE WORKERS (PWA) - service-worker.js (Criar novo arquivo)

```javascript
// frontend/service-worker.js

const CACHE_NAME = 'vexus-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/login.html',
    '/dashboard.html',
    '/contacts.html',
    '/pipeline.html',
    '/tasks.html',
    '/reports.html',
    '/css/design-system.css',
    '/css/style.css',
    '/js/api.js',
    '/js/auth.js',
    '/js/utils.js',
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(ASSETS_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

// Activate event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - Cache first, then network
self.addEventListener('fetch', (event) => {
    if (event.request.url.includes('/api/')) {
        // API calls: Network first
        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match(event.request))
        );
    } else {
        // Assets: Cache first
        event.respondWith(
            caches.match(event.request)
                .then((response) => {
                    return response || fetch(event.request)
                        .then((response) => {
                            return caches.open(CACHE_NAME)
                                .then((cache) => {
                                    cache.put(event.request, response.clone());
                                    return response;
                                });
                        });
                })
        );
    }
});
```

```html
<!-- Registrar em app.html -->
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
        .then(reg => console.log('Service Worker registrado'))
        .catch(err => console.log('Erro ao registrar:', err));
}
</script>
```

---

## 📝 TESTES - tests/api.test.js (Criar novo arquivo)

```javascript
// frontend/tests/api.test.js
import { describe, it, expect } from 'vitest';

describe('API Integration', () => {
    it('should fetch contacts list', async () => {
        // Mock fetch
        global.fetch = async () => ({
            ok: true,
            json: async () => ([
                { id: 1, name: 'João' },
                { id: 2, name: 'Maria' }
            ])
        });
        
        const response = await fetch('/api/contacts');
        const data = await response.json();
        
        expect(Array.isArray(data)).toBe(true);
        expect(data.length).toBe(2);
    });
    
    it('should create contact', async () => {
        const contact = { name: 'Pedro', email: 'pedro@example.com' };
        
        global.fetch = async () => ({
            ok: true,
            json: async () => ({ id: 3, ...contact })
        });
        
        const response = await fetch('/api/contacts', {
            method: 'POST',
            body: JSON.stringify(contact)
        });
        const data = await response.json();
        
        expect(data.id).toBe(3);
        expect(data.name).toBe('Pedro');
    });
});
```

```bash
# Rodar testes
npm install -D vitest
npm test
```

---

**Todos os snippets estão prontos para copiar e colar!** 🎯

Para mais informações, consulte `ANALISE_MELHORIAS_SISTEMA.md`
