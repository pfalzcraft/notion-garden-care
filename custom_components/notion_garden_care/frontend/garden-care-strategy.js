/**
 * Garden Care Dashboard Strategy
 *
 * Auto-generates a Lovelace dashboard with plant care cards grouped by
 * Home Assistant area. Plants not assigned to any area appear at the bottom
 * under an "Other" section without an area header.
 *
 * Usage in dashboard YAML:
 *   strategy:
 *     type: custom:garden-care
 */

// ── Area Care Card ────────────────────────────────────────────────────────────

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
      { label: '✂️ Prune All',     service: 'mark_as_pruned'     },
      { label: '🍅 Harvest All',   service: 'mark_as_harvested'  },
    ];

    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
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
        .action-btn:hover {
          background: rgba(255,255,255,0.35);
        }
        .action-btn:active {
          background: rgba(255,255,255,0.15);
        }
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
          area_id: areaId
        });
      });
    });
  }
}

if (!customElements.get('garden-area-card')) {
  customElements.define('garden-area-card', GardenAreaCard);
}

// ── Dashboard Strategy ────────────────────────────────────────────────────────

class GardenCareDashboardStrategy {
  /**
   * Generate the complete dashboard configuration, plants grouped by HA area.
   */
  static async generateDashboard(info) {
    const hass = info.hass || info;

    // Find all individual plant sensors (exclude aggregate sensors)
    const plantEntities = Object.keys(hass.states || {})
      .filter(entityId =>
        entityId.startsWith('sensor.garden_care_') &&
        !entityId.includes('plants_to_') &&
        !entityId.includes('active_plants') &&
        !entityId.includes('database')
      )
      .sort();

    // Group by HA area using hass.entities (entity registry) and hass.areas
    // { areaName: { area_id: string|null, entities: string[] } }
    const groups = {};

    for (const entityId of plantEntities) {
      const entityEntry = (hass.entities || {})[entityId];
      const areaId      = entityEntry?.area_id || null;
      const areaName    = areaId
        ? ((hass.areas || {})[areaId]?.name || areaId)
        : null;
      const key = areaName || '__none__';

      if (!groups[key]) {
        groups[key] = { area_id: areaId, area_name: areaName, entities: [] };
      }
      groups[key].entities.push(entityId);
    }

    // Build cards
    const cards = [];

    // Add Plant form always at the top
    cards.push({ type: 'custom:add-plant-card' });

    if (plantEntities.length === 0) {
      cards.push({
        type: 'markdown',
        content: '### No plants found\nAdd plants using the form above or directly in your Notion database.'
      });
    } else {
      // Named areas first (sorted), then ungrouped plants
      const namedKeys   = Object.keys(groups).filter(k => k !== '__none__').sort();
      const orderedKeys = [...namedKeys, ...(groups['__none__'] ? ['__none__'] : [])];

      for (const key of orderedKeys) {
        const group = groups[key];

        // Area header with bulk action buttons (only for named areas)
        if (group.area_id) {
          cards.push({
            type: 'custom:garden-area-card',
            area:    group.area_name,
            area_id: group.area_id,
          });
        }

        for (const entityId of group.entities) {
          cards.push({ type: 'custom:plant-care-card', entity: entityId });
        }
      }
    }

    return {
      title: 'Garden Care',
      views: [
        {
          title: 'Plants',
          path: 'plants',
          icon: 'mdi:flower',
          cards: cards,
        }
      ]
    };
  }
}

// Register the dashboard strategy (only if not already registered)
if (!customElements.get('ll-strategy-dashboard-garden-care')) {
  customElements.define(
    'll-strategy-dashboard-garden-care',
    class extends HTMLElement {
      static async generate(config, hass) {
        return await GardenCareDashboardStrategy.generateDashboard({ config, hass });
      }
    }
  );
  console.info('%c GARDEN-CARE-STRATEGY %c Loaded ',
    'color: white; background: #4CAF50; font-weight: bold;',
    'color: #4CAF50; background: white; font-weight: bold;'
  );
} else {
  console.info('%c GARDEN-CARE-STRATEGY %c Already registered ',
    'color: white; background: #FF9800; font-weight: bold;',
    'color: #FF9800; background: white; font-weight: bold;'
  );
}
