/**
 * Plant Care Card - Custom Lovelace Card for Notion Garden Care
 *
 * Displays individual plant information with care schedule and action buttons.
 */

class PlantCareCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }
    this._config = config;
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement('plant-care-card-editor');
  }

  static getStubConfig(hass) {
    // Find a garden care entity for the stub config
    const entities = Object.keys(hass.states).filter(e =>
      e.startsWith('sensor.garden_care_') &&
      !e.includes('plants_to_') &&
      !e.includes('active_plants') &&
      !e.includes('database')
    );
    return { entity: entities[0] || '' };
  }

  /**
   * Get icon based on plant type
   */
  getPlantIcon(type) {
    const icons = {
      'Tree': 'mdi:tree',
      'Shrub': 'mdi:tree',
      'Vegetable': 'mdi:carrot',
      'Herb': 'mdi:leaf',
      'Lawn': 'mdi:grass',
      'Plant': 'mdi:flower',
      'Flower': 'mdi:flower',
    };
    return icons[type] || 'mdi:flower';
  }

  /**
   * Calculate days difference from today
   */
  getDaysDiff(dateStr) {
    if (!dateStr) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const targetDate = new Date(dateStr);
    targetDate.setHours(0, 0, 0, 0);
    const diffTime = targetDate - today;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  /**
   * Format the due date with status indicator
   */
  formatDueDate(dateStr, label) {
    if (!dateStr) return { text: '-', class: 'neutral' };

    const days = this.getDaysDiff(dateStr);
    const date = new Date(dateStr);
    const dateFormatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

    if (days < 0) {
      return {
        text: `${dateFormatted} (${Math.abs(days)}d overdue)`,
        class: 'overdue'
      };
    } else if (days === 0) {
      return { text: `${dateFormatted} (today!)`, class: 'due-today' };
    } else if (days === 1) {
      return { text: `${dateFormatted} (tomorrow)`, class: 'due-soon' };
    } else if (days <= 3) {
      return { text: `${dateFormatted} (${days}d)`, class: 'due-soon' };
    } else {
      return { text: `${dateFormatted} (${days}d)`, class: 'neutral' };
    }
  }

  /**
   * Format months list with current month highlighted
   */
  formatMonths(monthsArray) {
    if (!monthsArray || !Array.isArray(monthsArray) || monthsArray.length === 0) {
      return { html: '-', hasCurrentMonth: false };
    }

    const currentMonth = new Date().toLocaleString('en-US', { month: 'long' });
    const shortCurrentMonth = new Date().toLocaleString('en-US', { month: 'short' });

    let hasCurrentMonth = false;
    const formatted = monthsArray.map(month => {
      const monthLower = month.toLowerCase();
      const currentLower = currentMonth.toLowerCase();
      const shortLower = shortCurrentMonth.toLowerCase();

      if (monthLower === currentLower || monthLower === shortLower ||
          currentLower.startsWith(monthLower) || monthLower.startsWith(shortLower)) {
        hasCurrentMonth = true;
        return `<span class="current-month">${month}</span>`;
      }
      return month;
    });

    return { html: formatted.join(', '), hasCurrentMonth };
  }

  /**
   * Call a service to mark a task as done
   */
  callService(service, entityId) {
    this._hass.callService('notion_garden_care', service, {
      entity_id: entityId
    });
  }

  /**
   * Format all attributes as table rows
   */
  formatAttributes(attrs) {
    const skipKeys = ['friendly_name', 'icon'];
    const rows = [];

    for (const [key, value] of Object.entries(attrs)) {
      if (skipKeys.includes(key)) continue;

      const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      let displayValue = value;

      if (Array.isArray(value)) {
        displayValue = value.join(', ');
      } else if (typeof value === 'boolean') {
        displayValue = value ? 'Yes' : 'No';
      } else if (value === null || value === undefined) {
        displayValue = '-';
      }

      rows.push(`<tr><td>${label}</td><td>${displayValue}</td></tr>`);
    }

    return rows.join('');
  }

  render() {
    if (!this._hass || !this._config) return;

    const entityId = this._config.entity;
    const state = this._hass.states[entityId];

    if (!state) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content" style="padding: 16px;">
            <p>Entity not found: ${entityId}</p>
          </div>
        </ha-card>
      `;
      return;
    }

    const attrs = state.attributes;
    const plantName = attrs.plant_name || attrs.name || state.entity_id;
    const plantType = attrs.type || 'Plant';
    const location = attrs.location || '';
    const isLawn = plantType === 'Lawn';

    // Get care schedule data
    const nextWater = this.formatDueDate(attrs.next_water, 'Water');
    const nextFertilize = this.formatDueDate(attrs.next_fertilize, 'Fertilize');
    const pruneMonths = this.formatMonths(attrs.prune_months);
    const harvestMonths = this.formatMonths(attrs.harvest_months);
    const nextAeration = isLawn ? this.formatDueDate(attrs.next_aeration, 'Aeration') : null;
    const nextSanding = isLawn ? this.formatDueDate(attrs.next_sanding, 'Sanding') : null;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 16px;
          box-sizing: border-box;
        }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .plant-icon {
          --mdc-icon-size: 32px;
          color: var(--primary-color);
        }
        .plant-name {
          font-size: 1.2em;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .location-badge {
          background: var(--secondary-background-color, #f5f5f5);
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 0.85em;
          color: var(--secondary-text-color);
        }
        .care-schedule {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 16px;
        }
        .care-row {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px;
          border-radius: 8px;
          background: var(--secondary-background-color, #f9f9f9);
        }
        .care-icon {
          font-size: 1.2em;
          width: 28px;
          text-align: center;
        }
        .care-label {
          width: 80px;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .care-value {
          flex: 1;
          color: var(--secondary-text-color);
        }
        .care-value.overdue {
          color: var(--error-color, #db4437);
          font-weight: 500;
        }
        .care-value.due-today {
          color: var(--warning-color, #ff9800);
          font-weight: 500;
        }
        .care-value.due-soon {
          color: var(--warning-color, #ff9800);
        }
        .current-month {
          background: var(--primary-color);
          color: var(--text-primary-color, white);
          padding: 2px 6px;
          border-radius: 4px;
          font-weight: 500;
        }
        .actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          padding-top: 12px;
          border-top: 1px solid var(--divider-color, #e0e0e0);
        }
        .action-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 8px 12px;
          border: none;
          border-radius: 8px;
          background: var(--primary-color);
          color: var(--text-primary-color, white);
          cursor: pointer;
          font-size: 0.9em;
          transition: opacity 0.2s;
        }
        .action-btn:hover {
          opacity: 0.85;
        }
        .action-btn:active {
          opacity: 0.7;
        }
        .info-icon {
          cursor: pointer;
          color: var(--secondary-text-color);
          --mdc-icon-size: 24px;
          transition: color 0.2s;
        }
        .info-icon:hover {
          color: var(--primary-color);
        }
        .popup-overlay {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.5);
          z-index: 999;
          justify-content: center;
          align-items: center;
        }
        .popup-overlay.open {
          display: flex;
        }
        .popup-content {
          background: var(--card-background-color, white);
          border-radius: 12px;
          padding: 20px;
          max-width: 500px;
          max-height: 80vh;
          overflow-y: auto;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
          position: relative;
        }
        .popup-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        .popup-title {
          font-size: 1.2em;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .popup-close {
          cursor: pointer;
          color: var(--secondary-text-color);
          --mdc-icon-size: 24px;
        }
        .popup-close:hover {
          color: var(--primary-color);
        }
        .popup-table {
          width: 100%;
          border-collapse: collapse;
        }
        .popup-table td {
          padding: 6px 8px;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
          vertical-align: top;
        }
        .popup-table td:first-child {
          font-weight: 500;
          color: var(--primary-text-color);
          white-space: nowrap;
          width: 40%;
        }
        .popup-table td:last-child {
          color: var(--secondary-text-color);
          word-break: break-word;
        }
        .popup-table tr:last-child td {
          border-bottom: none;
        }
      </style>

      <ha-card>
        <div class="header">
          <div class="header-left">
            <ha-icon class="plant-icon" icon="${this.getPlantIcon(plantType)}"></ha-icon>
            <span class="plant-name">${plantName}</span>
          </div>
          ${location ? `<span class="location-badge">${location}</span>` : ''}
          <ha-icon class="info-icon" icon="mdi:information-outline" id="info-toggle" title="Show all attributes"></ha-icon>
        </div>

        <div class="care-schedule">
          <div class="care-row">
            <span class="care-icon">💧</span>
            <span class="care-label">Water</span>
            <span class="care-value ${nextWater.class}">${nextWater.text}</span>
          </div>
          <div class="care-row">
            <span class="care-icon">🧪</span>
            <span class="care-label">Fertilize</span>
            <span class="care-value ${nextFertilize.class}">${nextFertilize.text}</span>
          </div>
          <div class="care-row">
            <span class="care-icon">✂️</span>
            <span class="care-label">Prune</span>
            <span class="care-value ${pruneMonths.hasCurrentMonth ? 'due-today' : ''}">${pruneMonths.html}</span>
          </div>
          <div class="care-row">
            <span class="care-icon">🍎</span>
            <span class="care-label">Harvest</span>
            <span class="care-value ${harvestMonths.hasCurrentMonth ? 'due-today' : ''}">${harvestMonths.html}</span>
          </div>
          ${isLawn ? `
          <div class="care-row">
            <span class="care-icon">🌱</span>
            <span class="care-label">Aeration</span>
            <span class="care-value ${nextAeration.class}">${nextAeration.text}</span>
          </div>
          <div class="care-row">
            <span class="care-icon">🏖️</span>
            <span class="care-label">Sanding</span>
            <span class="care-value ${nextSanding.class}">${nextSanding.text}</span>
          </div>
          ` : ''}
        </div>

        <div class="actions">
          <button class="action-btn" id="btn-water">
            💧 Watered
          </button>
          <button class="action-btn" id="btn-fertilize">
            🧪 Fertilized
          </button>
          <button class="action-btn" id="btn-prune">
            ✂️ Pruned
          </button>
          ${isLawn ? `
          <button class="action-btn" id="btn-aerate">
            🌱 Aerated
          </button>
          <button class="action-btn" id="btn-sand">
            🏖️ Sanded
          </button>
          ` : ''}
        </div>

      </ha-card>

      <div class="popup-overlay" id="popup-overlay">
        <div class="popup-content">
          <div class="popup-header">
            <span class="popup-title">${plantName} - Details</span>
            <ha-icon class="popup-close" icon="mdi:close" id="popup-close"></ha-icon>
          </div>
          <table class="popup-table">
            ${this.formatAttributes(attrs)}
          </table>
        </div>
      </div>
    `;

    // Add event listener for info popup
    const overlay = this.shadowRoot.getElementById('popup-overlay');
    let popupJustOpened = false;

    this.shadowRoot.getElementById('info-toggle')?.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      popupJustOpened = true;
      overlay?.classList.add('open');
      // Reset flag after a short delay to prevent immediate close on mobile
      setTimeout(() => { popupJustOpened = false; }, 300);
    });
    this.shadowRoot.getElementById('popup-close')?.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      overlay?.classList.remove('open');
    });
    overlay?.addEventListener('click', (e) => {
      // Only close if clicking on overlay (not content) and popup wasn't just opened
      if (e.target === overlay && !popupJustOpened) {
        overlay.classList.remove('open');
      }
    });

    // Add event listeners for buttons
    const entityIdForService = entityId;
    this.shadowRoot.getElementById('btn-water')?.addEventListener('click', () => {
      this.callService('mark_as_watered', entityIdForService);
    });
    this.shadowRoot.getElementById('btn-fertilize')?.addEventListener('click', () => {
      this.callService('mark_as_fertilized', entityIdForService);
    });
    this.shadowRoot.getElementById('btn-prune')?.addEventListener('click', () => {
      this.callService('mark_as_pruned', entityIdForService);
    });
    this.shadowRoot.getElementById('btn-aerate')?.addEventListener('click', () => {
      this.callService('mark_as_aerated', entityIdForService);
    });
    this.shadowRoot.getElementById('btn-sand')?.addEventListener('click', () => {
      this.callService('mark_as_sanded', entityIdForService);
    });
  }
}

