# Installation Guide - Notion Garden Care Custom Integration

This guide will walk you through installing the Notion Garden Care custom integration for Home Assistant.

## 📦 Installation Methods

### Method 1: HACS (Recommended - Coming Soon)

Once this integration is added to HACS, you'll be able to install it with one click:

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click "+ Explore & Download Repositories"
4. Search for "Notion Garden Care"
5. Click "Download"
6. Restart Home Assistant

### Method 2: Manual Installation

1. **Download the Integration**

   Clone or download this repository:
   ```bash
   cd /config  # or wherever your Home Assistant config directory is
   git clone https://github.com/pfalzcraft/notion-garden-care.git
   ```

2. **Copy Files to Custom Components**

   ```bash
   # Create custom_components directory if it doesn't exist
   mkdir -p custom_components

   # Copy the integration
   cp -r notion-garden-care/custom_components/notion_garden_care custom_components/
   ```

   Your directory structure should look like this:
   ```
   config/
   ├── custom_components/
   │   └── notion_garden_care/
   │       ├── __init__.py
   │       ├── config_flow.py
   │       ├── const.py
   │       ├── manifest.json
   │       ├── sensor.py
   │       ├── services.yaml
   │       ├── strings.json
   │       └── translations/
   │           └── en.json
   ├── configuration.yaml
   └── ...
   ```

3. **Restart Home Assistant**

   Go to **Settings** → **System** → **Restart**

---

## 🔧 Configuration

### Step 1: Create Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name: `Home Assistant Garden`
4. Select your workspace
5. Click **"Submit"**
6. **Copy the "Internal Integration Secret"** (starts with `secret_...` or `ntn_...`)

### Step 2: Create Parent Page in Notion (Optional)

If you want the integration to create the database automatically:

1. Open Notion
2. Create a new blank page (e.g., "Gardening")
3. **Important:** Connect your integration to this page:
   - Click **"..."** (three dots, top right)
   - Select **"Connections"** or **"Verbindungen"**
   - Click **"+ Add connection"**
   - Select **"Home Assistant Garden"**
   - Click **"Confirm"**
4. Copy the page URL from your browser

### Step 3: Add Integration in Home Assistant

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Notion Garden Care"**
4. Click on it to start the setup

### Step 4: Configuration Flow

#### Screen 1: Notion Token

- Paste your **Notion Integration Token** (from Step 1)
- Click **"Submit"**

#### Screen 2: Database Setup

You have two options:

**Option A: Automatic Setup (Recommended)**
- Paste your **Parent Page URL** (from Step 2)
- Keep **"Create Garden Care database automatically"** checked
- Keep **"Add example plants"** checked to get started with examples
- Click **"Submit"**

The integration will:
- ✅ Create the "Garden Care" database with all properties
- ✅ Set up formula fields for automatic calculations
- ✅ Add 4 example plants (Tomatoes, Rose Bush, Apple Tree, Basil)

**Option B: Use Existing Database**
- Uncheck **"Create Garden Care database automatically"**
- Click **"Submit"**
- On the next screen, paste your existing database URL or ID
- Click **"Submit"**

### Step 5: Verify Installation

After setup, you should see:

1. **New Sensors:**
   - `sensor.notion_garden_care_database` - Raw database data
   - `sensor.plants_to_water` - Plants needing water
   - `sensor.plants_to_fertilize` - Plants needing fertilizer
   - `sensor.plants_to_prune` - Plants to prune this month
   - `sensor.active_plants_count` - Total active plants

2. **New Services:**
   - `notion_garden_care.mark_as_watered`
   - `notion_garden_care.mark_as_fertilized`
   - `notion_garden_care.mark_as_pruned`
   - `notion_garden_care.refresh_database`

---

## 📊 Setup Dashboard (Optional)

### Option 1: Copy Dashboard Configuration

