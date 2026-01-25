# 🌱 Notion Garden Care for Home Assistant

Manage your garden with Notion and automate reminders with Home Assistant. Track watering, fertilizing, and pruning schedules for all your plants in one place.

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=homeassistant)
![Notion](https://img.shields.io/badge/Notion-Database-000000?logo=notion)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🌿 **Notion Database** - Beautiful, flexible plant management
- 📅 **Automated Reminders** - Never forget to water, fertilize, or prune
- 📊 **Dashboard** - Visual overview of all garden tasks
- 🔄 **Auto-sync** - Bidirectional sync between Notion and Home Assistant
- 🪴 **Example Plants** - Pre-configured templates to get started
- 🔔 **Smart Notifications** - Daily and monthly reminders
- 📱 **Mobile Friendly** - Works on all Home Assistant apps

## 📸 Screenshots

*Add screenshots of your Notion database and Home Assistant dashboard here*

## 🚀 Quick Start

### Prerequisites

- [Notion](https://notion.so) account (free tier works!)
- [Home Assistant](https://www.home-assistant.io/) installation
- Python 3.8+ (for database setup)

### Installation

#### Step 1: Clone this Repository

```bash
git clone https://github.com/yourusername/notion-garden-care.git
cd notion-garden-care
```

#### Step 2: Create Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Name: `Home Assistant Garden`
4. Click **"Submit"**
5. **Copy the "Internal Integration Secret"** (starts with `secret_...`)

#### Step 3: Create Parent Page in Notion

1. Open Notion
2. Create a new page (e.g., "Gardening" or "Home Assistant")
3. Connect the integration to this page:
   - Click **"..."** (top right)
   - Select **"Connections"**
   - Add **"Home Assistant Garden"**
   - Confirm

#### Step 4: Setup Python Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your Notion token
# NOTION_TOKEN=your_token_here
```

#### Step 5: Create Notion Database Automatically

```bash
python create_database_en.py
```

This script will:
- ✅ Create the "Garden Care" database with all properties
- ✅ Add formula fields for automatic date calculations
- ✅ Populate with example plants (Tomatoes, Rose Bush, Apple Tree, Basil)
- ✅ Save the Database ID to `.env`

#### Step 6: Configure Home Assistant

1. Copy the configuration files to your Home Assistant config directory:

```bash
# Copy to your Home Assistant config folder
cp homeassistant/config/configuration.yaml <your-ha-config-path>/packages/garden_care.yaml
cp homeassistant/config/secrets.yaml <your-ha-config-path>/secrets.yaml
cp homeassistant/config/automations.yaml <your-ha-config-path>/automations.yaml
```

2. Update `secrets.yaml` with your credentials:

```yaml
notion_token: "your_notion_token_here"
notion_auth_header: "Bearer your_notion_token_here"
notion_database_id: "your_database_id_here"
notion_database_query_url: "https://api.notion.com/v1/databases/your_database_id_here/query"
```

3. Restart Home Assistant

#### Step 7: Add Dashboard (Optional)

1. In Home Assistant, go to **Settings** → **Dashboards**
2. Create a new dashboard or edit existing
3. Click **"..."** → **"Edit"** → **"Raw Configuration Editor"**
4. Paste contents from `homeassistant/config/dashboard.yaml`
5. Save

## 📊 Notion Database Structure

The database includes the following properties:

### Basic Information
- **Name** (Title) - Plant name
- **Type** (Select) - Plant, Tree, Shrub, Vegetable, Herb, Lawn
- **Location** (Select) - Garden, Balcony, Terrace, Conservatory, Indoor
- **Active** (Checkbox) - Is the plant still active?

### Watering
- **Water Interval (days)** (Number) - Days between watering
- **Last Watered** (Date) - Date of last watering
- **Next Water** (Formula) - Auto-calculated next watering date
- **Water Amount** (Select) - Low, Medium, High

### Fertilizing
- **Fertilize Interval (days)** (Number) - Days between fertilizing
- **Last Fertilized** (Date) - Date of last fertilizing
- **Next Fertilize** (Formula) - Auto-calculated next fertilizing date
- **Fertilizer Type** (Text) - Type of fertilizer used

### Pruning
- **Prune Months** (Multi-select) - Months when pruning is needed
- **Prune Instructions** (Text) - Detailed pruning instructions
- **Last Pruned** (Date) - Date of last pruning

### Care & Notes
- **Care Instructions** (Text) - General care instructions
- **Special Notes** (Text) - Any special requirements
- **Notes** (Text) - Free-form notes

## 🎯 How It Works

### Data Flow

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Notion    │◄────────┤  Home Assistant  ├────────►│ Notifications   │
│  Database   │  Sync   │  REST API        │  Send   │ (Mobile/Web)    │
└─────────────┘         └──────────────────┘         └─────────────────┘
       │                         │
       │                         │
       ▼                         ▼
   Add/Edit Plants          Create Sensors
   Set Intervals            Run Automations
```

### Sensors

Home Assistant creates the following sensors:

- `sensor.notion_garden_care_database` - Raw data from Notion
- `sensor.plants_to_water` - Count of plants needing water
- `sensor.plants_to_fertilize` - Count of plants needing fertilizer
- `sensor.plants_to_prune` - Count of plants to prune this month
- `sensor.active_plants_count` - Total active plants

### Automations

- **Daily 7 AM** - Watering reminder (if plants need water)
- **Daily 8 AM** - Fertilizing reminder (if plants need fertilizer)
- **Monthly 1st** - Pruning reminder (for current month)
- **On Change** - Persistent notifications in Home Assistant

## ⚙️ Customization

### Change Notification Times

Edit `automations.yaml`:

```yaml
trigger:
  - platform: time
    at: "07:00:00"  # Change to your preferred time
```

### Change Notification Service

Replace `notify.notify` with your service:

```yaml
action:
  - service: notify.mobile_app_your_device  # Your notification service
```

Available services:
- `notify.mobile_app_your_phone` - Home Assistant Companion App
- `notify.telegram` - Telegram
- `notify.pushbullet` - Pushbullet
- `persistent_notification.create` - Home Assistant UI (default)

### Add Custom Plant Types

Edit Notion database:
1. Go to Notion database
2. Click on "Type" column
3. Add more options (e.g., "Flower", "Cactus", "Fern")

## 🔄 Update Data from Notion to Home Assistant

The sensor automatically updates every hour. To manually refresh:

1. **Developer Tools** → **Services**
2. Service: `homeassistant.update_entity`
3. Entity: `sensor.notion_garden_care_database`
4. Call Service

## 📝 Update Data from Home Assistant to Notion

Use the provided REST commands:

### Mark Plant as Watered

```yaml
service: rest_command.notion_update_last_watered
data:
  page_id: "your_plant_page_id"
```

### Mark Plant as Fertilized

```yaml
service: rest_command.notion_update_last_fertilized
data:
  page_id: "your_plant_page_id"
```

### Mark Plant as Pruned

```yaml
service: rest_command.notion_update_last_pruned
data:
  page_id: "your_plant_page_id"
```

*To get the `page_id`, check the `plant_details` attribute in the sensors.*

## 🐛 Troubleshooting

### Sensor shows "unavailable"

**Solution:**
1. Check `secrets.yaml` - Ensure token and database ID are correct
2. Verify the Notion integration is connected to the database
3. Check Home Assistant logs: **Settings** → **System** → **Logs**

### No notifications received

**Solution:**
1. Verify a notification service is configured
2. Check automation conditions (time, count > 0)
3. Test notification service manually in **Developer Tools** → **Services**

### Template errors in logs

**Solution:**
1. Ensure Notion database property names match exactly (case-sensitive!)
2. Verify formula fields are properly configured in Notion
3. Wait for database to fully sync (can take a few minutes)

### Database not created

**Solution:**
1. Ensure the parent page exists in Notion
2. Verify the integration is connected to the parent page
3. Check Python script output for errors

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Home Assistant](https://www.home-assistant.io/) - Open source home automation
- [Notion](https://www.notion.so/) - All-in-one workspace
- [Notion API](https://developers.notion.com/) - Official Notion API

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/notion-garden-care/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/notion-garden-care/discussions)
- **Home Assistant Community:** [Forum Thread](https://community.home-assistant.io/)

---

**Made with 🌱 for gardeners who love automation**
