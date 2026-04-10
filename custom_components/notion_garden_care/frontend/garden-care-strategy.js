/**
 * Garden Care - Area Care Card
 *
 * Displays an area header with bulk action buttons (Water All, Fertilize All,
 * Prune All, Harvest All) that call the notion_garden_care services for all
 * plants assigned to the given HA area.
 *
 * Inserted automatically into garden-care.yaml by the integration backend.
 * Usage:
 *   type: custom:garden-area-card
 *   area: "Garden"
 *   area_id: "abc123"
 */

class GardenAreaCard extends HTMLElement {
  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._render();
      this._rendered = true;
    }
  }

  getCardSize() { return 1; }

  _render() {
    const areaName = this._config.area || 'Area';
    const areaId   = this._config.area_id;

    const actions = [
      { label: '💧 Water All',     service: 'mark_as_watered'    },
      { label: '🌿 Fertilize All', service: 'mark_as_fertilized' },
      { label: '\u2702\ufe0f Prune All',     service: 'mark_as_pruned'     },
      { label: '🍅 Harvest All',   service: 'mark_as_harvested'  },
    ];

    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .area-header {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 8px;
          padding: 12px 16px 10px;
          background: var(--primary-color, #03a9f4);
          border-radius: var(--ha-card-border-radius, 12px);
          margin-bottom: 4px;
        }
        .area-name {
          font-size: 1.1em;
          font-weight: 600;
          color: var(--text-primary-color, #fff);
          flex: 1;
          min-width: 100px;
        }
        .action-btn {
          background: rgba(255,255,255,0.2);
          color: var(--text-primary-color, #fff);
          border: none;
          border-radius: 8px;
          padding: 6px 10px;
          font-size: 0.8em;
          cursor: pointer;
          transition: background 0.15s;
          white-space: nowrap;
        }
        .action-btn:hover  { background: rgba(255,255,255,0.35); }
        .action-btn:active { background: rgba(255,255,255,0.15); }
      </style>
      <div class="area-header">
        <span class="area-name">📍 ${areaName}</span>
        ${actions.map(a =>
          `<button class="action-btn" data-service="${a.service}">${a.label}</button>`
        ).join('')}
      </div>
    `;

    this.shadowRoot.querySelectorAll('.action-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!this._hass || !areaId) return;
        this._hass.callService('notion_garden_care', btn.dataset.service, {
          area_id: areaId,
        });
      });
    });
  }
}

if (!customElements.get('garden-area-card')) {
  customElements.define('garden-area-card', GardenAreaCard);
  console.info(
    '%c GARDEN-AREA-CARD %c Loaded ',
    'color: white; background: #4CAF50; font-weight: bold;',
    'color: #4CAF50; background: white; font-weight: bold;'
  );
}