/**
 * Card Editor - Provides UI for configuring the card
 */
class PlantCareCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  setConfig(config) {
    this._config = config;
  }

  configChanged(newConfig) {
    const event = new Event('config-changed', {
      bubbles: true,
      composed: true
    });
    event.detail = { config: newConfig };
    this.dispatchEvent(event);
  }

  render() {
    if (!this._hass) return;

    // Get all garden care plant entities
    const entities = Object.keys(this._hass.states)
      .filter(entityId =>
        entityId.startsWith('sensor.garden_care_') &&
        !entityId.includes('plants_to_') &&
        !entityId.includes('active_plants') &&
        !entityId.includes('database')
      )
      .sort();

    const selectedEntity = this._config?.entity || '';

    this.shadowRoot.innerHTML = `
      <style>
        .editor {
          padding: 16px;
        }
        .row {
          margin-bottom: 16px;
        }
        label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
        }
        select {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 4px;
          background: var(--card-background-color, white);
          color: var(--primary-text-color);
          font-size: 14px;
        }
        .hint {
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-top: 4px;
        }
      </style>
      <div class="editor">
        <div class="row">
          <label for="entity">Plant Entity</label>
          <select id="entity">
            <option value="">Select a plant...</option>
            ${entities.map(e => {
              const state = this._hass.states[e];
              const name = state?.attributes?.plant_name || state?.attributes?.friendly_name || e;
              return `<option value="${e}" ${e === selectedEntity ? 'selected' : ''}>${name}</option>`;
            }).join('')}
          </select>
          <div class="hint">Select a plant from your Notion Garden Care database</div>
        </div>
      </div>
    `;

    // Add event listener for entity selection
    this.shadowRoot.getElementById('entity').addEventListener('change', (e) => {
      this.configChanged({
        ...this._config,
        entity: e.target.value
      });
    });
  }
}

