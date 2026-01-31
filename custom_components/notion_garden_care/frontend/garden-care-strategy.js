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

    // Generate views
    const views = [
      await this.generatePlantsView(info, plantEntities),
      await this.generateOverviewView(info),
    ];

    return {
      title: 'Garden Care',
      views: views
    };
  }

  /**
   * Generate the Plants view with individual plant cards
   */
  static async generatePlantsView(info, plantEntities) {
    const cards = [];

    // Add the "Add Plant" form card at the top
    cards.push({
      type: 'custom:add-plant-card'
    });

    // Add a plant card for each plant - no grid, let masonry layout handle it
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
        content: '*No plants found. Add plants to your Notion database to see them here.*'
      });
    }

    return {
      title: 'Plants',
      path: 'plants',
      icon: 'mdi:flower',
      cards: cards
    };
  }

  /**
   * Generate the Overview view with summary cards
   */
  static async generateOverviewView(info) {
    return {
      title: 'Overview',
      path: 'overview',
      icon: 'mdi:view-dashboard',
      cards: [
        {
          type: 'markdown',
          content: '# Garden Overview\nQuick summary of your garden care tasks.'
        },
        {
          type: 'glance',
          title: 'Garden Statistics',
          entities: [
            {
              entity: 'sensor.active_plants_count',
              name: 'Active Plants',
              icon: 'mdi:flower'
            },
            {
              entity: 'sensor.plants_to_water',
              name: 'Need Water',
              icon: 'mdi:watering-can'
            },
            {
              entity: 'sensor.plants_to_fertilize',
              name: 'Need Fertilizer',
              icon: 'mdi:spray-bottle'
            },
            {
              entity: 'sensor.plants_to_prune',
              name: 'Need Pruning',
              icon: 'mdi:content-cut'
            }
          ]
        },
        {
          type: 'vertical-stack',
          title: 'Watering Tasks',
          cards: [
            {
              type: 'entity',
              entity: 'sensor.plants_to_water',
              name: 'Plants to Water Today',
              icon: 'mdi:watering-can'
            },
            {
              type: 'conditional',
              conditions: [
                {
                  entity: 'sensor.plants_to_water',
                  state_not: '0'
                }
              ],
              card: {
                type: 'markdown',
                content: "{% set plants = state_attr('sensor.plants_to_water', 'plants') %}{% if plants %}**Plants needing water:**\n{% for plant in plants %}- {{ plant }}\n{% endfor %}{% endif %}"
              }
            }
          ]
        },
        {
          type: 'vertical-stack',
          title: 'Fertilizing Tasks',
          cards: [
            {
              type: 'entity',
              entity: 'sensor.plants_to_fertilize',
              name: 'Plants to Fertilize Today',
              icon: 'mdi:spray-bottle'
            },
            {
              type: 'conditional',
              conditions: [
                {
                  entity: 'sensor.plants_to_fertilize',
                  state_not: '0'
                }
              ],
              card: {
                type: 'markdown',
                content: "{% set plants = state_attr('sensor.plants_to_fertilize', 'plants') %}{% if plants %}**Plants needing fertilizer:**\n{% for plant in plants %}- {{ plant }}\n{% endfor %}{% endif %}"
              }
            }
          ]
        },
        {
          type: 'vertical-stack',
          title: 'Pruning Tasks',
          cards: [
            {
              type: 'entity',
              entity: 'sensor.plants_to_prune',
              name: 'Plants to Prune This Month',
              icon: 'mdi:content-cut'
            },
            {
              type: 'conditional',
              conditions: [
                {
                  entity: 'sensor.plants_to_prune',
                  state_not: '0'
                }
              ],
              card: {
                type: 'markdown',
                content: "{% set plants = state_attr('sensor.plants_to_prune', 'plants') %}{% if plants %}**Plants to prune this month:**\n{% for plant in plants %}- {{ plant }}\n{% endfor %}{% endif %}"
              }
            }
          ]
        }
      ]
    };
  }
}

// Register the dashboard strategy
// When user specifies: strategy: { type: custom:garden-care }
// HA looks for: ll-strategy-dashboard-garden-care
customElements.define(
  'll-strategy-dashboard-garden-care',
  class extends HTMLElement {
    static async generate(config, hass) {
      // HA passes (config, hass) not (info)
      return await GardenCareDashboardStrategy.generateDashboard({ config, hass });
    }
  }
);

console.info('%c GARDEN-CARE-STRATEGY %c Loaded ',
  'color: white; background: #2196F3; font-weight: bold;',
  'color: #2196F3; background: white; font-weight: bold;'
);
