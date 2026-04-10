/**
 * Garden Care — frontend elements
 *
 * GardenAreaCard (custom:garden-area-card)
 *   Area section header with bulk-care action buttons.
 *
 * GardenCareRootCard (custom:garden-care-root-card)
 *   Single self-healing container card placed in garden-care.yaml.
 *   Reads all notion_garden_care plant sensors directly from hass.states,
 *   groups them by HA area, and dynamically instantiates child cards.
 *   Rebuilds layout only when the set of entities or their area assignments
 *   change — otherwise just propagates hass updates to each child card.
 *   No YAML regeneration ever required.
 */

// ─────────────────────────────────────────────────────────────────────────────
// GardenAreaCard
// ─────────────────────────────────────────────────────────────────────────────
class GardenAreaCard extends HTMLElement {
  setConfig(config) { this._config = config; }
  getCardSize() { return 1; }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) { this._render(); this._rendered = true; }
  }

  _render() {
    const areaName = this._config.area || 'Area';
    const areaId   = this._config.area_id;

    const actions = [
      { label: '💧 Water All',     service: 'mark_as_watered'    },
      { label: '🌿 Fertilize All', service: 'mark_as_fertilized' },
      { label: '✂️ Prune All',     service: 'mark_as_pruned'     },
      { label: '🍅 Harvest All',   service: 'mark_as_harvested'  },
    ];

    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        .area-header {
          display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
          padding: 12px 16px 10px;
          background: var(--primary-color, #03a9f4);
          border-radius: var(--ha-card-border-radius, 12px);
          margin-bottom: 4px;
        }
        .area-name {
          font-size: 1.1em; font-weight: 600;
          color: var(--text-primary-color, #fff);
          flex: 1; min-width: 100px;
        }
        .action-btn {
          background: rgba(255,255,255,0.2); color: var(--text-primary-color, #fff);
          border: none; border-radius: 8px; padding: 6px 10px; font-size: 0.8em;
          cursor: pointer; transition: background 0.15s; white-space: nowrap;
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
        this._hass.callService('notion_garden_care', btn.dataset.service, { area_id: areaId });
      });
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// GardenCareRootCard
// ─────────────────────────────────────────────────────────────────────────────
class GardenCareRootCard extends HTMLElement {
  constructor() {
    super();
    this._hass      = null;
    this._layoutKey = null;
    this._childCards = [];
    this._buildId   = 0;
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = '<style>:host{display:block}</style>';
  }

  setConfig(config) { this._config = config || {}; }
  getCardSize() { return 1; }

  set hass(hass) {
    this._hass = hass;
    const key = this._getLayoutKey(hass);
    if (key !== this._layoutKey) {
      this._layoutKey = key;
      this._buildLayout();
    } else {
      for (const card of this._childCards) card.hass = hass;
    }
  }

  /** A string that changes whenever the set of plants or their area assignments change. */
  _getLayoutKey(hass) {
    const SKIP = ['plants_to_', 'active_plants', '_database'];
    return Object.entries(hass.states || {})
      .filter(([id, s]) =>
        id.startsWith('sensor.') &&
        s.attributes?.page_id &&
        !SKIP.some(f => id.includes(f))
      )
      .map(([id]) => `${id}:${hass.entities?.[id]?.area_id ?? ''}`)
      .sort()
      .join('|');
  }

  async _buildLayout() {
    const buildId = ++this._buildId;

    // Wait for sibling custom elements (resolves immediately if already defined)
    await Promise.all([
      customElements.whenDefined('add-plant-card'),
      customElements.whenDefined('plant-care-card'),
      customElements.whenDefined('garden-area-card'),
    ]);

    // A newer build was triggered while we were waiting — bail
    if (buildId !== this._buildId) return;

    const hass = this._hass;
    const root = this.shadowRoot;
    root.innerHTML = '<style>:host{display:block}</style>';
    this._childCards = [];

    const frag = document.createDocumentFragment();

    // ── Add Plant card ────────────────────────────────────────────────────
    const addCard = document.createElement('add-plant-card');
    addCard.setConfig({});
    addCard.hass = hass;
    frag.appendChild(addCard);
    this._childCards.push(addCard);

    // ── Collect plant entities ────────────────────────────────────────────
    const SKIP = ['plants_to_', 'active_plants', '_database'];
    const plants = Object.entries(hass.states || {})
      .filter(([id, s]) =>
        id.startsWith('sensor.') &&
        s.attributes?.page_id &&
        !SKIP.some(f => id.includes(f))
      )
      .map(([id]) => {
        const areaId = hass.entities?.[id]?.area_id ?? null;
        return {
          entityId: id,
          areaId,
          areaName: areaId ? (hass.areas?.[areaId]?.name ?? areaId) : null,
        };
      })
      .sort((a, b) => a.entityId.localeCompare(b.entityId));

    if (plants.length === 0) {
      const card = document.createElement('ha-card');
      card.innerHTML = `<div style="padding:20px;text-align:center;color:var(--secondary-text-color)">
        <p>No plants found. Use the form above to add your first plant.</p></div>`;
      frag.appendChild(card);
      root.appendChild(frag);
      return;
    }

    // ── Group by area ─────────────────────────────────────────────────────
    const areas  = {}; // areaName → { areaId, plants[] }
    const noArea = [];

    for (const p of plants) {
      if (p.areaId && p.areaName) {
        if (!areas[p.areaName]) areas[p.areaName] = { areaId: p.areaId, plants: [] };
        areas[p.areaName].plants.push(p);
      } else {
        noArea.push(p);
      }
    }

    // ── Render area groups ────────────────────────────────────────────────
    const _addPlantCard = (entityId) => {
      const card = document.createElement('plant-care-card');
      card.setConfig({ entity: entityId });
      card.hass = hass;
      frag.appendChild(card);
      this._childCards.push(card);
    };

    for (const areaName of Object.keys(areas).sort()) {
      const group = areas[areaName];

      const areaCard = document.createElement('garden-area-card');
      areaCard.setConfig({ area: areaName, area_id: group.areaId });
      areaCard.hass = hass;
      frag.appendChild(areaCard);
      this._childCards.push(areaCard);

      for (const p of group.plants) _addPlantCard(p.entityId);
    }

    // ── Plants with no area ───────────────────────────────────────────────
    for (const p of noArea) _addPlantCard(p.entityId);

    root.appendChild(frag);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Register
// ─────────────────────────────────────────────────────────────────────────────
if (!customElements.get('garden-area-card')) {
  customElements.define('garden-area-card', GardenAreaCard);
}
if (!customElements.get('garden-care-root-card')) {
  customElements.define('garden-care-root-card', GardenCareRootCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.find(c => c.type === 'garden-care-root-card')) {
  window.customCards.push({
    type: 'garden-care-root-card',
    name: 'Garden Care Dashboard',
    description: 'Auto-discovering garden care dashboard — plants grouped by HA area',
    preview: false,
    documentationURL: 'https://github.com/pfalzcraft/notion-garden-care',
  });
}

console.info('%c GARDEN-AREA-CARD %c Loaded ',
  'color: white; background: #4CAF50; font-weight: bold;',
  'color: #4CAF50; background: white; font-weight: bold;'
);
console.info('%c GARDEN-CARE-ROOT-CARD %c Loaded ',
  'color: white; background: #2e7d32; font-weight: bold;',
  'color: #2e7d32; background: white; font-weight: bold;'
);