1. Copy the dashboard configuration from `homeassistant/config/dashboard.yaml`
2. Go to **Settings** → **Dashboards**
3. Click your dashboard → **"..."** → **"Edit Dashboard"**
4. Click **"+ Add Card"** → **"Manual"** or **"Raw Configuration Editor"**
5. Paste the YAML configuration
6. Click **"Save"**

### Option 2: Create Cards Manually

Add these cards to your dashboard:

1. **Statistics Glance Card:**
   - Type: Glance
   - Entities: All 4 sensor entities

2. **Conditional Markdown Cards:**
   - For each task type (watering, fertilizing, pruning)
   - Show only when count > 0

---

## 🤖 Setup Automations (Optional)

### Method 1: Use Blueprints (Recommended)

The integration includes blueprints for easy automation setup:

1. Go to **Settings** → **Automations & Scenes**
2. Click **"+ Create Automation"**
3. Select **"Start with a blueprint"**
4. Choose one of:
   - **Garden Care - Watering Reminder**
   - **Garden Care - Fertilizing Reminder**
   - **Garden Care - Pruning Reminder (Monthly)**
5. Configure:
   - Notification time
   - Notification service (e.g., `notify.mobile_app_your_phone`)
   - Custom title if desired
6. Click **"Save"**

### Method 2: Copy Automations

Copy automations from `homeassistant/config/automations.yaml` to your automations.yaml file.

---

## 🔧 Services Usage

### Mark Plant as Watered

```yaml
service: notion_garden_care.mark_as_watered
data:
  plant_name: "Tomatoes"  # or use page_id instead
```

### Mark Plant as Fertilized

```yaml
service: notion_garden_care.mark_as_fertilized
data:
  page_id: "abc123def456"  # or use plant_name instead
```

### Mark Plant as Pruned

```yaml
service: notion_garden_care.mark_as_pruned
data:
  plant_name: "Rose Bush"
```

### Refresh Database

```yaml
service: notion_garden_care.refresh_database
```

---

## 🐛 Troubleshooting

### Integration Not Showing Up

**Problem:** Can't find "Notion Garden Care" in the integrations list

**Solution:**
1. Verify files are in `custom_components/notion_garden_care/`
2. Check `manifest.json` exists and is valid JSON
3. Restart Home Assistant
4. Check logs: **Settings** → **System** → **Logs**

### Sensors Show "Unavailable"

**Problem:** Sensors are unavailable or show no data

**Solution:**
1. Check if the integration is connected in Notion:
   - Open your database in Notion
   - Click **"..."** → **"Connections"**
   - Verify "Home Assistant Garden" is connected
2. Check the Notion token is valid
3. Try refreshing: Call `notion_garden_care.refresh_database`
4. Check Home Assistant logs for API errors

### Database Not Created

**Problem:** Setup completed but no database in Notion

**Solution:**
1. Verify the parent page exists in Notion
2. Check the integration is connected to the parent page
3. Try manual setup with database ID instead

### Permission Errors

**Problem:** "API Error: Unauthorized" or similar

**Solution:**
1. Regenerate the Notion integration token
2. Remove and re-add the integration in Home Assistant
3. Ensure the integration has access to the page/database

---

## 🔄 Updating

### HACS Updates

HACS will notify you when updates are available. Click "Update" to install.

### Manual Updates

```bash
cd /config/notion-garden-care
git pull
cp -r custom_components/notion_garden_care /config/custom_components/
```

Then restart Home Assistant.

---

## ❌ Uninstalling

1. Go to **Settings** → **Devices & Services**
2. Find **"Notion Garden Care"**
3. Click **"..."** → **"Delete"**
4. Remove the integration folder:
   ```bash
   rm -rf /config/custom_components/notion_garden_care
   ```
5. Restart Home Assistant

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/pfalzcraft/notion-garden-care/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pfalzcraft/notion-garden-care/discussions)
- **Documentation:** [README.md](README.md)

---

**Happy Gardening! 🌱**
