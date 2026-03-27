/**
 * ═════════════════════════════════════════════════════════════════  
 * NEXUS CRM - Utilities & Helpers (Mobile & Web)
 * ═════════════════════════════════════════════════════════════════ 
 */

// ─── Avatar Colors (baseado no mobile) ───
const AVATAR_COLORS = [
  'avatar-color-1', // #1A56DB
  'avatar-color-2', // #7C3AED
  'avatar-color-3', // #10B981
  'avatar-color-4', // #F59E0B
  'avatar-color-5', // #EF4444
  'avatar-color-6', // #EC4899
];

const TAG_COLORS = {
  blue: { class: 'badge-primary', hex: '#3B82F6' },
  green: { class: 'badge-success', hex: '#10B981' },
  red: { class: 'badge-error', hex: '#EF4444' },
  yellow: { class: 'badge-warning', hex: '#F59E0B' },
  purple: { class: 'badge-accent', hex: '#8B5CF6' },
  orange: { class: 'badge-warning', hex: '#F97316' },
  pink: { class: 'badge-error', hex: '#EC4899' },
};

const PRIORITY_COLORS = {
  low: { class: 'badge-success', label: 'Baixa' },
  medium: { class: 'badge-warning', label: 'Média' },
  high: { class: 'badge-error', label: 'Alta' },
};

const PIPELINE_STAGES = [
  { id: 'lead', label: 'Lead', color: '#64748B' },
  { id: 'qualified', label: 'Qualificado', color: '#3B82F6' },
  { id: 'proposal', label: 'Proposta', color: '#8B5CF6' },
  { id: 'negotiation', label: 'Negociação', color: '#F59E0B' },
  { id: 'won', label: 'Ganho', color: '#10B981' },
  { id: 'lost', label: 'Perdido', color: '#EF4444' },
];

// ═════════════════════════════════════════════════════════════════
// AVATAR UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Generate initials from a name
 * @param {string} name - Full name
 * @returns {string} - Initials (e.g., "John Doe" -> "JD")
 */