/**
 * Add Plant Card - Form to add new plants using AI
 */
class AddPlantCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._loading = false;
    this._message = null;
    this._messageType = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this.render();
      this._initialized = true;
    }
  }

  setConfig(config) {
    this._config = config;
  }

  getCardSize() {
    return 2;
  }

  static getConfigElement() {
    return document.createElement('add-plant-card-editor');
  }

  static getStubConfig() {
    return {};
  }

  /**
   * Check if plant already exists
   */
  plantExists(plantName) {
    if (!this._hass || !plantName) return false;

    const normalizedInput = plantName.toLowerCase().trim();

    // Check all garden care entities
    for (const entityId of Object.keys(this._hass.states)) {
      if (entityId.startsWith('sensor.garden_care_') &&
          !entityId.includes('plants_to_') &&
          !entityId.includes('active_plants') &&
          !entityId.includes('database')) {
        const state = this._hass.states[entityId];
        const existingName = state.attributes.plant_name || state.attributes.name || '';
        if (existingName.toLowerCase().trim() === normalizedInput) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Handle add plant button click
   */
  async addPlant() {
    const input = this.shadowRoot.getElementById('plant-name-input');
    const plantName = input?.value?.trim();

    if (!plantName) {
      this.showMessage('Please enter a plant name', 'error');
      return;
    }

    // Check for duplicates
    if (this.plantExists(plantName)) {
      this.showMessage(`"${plantName}" already exists in your garden`, 'error');
      return;
    }

    // Show loading state
    this._loading = true;
    this.updateUI();

    try {
      await this._hass.callService('notion_garden_care', 'add_plant', {
        plant_name: plantName
      });

      this.showMessage(`Adding "${plantName}"... This may take a moment.`, 'success');
      input.value = '';

    } catch (err) {
      console.error('Failed to add plant:', err);
      this.showMessage(`Failed to add plant: ${err.message}`, 'error');
    } finally {
      this._loading = false;
      this.updateUI();
    }
  }

  showMessage(text, type) {
    this._message = text;
    this._messageType = type;
    this.updateUI();

    // Clear message after 5 seconds
    setTimeout(() => {
      this._message = null;
      this._messageType = null;
      this.updateUI();
    }, 5000);
  }

  updateUI() {
    const messageEl = this.shadowRoot.getElementById('message');
    const buttonEl = this.shadowRoot.getElementById('add-btn');
    const spinnerEl = this.shadowRoot.getElementById('spinner');

    if (messageEl) {
      messageEl.textContent = this._message || '';
      messageEl.className = `message ${this._messageType || ''}`;
      messageEl.style.display = this._message ? 'block' : 'none';
    }

    if (buttonEl) {
      buttonEl.disabled = this._loading;
      buttonEl.textContent = this._loading ? 'Adding...' : 'Add Plant';
    }

    if (spinnerEl) {
      spinnerEl.style.display = this._loading ? 'inline-block' : 'none';
    }
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 16px;
          box-sizing: border-box;
        }
        .header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        .header-icon {
          --mdc-icon-size: 32px;
          color: var(--primary-color);
        }
        .header-title {
          font-size: 1.2em;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .form-row {
          display: flex;
          gap: 12px;
          align-items: center;
        }
        .input-wrapper {
          flex: 1;
        }
        input[type="text"] {
          width: 100%;
          padding: 12px;
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 8px;
          font-size: 1em;
          background: var(--card-background-color, white);
          color: var(--primary-text-color);
          box-sizing: border-box;
        }
        input[type="text"]:focus {
          outline: none;
          border-color: var(--primary-color);
          box-shadow: 0 0 0 2px rgba(var(--rgb-primary-color, 33, 150, 243), 0.2);
        }
        input[type="text"]::placeholder {
          color: var(--secondary-text-color);
          opacity: 0.7;
        }
        .add-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          background: var(--primary-color);
          color: var(--text-primary-color, white);
          cursor: pointer;
          font-size: 1em;
          font-weight: 500;
          transition: opacity 0.2s, background 0.2s;
          white-space: nowrap;
        }
        .add-btn:hover:not(:disabled) {
          opacity: 0.9;
        }
        .add-btn:active:not(:disabled) {
          opacity: 0.8;
        }
        .add-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .spinner {
          display: none;
          width: 16px;
          height: 16px;
          border: 2px solid transparent;
          border-top-color: currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .message {
          display: none;
          margin-top: 12px;
          padding: 10px 12px;
          border-radius: 8px;
          font-size: 0.9em;
        }
        .message.success {
          background: rgba(76, 175, 80, 0.15);
          color: #2e7d32;
          border: 1px solid rgba(76, 175, 80, 0.3);
        }
        .message.error {
          background: rgba(244, 67, 54, 0.15);
          color: #c62828;
          border: 1px solid rgba(244, 67, 54, 0.3);
        }
        .hint {
          margin-top: 12px;
          font-size: 0.85em;
          color: var(--secondary-text-color);
        }
      </style>

      <ha-card>
        <div class="header">
          <ha-icon class="header-icon" icon="mdi:plus-circle"></ha-icon>
          <span class="header-title">Add New Plant</span>
        </div>

        <div class="form-row">
          <div class="input-wrapper">
            <input
              type="text"
              id="plant-name-input"
              placeholder="Enter plant name (e.g., Lavender, Tomato, Oak Tree)"
            />
          </div>
          <button class="add-btn" id="add-btn">
            <span class="spinner" id="spinner"></span>
            Add Plant
          </button>
        </div>

        <div class="message" id="message"></div>

        <div class="hint">
          AI will automatically fill in care instructions, watering schedule, and more.
        </div>
      </ha-card>
    `;

    // Add event listeners
    this.shadowRoot.getElementById('add-btn')?.addEventListener('click', () => {
      this.addPlant();
    });

    // Allow Enter key to submit
    this.shadowRoot.getElementById('plant-name-input')?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.addPlant();
      }
    });
  }
}

/**
 * Add Plant Card Editor
 */
class AddPlantCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    this._config = config;
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        .editor {
          padding: 16px;
        }
        .note {
          color: var(--secondary-text-color);
          font-size: 14px;
        }
      </style>
      <div class="editor">
        <p class="note">This card provides a form to add new plants using AI. No configuration required.</p>
      </div>
    `;
  }

  connectedCallback() {
    this.render();
  }
}

// Register the cards and editors
customElements.define('plant-care-card', PlantCareCard);
customElements.define('plant-care-card-editor', PlantCareCardEditor);
customElements.define('add-plant-card', AddPlantCard);
customElements.define('add-plant-card-editor', AddPlantCardEditor);

// Register for card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'plant-care-card',
  name: 'Plant Care Card',
  description: 'Display plant care information from Notion Garden Care',
  preview: true,
  documentationURL: 'https://github.com/pfalzcraft/notion-garden-care'
});
window.customCards.push({
  type: 'add-plant-card',
  name: 'Add Plant Card',
  description: 'Form to add new plants with AI-powered care info',
  preview: false,
  documentationURL: 'https://github.com/pfalzcraft/notion-garden-care'
});

console.info('%c PLANT-CARE-CARD %c Loaded ',
  'color: white; background: #4CAF50; font-weight: bold;',
  'color: #4CAF50; background: white; font-weight: bold;'
);
console.info('%c ADD-PLANT-CARD %c Loaded ',
  'color: white; background: #2196F3; font-weight: bold;',
  'color: #2196F3; background: white; font-weight: bold;'
);
