# 🌱 Notion Garden Care for Home Assistant

Manage your garden with Notion and automate reminders with Home Assistant. Track watering, fertilizing, and pruning schedules for all your plants in one place.

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=homeassistant)
![Notion](https://img.shields.io/badge/Notion-Database-000000?logo=notion)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🌿 **Automatic Setup** - No coding required, everything happens in Home Assistant UI
- 🗄️ **Auto-Create Database** - Integration creates the Notion database for you
- 📅 **Smart Reminders** - Never forget to water, fertilize, or prune
- 📊 **Beautiful Dashboard** - Visual overview of all garden tasks
- 🔄 **Bidirectional Sync** - Update Notion from Home Assistant and vice versa
- 🪴 **Example Plants** - Pre-configured templates to get started
- 📱 **Mobile Friendly** - Works on all Home Assistant apps

### Extended Plant Information

- ☀️ **Sun Exposure** - Track light requirements (Full Sun, Partial Sun, Shade)
- 🍅 **Harvest Info** - Record harvest months and notes
- 🌻 **Companion Plants** - Get planting suggestions
- 🐝 **Bee Friendly** - Mark pollinator-friendly plants
- ⚠️ **Toxicity Warnings** - Safety info for pets and children
- 🌱 **Lawn Care** - Track aeration schedules

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
   - Click **Submit**

**That's it!** 🎉

The integration will:
- ✅ Create the "Garden Care" database in Notion
- ✅ Set up all properties and formulas
- ✅ Add 5 example plants (Tomatoes, Rose, Apple Tree, Basil, Lawn)
- ✅ Create 5 sensors in Home Assistant
- ✅ Register 4 services for plant updates

## 📊 What You Get

### Sensors

After setup, you'll have these sensors:

- `sensor.notion_garden_care_database` - All plants from Notion
- `sensor.plants_to_water` - Plants needing water today
- `sensor.plants_to_fertilize` - Plants needing fertilizer today
- `sensor.plants_to_prune` - Plants to prune this month
- `sensor.active_plants_count` - Total active plants

### Services

Update your plants from Home Assistant:

```yaml
# Mark plant as watered
service: notion_garden_care.mark_as_watered
data:
  plant_name: "Tomatoes"

# Mark plant as fertilized
service: notion_garden_care.mark_as_fertilized
data:
  plant_name: "Rose Bush"

# Mark plant as pruned
service: notion_garden_care.mark_as_pruned
data:
  plant_name: "Apple Tree"

# Refresh data from Notion
service: notion_garden_care.refresh_database
```

### Automation Blueprints

Set up reminders in seconds:

1. **Settings** → **Automations & Scenes**
2. **Create Automation** → **Start with blueprint**
3. Choose:
   - **Garden Care - Watering Reminder** (daily)
   - **Garden Care - Fertilizing Reminder** (daily)
   - **Garden Care - Pruning Reminder** (monthly)

## 📱 Add Dashboard (Optional)

1. **Settings** → **Dashboards** → Your Dashboard
2. **Edit** → **+ Add Card** → **Manual**
3. Copy YAML from [`homeassistant/config/dashboard.yaml`](homeassistant/config/dashboard.yaml)

Or create cards manually:
- Glance card with all sensors
- Conditional markdown cards for task lists

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

### Companion & Safety
- **Companion Plants** - Plants that grow well together
- **Bee Friendly** - Is it good for pollinators?
- **Toxicity** - Safety warnings (Safe, Toxic to Pets, Toxic to Children, Toxic to Both)

### Lawn Care
- **Aeration Interval (days)** - Days between aeration
- **Last Aeration** - Date of last aeration
- **Next Aeration** - Auto-calculated ✨

### Notes
- **Care Instructions** - General care tips
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

## 📸 Screenshots

*Coming soon - Add your screenshots!*

---

## Advanced Usage (For Developers)

If you want to use the Python scripts directly without Home Assistant:

See [docs/standalone_setup.md](docs/standalone_setup.md) for manual database creation.

---

**Made with 🌱 for gardeners who love automation**

**No Python knowledge required • No YAML editing needed • Just works ✨**
