[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/pfalzcraft)

# 🌱 Notion Garden Care for Home Assistant

Manage your garden with Notion and automate reminders with Home Assistant. Track watering, fertilizing, and pruning schedules for all your plants in one place.

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=homeassistant)
![Notion](https://img.shields.io/badge/Notion-Database-000000?logo=notion)
![License](https://img.shields.io/badge/License-MIT-green)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/pfalzcraft)

## ✨ Features

- 🌿 **Automatic Setup** - No coding required, everything happens in the Home Assistant UI
- 🗄️ **Auto-Create Database** - Integration creates the Notion database for you
- 📅 **Smart Reminders** - Never forget to water, fertilize, or prune
- 📊 **Self-Healing Dashboard** - Auto-created on install; discovers plants at runtime, always up to date
- 📍 **Area-Based Bulk Care** - Group plants by HA area and water/fertilize/prune an entire area at once
- 🖼️ **Area Background Images** - Area section headers use your HA area picture automatically
- 🏗️ **Responsive Grid Layout** - Plants arranged in a multi-column grid, one column per area
- 🖱️ **Clickable Plant Cards** - Click the plant name to open the HA more-info dialog
- ➕ **Add Plant Form** - Add new plants from the dashboard; entities refresh automatically
- 🤖 **AI-Powered Plant Addition** - Add plants with automatic care info using your AI assistant
- 🔄 **Bidirectional Sync** - Update Notion from Home Assistant and vice versa
- 🪴 **Example Plants** - Pre-configured templates to get started
- 📱 **Mobile Friendly** - Works on all Home Assistant apps

### Extended Plant Information

- ☀️ **Sun Exposure** - Track light requirements (Full Sun, Partial Sun, Shade)
- 🍅 **Harvest Info** - Record harvest months and notes
- 🌻 **Companion Plants** - Get planting suggestions
- 🚫 **Bad Companions** - Plants to avoid planting nearby
- 🐝 **Bee Friendly** - Mark pollinator-friendly plants
- ⚠️ **Toxicity Warnings** - Safety info for pets and children
- 🌱 **Lawn Care** - Track aeration and sanding schedules
- 🔄 **Lifecycle** - Perennial, Annual, or Biennial
- 🌡️ **Hardiness Zone** - USDA zones 1-13
- 🪴 **Soil Type** - Sandy, Loamy, Clay, etc.
- ⚗️ **Soil pH** - Acidic, Neutral, or Alkaline
- 📏 **Height** - Expected mature height
- 📈 **Growth per Year** - Annual growth rate
- ❄️ **Winterize** - Winter protection requirements

## 🚀 Quick Start

### Step 1: Create a Notion Account (if you don't have one)

1. Go to [https://www.notion.so/signup](https://www.notion.so/signup)
2. Sign up for a free account (email or Google/Apple)
3. Complete the onboarding

### Step 2: Create Notion Integration (2 minutes)

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Fill in the required fields:
   - **Name:** `Home Assistant Garden`
   - **Associated workspace:** Select your Notion workspace
   - **Type:** Leave as **Internal**
4. Under **Capabilities**, enable at minimum:
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
5. Click **"Save"**
6. **Copy the token** (starts with `ntn_...`) from the **Secrets** tab

> **Note:** Make sure to select your workspace and enable all three content capabilities — without them the integration cannot read or write your Notion database.

### Step 3: Create a Page in Notion (1 minute)

1. Open Notion and create a new blank page (e.g., "Gardening" or "Home Assistant")
2. **Connect your integration:**
   - Click **"..."** (three dots, top right)
   - Select **"Connections"** → Add **"Home Assistant Garden"** → Confirm
3. **Copy the page URL** from your browser

### Step 4: Install & Configure in Home Assistant (3 minutes)

#### Install the Integration

**Option A: HACS (Coming Soon)**
1. Open HACS → Integrations → Search "Notion Garden Care" → Install

**Option B: Manual Install**
```bash
cd /config/custom_components
git clone https://github.com/pfalzcraft/notion-garden-care.git
cp -r notion-garden-care/custom_components/notion_garden_care .
rm -rf notion-garden-care
```

Restart Home Assistant.

#### Setup in UI

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"** → Search **"Notion Garden Care"**
3. Follow the setup wizard:
   - **Screen 1:** Paste your Notion token
   - **Screen 2:** Paste your page URL
   - ✅ Keep "Create database automatically" checked
   - ✅ Keep "Add example plants" checked
   - Click **Submit**

**That's it!** 🎉

The integration will:
- ✅ Create the "Garden Care" database in Notion with all properties and formulas
- ✅ Add 5 example plants (Tomatoes, Rose, Apple Tree, Basil, Lawn)
- ✅ Create aggregate sensors and individual plant sensors in Home Assistant
- ✅ Register frontend resources automatically
- ✅ Create the Garden Care dashboard in YAML mode
- ✅ Write `garden-care.yaml` with the self-healing root card

### Step 5: Configure AI Agent (Optional - Recommended)

1. **Install a Conversation Agent** (if you don't have one):
   - **Settings** → **Devices & Services** → **Add Integration**
   - Add one of: **OpenAI Conversation**, **Google Generative AI**, **Anthropic**, or any other AI agent

2. **Connect to Garden Care:**
   - **Settings** → **Devices & Services** → **Notion Garden Care** → **Configure** (gear icon)
   - Select your **Conversation Agent** → **Submit**

3. **Add Plants with AI:**
   - Use the **Add Plant** form on the dashboard, or:
   ```yaml
   action: notion_garden_care.add_plant
   data:
     plant_name: "Lavender"
   ```
   The AI fills in all care details tailored to your local climate using your HA location settings.

### Step 6: Assign Plants to Areas (Recommended)

After setup, assign each plant sensor to a Home Assistant area to enable area grouping and bulk care:

1. **Settings** → **Devices & Services** → find a plant sensor → click it
2. Click the **Area** field → select or create an area
3. The dashboard groups and grid update automatically on the next browser refresh

> **Tip:** Set an area picture in **Settings** → **Areas** — it becomes the background image of that area's section header in the dashboard.

## 📊 What You Get

### Sensors

**Aggregate Sensors (always created):**
- `sensor.notion_garden_care_database` - All plants from Notion
- `sensor.plants_to_water` - Plants needing water today
- `sensor.plants_to_fertilize` - Plants needing fertilizer today
- `sensor.plants_to_prune` - Plants to prune this month
- `sensor.active_plants_count` - Total active plants

**Individual Plant Sensors (one per plant):**
- `sensor.garden_care_tomatoes` — shows status, all care dates, and attributes

Each plant sensor state is one of: `"OK"`, `"Needs Water"`, `"Needs Fertilizer"`, `"Needs Pruning"`.

#### Sensor Logic

**🚰 Plants to Water** — "Next Water" date is today or in the past  
**🌿 Plants to Fertilize** — "Next Fertilize" date is today or in the past  
**✂️ Plants to Prune** — current month is in the plant's "Prune Months" list  
**🌺 Active Plants Count** — "Active" checkbox is checked

### Actions

Update your plants from Home Assistant (11 actions available):

```yaml
# Mark single plant as watered (today)
action: notion_garden_care.mark_as_watered
data:
  entity_id: sensor.garden_care_tomatoes

# Mark plant as watered on a specific date
action: notion_garden_care.mark_as_watered
data:
  plant_name: "Tomatoes"
  date: "2026-01-20"

# Water ALL plants in a Home Assistant area at once
action: notion_garden_care.mark_as_watered
data:
  area_id: balcony

# Mark plant as fertilized / pruned / harvested / aerated / sanded / mowed
action: notion_garden_care.mark_as_fertilized
data:
  entity_id: sensor.garden_care_rose_bush

# Update any Notion property directly
action: notion_garden_care.update_plant_property
data:
  entity_id: sensor.garden_care_tomatoes
  property_name: "Water Interval (days)"
  property_value: "5"

# Add a new plant using AI
action: notion_garden_care.add_plant
data:
  plant_name: "Lavender"

# Refresh data from Notion
action: notion_garden_care.refresh_database
```

#### Action Parameters

All `mark_as_*` actions accept **one** of:
- `entity_id` — select a plant sensor
- `plant_name` — plant name as a string
- `page_id` — Notion page ID
- `area_id` — HA area ID → **updates all plants in that area at once**

Plus an optional `date` (YYYY-MM-DD, defaults to today).

### AI-Powered Plant Addition

Configure an AI conversation agent (OpenAI, Google AI, Anthropic, etc.) and the integration will automatically fill in:
- Plant type, lifecycle, hardiness zone, soil requirements
- Sun exposure, watering and fertilizing schedules
- Pruning and harvest months with instructions
- Companion plants, toxicity, bee-friendliness
- Care guide URLs, winter protection, special notes
- All tailored to your local climate via your HA location settings

### Automation Blueprints

Set up reminders in seconds via **Settings** → **Automations & Scenes** → **Create Automation** → **Start with blueprint**:
- Garden Care - Watering Reminder (daily)
- Garden Care - Fertilizing Reminder (daily)
- Garden Care - Pruning Reminder (monthly)

## 📱 Dashboard

### How It Works

The dashboard is created automatically on install. It uses a single `custom:garden-care-root-card` that:

- **Auto-discovers** all plant sensors from `hass.states` at page load — no YAML regeneration needed
- **Groups by HA area** using live `hass.entities` / `hass.areas` data
- **Responsive grid** — one column per area, adapts to any screen width
- **Area background images** — uses your HA area picture as the section header background
- **Rebuilds automatically** when plants are added or area assignments change
- **Self-healing** — if deleted, reload the integration to recreate it

### Plant Care Card

Each plant card displays:
- **Clickable plant name** — click to open the HA more-info dialog
- **Area label** — shown below the plant name; updates live when area assignment changes
- Type-specific icon (flower, tree, vegetable, herb, lawn, etc.)
- **Next** and **Last** dates for Water, Fertilize, Prune, Harvest (lawn: Aeration, Sanding, Mowed)
- Overdue indicators highlighted in red/orange
- **ⓘ Info button** — shows all plant attributes in a popup
- **Action buttons** — Water / Fertilize / Prune / Harvest with loading and success feedback
- **Delete button** — removes the plant from Notion with inline confirmation

### Add Plant Form

At the top of the dashboard:
- Enter a plant name → click **Add Plant**
- AI generates the full care profile
- **Duplicate protection** — won't create a plant that already exists
- **Auto-refresh** — triggers `refresh_database` automatically so the new plant appears without a manual reload

### Area Sections

Each HA area gets its own column with:
- A header card showing the area name and bulk action buttons
- The area picture (set in **Settings → Areas**) as background with a readable overlay
- All plants assigned to that area stacked below

Plants not assigned to any area appear in a separate column at the end.

### Manual Dashboard Setup

If the dashboard wasn't created automatically:

1. **Settings** → **Dashboards** → **Add Dashboard**
2. Title: `Garden Care`, Icon: `mdi:flower`
3. Select **YAML** mode, Filename: `garden-care.yaml`
4. Click **Create**, then reload the integration

> **If the dashboard is empty or stuck:** delete it in **Settings → Dashboards**, then reload the integration. It will be recreated automatically in YAML mode.

## 🌱 Notion Database Structure

The integration creates these properties automatically:

### Basic Info
- **Name** - Plant name
- **Type** - Plant, Tree, Shrub, Vegetable, Herb, Lawn
- **Active** - Is the plant still active?

> **Note:** Location is not a Notion field. Use **Home Assistant Areas** instead — assign each plant sensor to an area in Settings → Devices & Services → (entity) → Area. This enables area-based grouping and bulk actions.

### Watering
- **Water Interval (days)**, **Last Watered**, **Next Water** (auto-calculated ✨), **Water Amount**

### Fertilizing
- **Fertilize Interval (days)**, **Last Fertilized**, **Next Fertilize** (auto-calculated ✨), **Fertilizer Type**

### Pruning
- **Prune Months**, **Prune Instructions**, **Last Pruned**

### Harvest
- **Harvest Months**, **Harvest Notes**, **Last Harvested**

### Plant Characteristics
- **Lifecycle**, **Hardiness Zone**, **Soil Type**, **Soil pH**, **Height**, **Growth per Year**, **Winterize**

### Companion & Safety
- **Companion Plants**, **Bad Companions**, **Bee Friendly**, **Toxicity**

### Lawn Care
- **Aeration Interval (days)**, **Last Aeration**, **Next Aeration** (auto-calculated ✨)
- **Sanding Interval (days)**, **Last Sanded**, **Next Sanding** (auto-calculated ✨), **Last Mowed**

### Notes & Links
- **Care Instructions**, **Special Notes**, **Notes**
- **Care Instructions URL**, **Prune Instructions URL**, **Harvest Instructions URL**

### Sun & Environment
- **Sun Exposure** - Full Sun, Partial Sun, Partial Shade, Full Shade

## 🎯 How It Works

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Home Assistant │◄────────┤   Notion API     ├────────►│     Notion      │
│   Integration   │  Sync   │   (REST)         │  Create │    Database     │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │
        ▼
  Plant sensors created
  Aggregate sensors updated hourly
  Actions + automations available
  Self-healing dashboard in sidebar
```

## 📝 Example Use Cases

### Morning Routine Automation

```yaml
automation:
  - alias: "Morning Garden Report"
    trigger:
      - platform: time
        at: "07:00:00"
    actions:
      - action: notify.mobile_app
        data:
          title: "Good Morning! Garden Update"
          message: >
            🌱 {{ states('sensor.active_plants_count') }} plants total
            💧 {{ states('sensor.plants_to_water') }} need water
            🌿 {{ states('sensor.plants_to_fertilize') }} need fertilizer
```

### Water an Entire Area

```yaml
automation:
  - alias: "Evening Balcony Watering"
    trigger:
      - platform: time
        at: "19:00:00"
    actions:
      - action: notion_garden_care.mark_as_watered
        data:
          area_id: balcony
```

### Dashboard Button

```yaml
type: button
name: Water Tomatoes
tap_action:
  action: perform-action
  perform_action: notion_garden_care.mark_as_watered
  data:
    plant_name: Tomatoes
icon: mdi:watering-can
```

## 🐛 Troubleshooting

### Dashboard is empty or not created

1. Delete any existing "garden-care" dashboard in **Settings → Dashboards**
2. Reload the integration: **Settings → Devices & Services → Notion Garden Care → ⋮ → Reload**
3. Hard-refresh your browser: **Ctrl+Shift+R**

The integration automatically creates a YAML-mode dashboard and writes `garden-care.yaml`. The self-healing root card discovers your plants at page load — no additional setup needed.

### Cards don't appear (custom element errors)

The integration auto-registers both JS files as Lovelace resources on startup. If you see "Custom element doesn't exist":

1. Reload the integration
2. Hard-refresh your browser (**Ctrl+Shift+R**)
3. Open **Developer Tools** (F12) → **Console** and confirm you see:
   ```
   PLANT-CARE-CARD         Loaded
   GARDEN-AREA-CARD        Loaded
   GARDEN-CARE-ROOT-CARD   Loaded
   ```
4. If the messages are missing, check **Settings → Dashboards → ⋮ → Resources** — both entries should be present. If not, reload the integration again.

### Integration doesn't appear

1. Verify files are in `custom_components/notion_garden_care/`
2. Restart Home Assistant
3. Check logs: **Settings** → **System** → **Logs**

### Sensors show "Unavailable"

1. Check Notion connection: open page in Notion → **"..."** → **Connections** — "Home Assistant Garden" should be listed
2. Verify your Notion token is correct
3. Call `notion_garden_care.refresh_database`
4. Check Home Assistant logs

### New plant doesn't appear after adding

The Add Plant form automatically triggers a database refresh after creation. If the plant still doesn't appear after ~30 seconds, call `notion_garden_care.refresh_database` manually, then hard-refresh your browser.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes
4. Open a Pull Request

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/pfalzcraft/notion-garden-care/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pfalzcraft/notion-garden-care/discussions)

## ☕ Buy Me a Coffee

If you find this integration helpful, consider supporting the development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/pfalzcraft)

---

**Made with 🌱 for gardeners who love automation**

**No Python knowledge required · No YAML editing needed · Just works ✨**

---

<p align="center">
  <a href="https://buymeacoffee.com/pfalzcraft">
    <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20This%20Project-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black" alt="Buy Me A Coffee">
  </a>
</p>