function getInitials(name) {
  return name
    .split(' ')
    .map(n => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

/**
 * Get avatar color based on name hash
 * @param {string} name - Full name
 * @returns {string} - Avatar color class
 */
function getAvatarColor(name) {
  const code = name.charCodeAt(0);
  return AVATAR_COLORS[code % AVATAR_COLORS.length];
}

/**
 * Create avatar HTML element
 * @param {string} name - Full name
 * @param {string} size - Size class (avatar-sm, avatar-md, avatar-lg)
 * @returns {HTMLElement} - Avatar div
 */
function createAvatar(name, size = 'avatar-md') {
  const avatar = document.createElement('div');
  avatar.className = `avatar ${size} ${getAvatarColor(name)}`;
  avatar.textContent = getInitials(name);
  avatar.title = name;
  return avatar;
}

/**
 * Create avatar HTML string
 * @param {string} name - Full name
 * @param {string} size - Size class
 * @returns {string} - HTML string
 */
function createAvatarHTML(name, size = 'avatar-md') {
  const color = getAvatarColor(name);
  const initials = getInitials(name);
  return `<div class="avatar ${size} ${color}" title="${name}">${initials}</div>`;
}

// ═════════════════════════════════════════════════════════════════
// BADGE & TAG UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Create tag badge HTML
 * @param {string} label - Tag label
 * @param {string} color - Tag color (blue, green, red, etc)
 * @returns {string} - HTML string
 */
function createTagBadge(label, color = 'blue') {
  const tagInfo = TAG_COLORS[color] || TAG_COLORS.blue;
  return `<span class="badge ${tagInfo.class}">${label}</span>`;
}

/**
 * Create priority badge
 * @param {string} priority - Priority level (low, medium, high)
 * @returns {string} - HTML string
 */
function createPriorityBadge(priority) {
  const info = PRIORITY_COLORS[priority] || PRIORITY_COLORS.medium;
  return `<span class="badge ${info.class}">${info.label}</span>`;
}

/**
 * Create status badge
 * @param {string} status - Status (ativo, inativo, prospect, etc)
 * @returns {string} - HTML string
 */
function createStatusBadge(status) {
  const statusMap = {
    ativo: { class: 'badge-success', label: 'Ativo' },
    inativo: { class: 'badge-error', label: 'Inativo' },
    prospect: { class: 'badge-primary', label: 'Prospect' },
    cliente: { class: 'badge-accent', label: 'Cliente' },
  };
  
  const info = statusMap[status] || { class: 'badge-primary', label: status };
  return `<span class="badge ${info.class}">${info.label}</span>`;
}

// ═════════════════════════════════════════════════════════════════
// FILTER UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Filter array by search term across multiple fields
 * @param {Array} items - Items to filter
 * @param {string} searchTerm - Search term
 * @param {Array} fields - Fields to search in
 * @returns {Array} - Filtered items
 */
function filterBySearch(items, searchTerm, fields = ['name', 'email', 'company']) {
  if (!searchTerm) return items;
  
  const term = searchTerm.toLowerCase();
  return items.filter(item =>
    fields.some(field => {
      const value = item[field] || '';
      return value.toString().toLowerCase().includes(term);
    })
  );
}

/**
 * Filter array by tags
 * @param {Array} items - Items to filter
 * @param {Array} tags - Tag labels to filter by
 * @returns {Array} - Filtered items
 */
function filterByTags(items, tags) {
  if (!tags || tags.length === 0) return items;
  
  return items.filter(item =>
    item.tags && item.tags.some(tag => tags.includes(tag.label))
  );
}

/**
 * Filter array by status
 * @param {Array} items - Items to filter
 * @param {string} status - Status to filter by
 * @returns {Array} - Filtered items
 */
function filterByStatus(items, status) {
  if (!status) return items;
  return items.filter(item => item.status === status);
}

/**
 * Apply multiple filters
 * @param {Array} items - Items to filter
 * @param {Object} filters - Filter object
 * @returns {Array} - Filtered items
 */
function applyFilters(items, filters = {}) {
  let filtered = items;
  
  if (filters.search) {
    filtered = filterBySearch(filtered, filters.search);
  }
  
  if (filters.tags && filters.tags.length > 0) {
    filtered = filterByTags(filtered, filters.tags);
  }
  
  if (filters.status) {
    filtered = filterByStatus(filtered, filters.status);
  }
  
  return filtered;
}

// ═════════════════════════════════════════════════════════════════
// CARD UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Create contact card HTML
 * @param {Object} contact - Contact object
 * @returns {string} - HTML string
 */
function createContactCardHTML(contact) {
  const avatar = createAvatarHTML(contact.name, 'avatar-md');
  const tagsHTML = contact.tags
    .slice(0, 2)
    .map(tag => createTagBadge(tag.label, tag.color))
    .join('');
  
  return `
    <div class="card cursor-pointer animate-slideIn">
      <div class="flex-gap-md">
        ${avatar}
        <div class="flex-1">
          <h3 class="font-semibold text-lg">${contact.name}</h3>
          <p class="text-muted text-sm">${contact.role} · ${contact.company}</p>
          ${tagsHTML ? `<div class="flex-gap-md mt-2">${tagsHTML}</div>` : ''}
        </div>
        <span class="text-muted">→</span>
      </div>
    </div>
  `;
}

/**
 * Create deal card HTML
 * @param {Object} deal - Deal object
 * @returns {string} - HTML string
 */
function createDealCardHTML(deal) {
  return `
    <div class="card cursor-pointer animate-slideIn">
      <div class="flex-between mb-2">
        <h3 class="font-semibold">${deal.title}</h3>
        <span class="text-accent font-bold">R$ ${formatCurrency(deal.value)}</span>
      </div>
      <p class="text-muted text-sm">${deal.company}</p>
      <div class="flex-between mt-3 text-xs text-muted">
        <span>📅 ${deal.closingDate}</span>
        <span class="badge badge-accent">${deal.stage}</span>
      </div>
    </div>
  `;
}

/**
 * Create task card HTML
 * @param {Object} task - Task object
 * @returns {string} - HTML string
 */
function createTaskCardHTML(task) {
  return `
    <div class="card">
      <div class="flex-between">
        <div>
          <h3 class="font-semibold">${task.title}</h3>
          <p class="text-muted text-sm">${task.description}</p>
        </div>
        ${createPriorityBadge(task.priority)}
      </div>
      <div class="flex-between mt-3 text-xs">
        <span class="text-muted">📅 ${task.dueDate}</span>
        <label class="flex-gap-md cursor-pointer">
          <input type="checkbox" ${task.status === 'done' ? 'checked' : ''}>
          <span class="text-muted">${task.status === 'done' ? 'Concluída' : 'Pendente'}</span>
        </label>
      </div>
    </div>
  `;
}

// ═════════════════════════════════════════════════════════════════
// FORMATTING UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Format currency for display
 * @param {number} value - Value to format
 * @returns {string} - Formatted string
 */
function formatCurrency(value) {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k`;
  }
  return value.toLocaleString('pt-BR');
}

/**
 * Format date for display
 * @param {string} dateStr - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format datetime for display
 * @param {string} dateStr - ISO datetime string
 * @returns {string} - Formatted datetime
 */
function formatDateTime(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('pt-BR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Get time ago string (e.g., "2 horas atrás")
 * @param {string} dateStr - ISO date string
 * @returns {string} - Time ago string
 */
function getTimeAgo(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  
  if (seconds < 60) return 'agora';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m atrás`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h atrás`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d atrás`;
  
  return formatDate(dateStr);
}

// ═════════════════════════════════════════════════════════════════
// MODAL UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Show modal
 * @param {string} modalId - Modal element ID
 */
function showModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('modal-hidden');
    modal.classList.add('modal-visible');
    document.body.style.overflow = 'hidden';
  }
}

/**
 * Hide modal
 * @param {string} modalId - Modal element ID
 */
function hideModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('modal-visible');
    modal.classList.add('modal-hidden');
    document.body.style.overflow = 'auto';
  }
}

/**
 * Toggle modal
 * @param {string} modalId - Modal element ID
 */
function toggleModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal && modal.classList.contains('modal-visible')) {
    hideModal(modalId);
  } else {
    showModal(modalId);
  }
}

// ═════════════════════════════════════════════════════════════════
// NOTIFICATION UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Show notification
 * @param {string} message - Notification message
 * @param {string} type - Type (success, error, info, warning)
 * @param {number} duration - Duration in ms (0 = persistent)
 */
function showNotification(message, type = 'info', duration = 3000) {
  const container = document.getElementById('notification-container') || createNotificationContainer();
  
  const notification = document.createElement('div');
  const typeClass = `notification-${type}`;
  
  notification.className = `notification ${typeClass} animate-slideIn`;
  notification.innerHTML = `
    <div class="notification-content">
      <span>${message}</span>
      <button class="notification-close" onclick="this.parentElement.parentElement.remove()">✕</button>
    </div>
  `;
  
  container.appendChild(notification);
  
  if (duration > 0) {
    setTimeout(() => notification.remove(), duration);
  }
  
  return notification;
}

/**
 * Create notification container
 * @returns {HTMLElement} - Container element
 */
function createNotificationContainer() {
  const container = document.createElement('div');
  container.id = 'notification-container';
  container.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 400px;
  `;
  document.body.appendChild(container);
  return container;
}

/**
 * Show success notification
 * @param {string} message - Message
 */
function notifySuccess(message) {
  showNotification(message, 'success', 3000);
}

/**
 * Show error notification
 * @param {string} message - Message
 */
function notifyError(message) {
  showNotification(message, 'error', 5000);
}

/**
 * Show info notification
 * @param {string} message - Message
 */
function notifyInfo(message) {
  showNotification(message, 'info', 3000);
}

// ═════════════════════════════════════════════════════════════════
// TABLE & LIST UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Create table header
 * @param {Array} columns - Column definitions [{label, key, width}]
 * @returns {string} - HTML string
 */
function createTableHeader(columns) {
  return `
    <tr>
      ${columns.map(col => `<th style="width: ${col.width || 'auto'}">${col.label}</th>`).join('')}
    </tr>
  `;
}

/**
 * Create table row
 * @param {Object} item - Item data
 * @param {Array} columns - Column definitions
 * @returns {string} - HTML string
 */
function createTableRow(item, columns) {
  return `
    <tr>
      ${columns.map(col => {
        const value = item[col.key];
        return `<td>${value || '—'}</td>`;
      }).join('')}
    </tr>
  `;
}

// ═════════════════════════════════════════════════════════════════
// VALIDATION UTILITIES
// ═════════════════════════════════════════════════════════════════

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean}
 */
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate phone format (basic)
 * @param {string} phone - Phone to validate
 * @returns {boolean}
 */
function isValidPhone(phone) {
  return /^\d{10,15}$/.test(phone.replace(/\D/g, ''));
}

/**
 * Validate form data
 * @param {Object} data - Form data
 * @param {Object} rules - Validation rules
 * @returns {Object} - Errors object
 */
function validateForm(data, rules) {
  const errors = {};
  
  for (const [field, rule] of Object.entries(rules)) {
    const value = data[field];
    
    if (rule.required && (!value || value.trim() === '')) {
      errors[field] = `${rule.label || field} é obrigatório`;
      continue;
    }
    
    if (rule.email && value && !isValidEmail(value)) {
      errors[field] = 'Email inválido';
      continue;
    }
    
    if (rule.minLength && value && value.length < rule.minLength) {
      errors[field] = `${rule.label || field} deve ter pelo menos ${rule.minLength} caracteres`;
      continue;
    }
  }
  
  return errors;
}

// ═════════════════════════════════════════════════════════════════
// EXPORT
// ═════════════════════════════════════════════════════════════════

// Ensure utilities are available globally
if (typeof window !== 'undefined') {
  window.NexusUtils = {
    // Avatar
    getInitials,
    getAvatarColor,
    createAvatar,
    createAvatarHTML,
    
    // Badges
    createTagBadge,
    createPriorityBadge,
    createStatusBadge,
    
    // Filters
    filterBySearch,
    filterByTags,
    filterByStatus,
    applyFilters,
    
    // Cards
    createContactCardHTML,
    createDealCardHTML,
    createTaskCardHTML,
    
    // Formatting
    formatCurrency,
    formatDate,
    formatDateTime,
    getTimeAgo,
    
    // Modals
    showModal,
    hideModal,
    toggleModal,
    
    // Notifications
    showNotification,
    notifySuccess,
    notifyError,
    notifyInfo,
    
    // Tables
    createTableHeader,
    createTableRow,
    
    // Validation
    isValidEmail,
    isValidPhone,
    validateForm,
    
    // Constants
    AVATAR_COLORS,
    TAG_COLORS,
    PRIORITY_COLORS,
    PIPELINE_STAGES,
  };
}
