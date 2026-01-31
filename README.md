[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/pfalzcraft)

# 🌱 Notion Garden Care for Home Assistant

Manage your garden with Notion and automate reminders with Home Assistant. Track watering, fertilizing, and pruning schedules for all your plants in one place.

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=homeassistant)
![Notion](https://img.shields.io/badge/Notion-Database-000000?logo=notion)
![License](https://img.shields.io/badge/License-MIT-green)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/pfalzcraft)

## ✨ Features

- 🌿 **Automatic Setup** - No coding required, everything happens in Home Assistant UI
- 🗄️ **Auto-Create Database** - Integration creates the Notion database for you
- 📅 **Smart Reminders** - Never forget to water, fertilize, or prune
- 📊 **Auto-Created Dashboard** - Beautiful dashboard with plant cards auto-generated on install
- ➕ **Add Plant Form** - Easy form to add new plants directly from the dashboard
- 🃏 **Custom Plant Cards** - Interactive cards showing care schedules with action buttons
- 🔄 **Bidirectional Sync** - Update Notion from Home Assistant and vice versa
- 🪴 **Example Plants** - Pre-configured templates to get started
- 📱 **Mobile Friendly** - Works on all Home Assistant apps
- 🤖 **AI-Powered Plant Addition** - Add plants with automatic care info using your AI assistant

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

## 🚀 Quick Start (3 Steps!)

### Step 1: Create Notion Integration (2 minutes)

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Name: `Home Assistant Garden`
4. Click **"Submit"**
5. **Copy the token** (starts with `secret_...` or `ntn_...`)

### Step 2: Create a Page in Notion (1 minute)

1. Open Notion
2. Create a new blank page (e.g., "Gardening" or "Home Assistant")
3. **Connect your integration:**
   - Click **"..."** (three dots, top right)
   - Select **"Connections"**
   - Add **"Home Assistant Garden"**
   - Confirm
4. **Copy the page URL** from your browser

### Step 3: Install & Configure in Home Assistant (3 minutes)

#### Install the Integration

**Option A: HACS (Coming Soon)**
1. Open HACS → Integrations
2. Search "Notion Garden Care"
3. Install

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
2. Click **"+ Add Integration"**
3. Search **"Notion Garden Care"**
4. Follow the setup wizard:
   - **Screen 1:** Paste your Notion token
   - **Screen 2:** Paste your page URL
   - ✅ Keep "Create database automatically" checked
   - ✅ Keep "Add example plants" checked
   - ✅ Keep "Create individual sensors for each plant" checked (or uncheck for aggregate sensors only)
   - Click **Submit**

**That's it!** 🎉

The integration will:
- ✅ Create the "Garden Care" database in Notion
- ✅ Set up all properties and formulas
- ✅ Add 5 example plants (Tomatoes, Rose, Apple Tree, Basil, Lawn)
- ✅ Create 5 aggregate sensors in Home Assistant
- ✅ Create individual sensors for each plant (if enabled)
- ✅ Register 4 services for plant updates

## 📊 What You Get

### Sensors

After setup, you'll have these sensors:

**Aggregate Sensors (always created):**
- `sensor.notion_garden_care_database` - All plants from Notion
- `sensor.plants_to_water` - Plants needing water today
- `sensor.plants_to_fertilize` - Plants needing fertilizer today
- `sensor.plants_to_prune` - Plants to prune this month
- `sensor.active_plants_count` - Total active plants

**Individual Plant Sensors (optional, enabled by default):**
- `sensor.garden_care_tomatoes` - Individual sensor for Tomatoes
- `sensor.garden_care_rose_bush` - Individual sensor for Rose Bush
- `sensor.garden_care_apple_tree` - Individual sensor for Apple Tree
- ... one sensor per plant in your database!

Each plant sensor shows:
- **State:** Status text ("OK", "Needs Water", "Needs Fertilizer", "Needs Pruning")
- **Attributes:** All plant properties from Notion (type, location, watering schedule, etc.)
- **Icon:** Changes based on plant type (tree, vegetable, herb, etc.)

#### 📋 Detailed Sensor Logic

> **📚 For complete documentation with examples and troubleshooting, see [docs/SENSORS.md](docs/SENSORS.md)**

Understanding when plants appear in each sensor:

**🚰 Plants to Water** (`sensor.plants_to_water`)
- **Shows when:** The "Next Water" date is **today or in the past**
- **Example:** If today is Jan 25 and "Next Water" shows Jan 24 or Jan 25 → Plant appears in sensor
- **Formula:** `Next Water = Last Watered + Water Interval (days)`
- **Attributes:** Lists plant names and due dates
- **Updates:** Every hour automatically

**🌿 Plants to Fertilize** (`sensor.plants_to_fertilize`)
- **Shows when:** The "Next Fertilize" date is **today or in the past**
- **Example:** If today is Jan 25 and "Next Fertilize" shows Jan 20 → Plant appears in sensor
- **Formula:** `Next Fertilize = Last Fertilized + Fertilize Interval (days)`
- **Attributes:** Lists plant names and due dates
- **Updates:** Every hour automatically

**✂️ Plants to Prune** (`sensor.plants_to_prune`)
- **Shows when:** The **current month** is in the plant's "Prune Months" list
- **Example:** If today is January and plant has "January, March" in Prune Months → Plant appears
- **Note:** Month-based (not date-based like watering/fertilizing)
- **Attributes:** Lists plant names and all their pruning months
- **Updates:** Every hour automatically

**🌺 Active Plants Count** (`sensor.active_plants_count`)
- **Shows when:** The "Active" checkbox is **checked**
- **Purpose:** Track only plants you're actively caring for (excludes dead/removed plants)
- **Example:** 10 plants total, 2 marked inactive → Sensor shows 8
- **Updates:** Every hour automatically

**🗄️ Notion Garden Care Database** (`sensor.notion_garden_care_database`)
- **Shows:** Total count of **all plants** in the database (no filtering)
- **Attributes:** Contains full raw data from Notion
- **Note:** All plants are counted regardless of active status

### Services

Update your plants from Home Assistant (11 services available):

```yaml
# Mark plant as watered (today)
service: notion_garden_care.mark_as_watered
data:
  entity_id: sensor.garden_care_tomatoes  # Or use plant_name

# Mark plant as watered on a specific date
service: notion_garden_care.mark_as_watered
data:
  plant_name: "Tomatoes"
  date: "2026-01-20"

# Mark plant as fertilized
service: notion_garden_care.mark_as_fertilized
data:
  plant_name: "Rose Bush"

# Mark plant as pruned
service: notion_garden_care.mark_as_pruned
data:
  plant_name: "Apple Tree"

# Mark plant as harvested
service: notion_garden_care.mark_as_harvested
data:
  plant_name: "Tomatoes"

# Mark lawn as aerated
service: notion_garden_care.mark_as_aerated
data:
  plant_name: "Lawn"

# Mark lawn as sanded
service: notion_garden_care.mark_as_sanded
data:
  plant_name: "Lawn"

# Mark lawn as mowed
service: notion_garden_care.mark_as_mowed
data:
  plant_name: "Lawn"

# Update any property (generic service with dropdown)
service: notion_garden_care.update_plant_property
data:
  entity_id: sensor.garden_care_tomatoes
  property_name: "Water Interval (days)"
  property_value: "5"

# Add a new plant using AI
service: notion_garden_care.add_plant
data:
  plant_name: "Lavender"

# Refresh data from Notion
service: notion_garden_care.refresh_database
```

#### Service Parameters

All `mark_as_*` services accept:
- `entity_id` (entity selector) - Select plant from dropdown (or)
- `plant_name` (string) - Name of the plant (or)
- `page_id` (string) - Notion page ID
- `date` (optional) - Date in YYYY-MM-DD format (defaults to today)

The `update_plant_property` service accepts:
- `entity_id`, `plant_name`, or `page_id` - To identify the plant
- `property_name` (required) - Select from dropdown with all available properties
- `property_value` (required) - Value to set (auto-detects type: number, checkbox, date, multi-select, or text)

The `add_plant` service accepts:
- `plant_name` (required) - Name of the plant to add (AI will fill in all care details)

### AI-Powered Plant Addition

Add plants with automatic care information using AI:

1. **Configure AI Agent:**
   - Go to **Settings** → **Devices & Services**
   - Find **Notion Garden Care** → Click **Configure** (gear icon)
   - Select your **Conversation Agent** (e.g., OpenAI, Google AI, Claude)
   - Click **Submit**

2. **Add Plants:**
   ```yaml
   service: notion_garden_care.add_plant
   data:
     plant_name: "Lavender"
   ```

The AI will automatically fill in:
- Plant type and location
- Lifecycle (perennial/annual/biennial)
- Hardiness zone and soil requirements
- Sun exposure requirements
- Watering schedule and amount
- Fertilizing schedule and type
- Pruning months and instructions
- Harvest information (if applicable)
- Height and growth rate
- Companion plants and bad companions
- Bee-friendly status
- Toxicity warnings
- Winter protection requirements
- Care instructions and special notes
- **URLs to care guides** (care, pruning, and harvesting instructions from reputable gardening sites)

### Automation Blueprints

Set up reminders in seconds:

1. **Settings** → **Automations & Scenes**
2. **Create Automation** → **Start with blueprint**
3. Choose:
   - **Garden Care - Watering Reminder** (daily)
   - **Garden Care - Fertilizing Reminder** (daily)
   - **Garden Care - Pruning Reminder** (monthly)

## 📱 Dashboard

### Auto-Created Dashboard

When you install the integration, a **Garden Care** dashboard is automatically created and appears in your sidebar. This dashboard uses the `custom:garden-care` strategy to auto-populate with all your plants.

The dashboard includes:
- **Add Plant Form** - Easy form to add new plants at the top
- **Plant Cards** - Individual cards for each plant with care schedules and action buttons

### Add Plant Card

At the top of the Plants view, you'll find the **Add Plant** form:
- Enter a plant name in the text box
- Click **Add Plant** to create a new plant with AI-generated care info
- **Duplicate protection** - Won't create a plant if the name already exists
- Shows loading spinner while AI processes
- Displays success/error messages

### Plant Care Card

Each plant card displays:
- Plant name with type-specific icon (flower, tree, vegetable, etc.)
- Location badge
- Care schedule with both **Next** and **Last** dates:
  - Water: Next date with days until/overdue indicator + last watered date
  - Fertilize: Next date with days until/overdue + last fertilized date
  - Prune: Months (highlighted if current month) + last pruned date (only shown if plant has prune months)
  - Harvest: Months (highlighted if current month) + last harvested date (only shown if plant has harvest months)
  - Aeration/Sanding/Mowed: For lawns only
- **Info button** - Click to see all plant attributes in a popup
- **Action buttons** - Mark tasks as complete with visual feedback (loading spinner, success/error states)

### Manual Dashboard Setup

If you prefer to create the dashboard manually:

1. **Settings** → **Dashboards** → **Add Dashboard**
2. Name it "Garden Care" → **Create**
3. Click **Edit** → **Three dots** → **Raw configuration editor**
4. Replace content with:
   ```yaml
   strategy:
     type: custom:garden-care
   ```
5. **Save**

### Add Resources Manually (if needed)

The integration automatically registers the required JavaScript resources on startup. However, if the custom cards don't appear or you see errors, you may need to add them manually.

#### When Manual Setup is Required

- Dashboard shows "Custom element doesn't exist: plant-care-card"
- Cards appear blank or show errors
- After upgrading from an older version
- When using YAML mode dashboards

#### Step-by-Step Resource Setup

1. **Open Resources Page:**
   - Go to **Settings** → **Dashboards**
   - Click the **three dots menu** (top right) → **Resources**

2. **Add Plant Care Card Resource:**
   - Click **+ Add Resource**
   - URL: `/notion-garden-care/plant-care-card.js`
   - Resource Type: **JavaScript Module**
   - Click **Create**

3. **Add Dashboard Strategy Resource:**
   - Click **+ Add Resource**
   - URL: `/notion-garden-care/garden-care-strategy.js`
   - Resource Type: **JavaScript Module**
   - Click **Create**

4. **Refresh Browser:**
   - Hard refresh your browser: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)
   - Or clear browser cache and reload

#### Verify Resources are Loading

Open your browser's Developer Tools (F12) and check the Console tab. You should see:
```
PLANT-CARE-CARD  Loaded
GARDEN-CARE-STRATEGY  Loaded
```

If you see 404 errors for the JS files, verify the integration is installed correctly in `custom_components/notion_garden_care/` and restart Home Assistant.

### Use Plant Care Card Individually

You can also add the Plant Care Card to any dashboard:

1. **Edit Dashboard** → **Add Card**
2. Search for "Plant Care Card"
3. Select a plant entity from the dropdown

```yaml
type: custom:plant-care-card
entity: sensor.garden_care_tomatoes
```

## 🌱 Notion Database Structure

The integration creates these properties automatically:

### Basic Info
- **Name** - Plant name
- **Type** - Plant, Tree, Shrub, Vegetable, Herb, Lawn
- **Location** - Garden, Balcony, Terrace, etc.
- **Active** - Is the plant still active?

### Sun & Environment
- **Sun Exposure** - Full Sun, Partial Sun, Partial Shade, Full Shade

### Watering
- **Water Interval (days)** - Days between watering
- **Last Watered** - Date of last watering
- **Next Water** - Auto-calculated next watering date ✨
- **Water Amount** - Low, Medium, High

### Fertilizing
- **Fertilize Interval (days)** - Days between fertilizing
- **Last Fertilized** - Date of last fertilizing
- **Next Fertilize** - Auto-calculated next date ✨
- **Fertilizer Type** - Type of fertilizer

### Pruning
- **Prune Months** - Months when pruning needed
- **Prune Instructions** - Detailed instructions
- **Last Pruned** - Date of last pruning

### Harvest
- **Harvest Months** - When to harvest
- **Harvest Notes** - Harvest tips and timing
- **Last Harvested** - Date of last harvest

### Plant Characteristics
- **Lifecycle** - Perennial, Annual, or Biennial
- **Hardiness Zone** - USDA zones 1-13
- **Soil Type** - Sandy, Loamy, Clay, Silty, Peaty, Chalky, Any
- **Soil pH** - Acidic (pH < 6), Neutral (pH 6-7), Alkaline (pH > 7), Any
- **Height** - Expected mature height
- **Growth per Year** - Annual growth rate
- **Winterize** - Does it need winter protection?

### Companion & Safety
- **Companion Plants** - Plants that grow well together
- **Bad Companions** - Plants to avoid planting nearby
- **Bee Friendly** - Is it good for pollinators?
- **Toxicity** - Safety warnings (Safe, Toxic to Pets, Toxic to Children, Toxic to Both)

### Lawn Care
- **Aeration Interval (days)** - Days between aeration
- **Last Aeration** - Date of last aeration
- **Next Aeration** - Auto-calculated ✨
- **Sanding Interval (days)** - Days between sanding
- **Last Sanded** - Date of last sanding
- **Next Sanding** - Auto-calculated ✨
- **Last Mowed** - Date of last mowing

### Notes & Instructions
- **Care Instructions** - General care tips
- **Care Instructions URL** - Link to detailed care guide
- **Prune Instructions URL** - Link to pruning guide
- **Harvest Instructions URL** - Link to harvesting guide
- **Special Notes** - Special requirements
- **Notes** - Free-form notes

## 🎯 How It Works

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Home Assistant │◄────────┤   Notion API     ├────────►│     Notion      │
│   Integration   │  Sync   │   (REST)         │  Create │    Database     │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                                                          │
        │                                                          │
        ▼                                                          ▼
  5 Sensors Created                                     Auto-create DB
  4 Services Ready                                      Add Properties
  Blueprints Available                                  Formula Fields
```

## 🐛 Troubleshooting

### Integration doesn't appear

**Solution:**
1. Verify files are in `custom_components/notion_garden_care/`
2. Restart Home Assistant
3. Check logs: **Settings** → **System** → **Logs**

### Database not created

**Solution:**
1. Ensure the parent page exists in Notion
2. Verify the integration is connected to the page:
   - Open page in Notion → **"..."** → **Connections**
   - "Home Assistant Garden" should be listed
3. Try again with a fresh page

### Sensors show "Unavailable"

**Solution:**
1. Check if integration is connected in Notion (see above)
2. Verify token is correct
3. Call `notion_garden_care.refresh_database` service
4. Check Home Assistant logs

## 📝 Example Use Cases

### Morning Routine Automation

```yaml
automation:
  - alias: "Morning Garden Report"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Good Morning! Garden Update"
          message: >
            🌱 {{ states('sensor.active_plants_count') }} plants total
            💧 {{ states('sensor.plants_to_water') }} need water
            🌿 {{ states('sensor.plants_to_fertilize') }} need fertilizer
```

### Mark as Done Button

```yaml
# Create a button to mark plant as watered
type: button
name: Water Tomatoes
tap_action:
  action: call-service
  service: notion_garden_care.mark_as_watered
  service_data:
    plant_name: Tomatoes
icon: mdi:watering-can
```

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Home Assistant](https://www.home-assistant.io/) - Open source home automation
- [Notion](https://www.notion.so/) - All-in-one workspace
- [Notion API](https://developers.notion.com/) - Official Notion API

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/pfalzcraft/notion-garden-care/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pfalzcraft/notion-garden-care/discussions)
- **Installation Guide:** [INSTALLATION.md](INSTALLATION.md)

## ☕ Buy Me a Coffee

If you find this integration helpful, consider supporting the development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/pfalzcraft)

Your support helps keep this project maintained and improved!

## 📸 Screenshots

*Coming soon - Add your screenshots!*

---

## Advanced Usage (For Developers)

If you want to use the Python scripts directly without Home Assistant:

See [docs/standalone_setup.md](docs/standalone_setup.md) for manual database creation.

---

**Made with 🌱 for gardeners who love automation**

**No Python knowledge required • No YAML editing needed • Just works ✨**

---

<p align="center">
  <a href="https://buymeacoffee.com/pfalzcraft">
    <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20This%20Project-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black" alt="Buy Me A Coffee">
  </a>
</p>
