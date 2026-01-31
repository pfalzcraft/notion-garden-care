/**
 * Garden Care Dashboard Strategy
 *
 * Auto-generates a Lovelace dashboard with plant care cards
 * for all plants from the Notion Garden Care integration.
 *
 * Usage in dashboard YAML:
 *   strategy:
 *     type: custom:garden-care
 */

class GardenCareDashboardStrategy {
  /**
   * Generate the complete dashboard configuration
   */
  static async generateDashboard(info) {
    const hass = info.hass || info;

    // Find all garden care plant sensors
    const plantEntities = Object.keys(hass.states || {})
      .filter(entityId =>
        entityId.startsWith('sensor.garden_care_') &&
        !entityId.includes('plants_to_') &&
        !entityId.includes('active_plants') &&
        !entityId.includes('database')
      )
      .sort();

    // Build cards array
    const cards = [];

    // Add the "Add Plant" form card at the top
    cards.push({
      type: 'custom:add-plant-card'
    });

    // Add a plant card for each plant
    if (plantEntities.length > 0) {
      for (const entityId of plantEntities) {
        cards.push({
          type: 'custom:plant-care-card',
          entity: entityId
        });
      }
    } else {
      cards.push({
        type: 'markdown',
        content: '### No plants found\nAdd plants using the form above or directly in your Notion database.'
      });
    }

    return {
      title: 'Garden Care',
      views: [
        {
          title: 'Plants',
          path: 'plants',
          icon: 'mdi:flower',
          cards: cards
        }
      ]
    };
  }
}

// Register the dashboard strategy
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
