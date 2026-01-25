# 📊 Sensor Documentation

Complete guide to understanding how Notion Garden Care sensors work.

## Overview

The integration creates two types of sensors:

1. **Aggregate Sensors (5 sensors)** - Summary sensors that track all plants
2. **Individual Plant Sensors (optional)** - One sensor per plant with all details

All sensors automatically update every hour.

### Configuration Option

During setup, you can choose to enable/disable individual plant sensors:
- **"Create individual sensors for each plant"** - Check to create `sensor.garden_care_<plant_name>` for each plant
- When disabled, only the 5 aggregate sensors are created

---

## 🌱 Individual Plant Sensors

**Sensor ID:** `sensor.garden_care_<plant_name>` (e.g., `sensor.garden_care_tomatoes`)

### When Enabled

Individual plant sensors are created when you check **"Create individual sensors for each plant"** during integration setup.

### State Values

The sensor state shows the current status of the plant:

| State | Meaning |
|-------|---------|
| `OK` | Plant doesn't need any immediate care |
| `Needs Water` | Next Water date is today or in the past |
| `Needs Fertilizer` | Next Fertilize date is today or in the past |
| `Needs Pruning` | Current month is in Prune Months list |
| `Needs Water, Needs Fertilizer` | Multiple care needs (comma-separated) |

### Attributes

Each plant sensor includes ALL properties from Notion as attributes:

```yaml
sensor.garden_care_tomatoes:
  state: "Needs Water"
  attributes:
    page_id: "abc123..."
    plant_name: "Tomatoes"
    type: "Vegetable"
    location: "Garden"
    active: true
    sun_exposure: "Full Sun"
    water_interval_days: 2
    last_watered: "2026-01-23"
    next_water: "2026-01-25"
    water_amount: "High"
    fertilize_interval_days: 14
    last_fertilized: "2026-01-15"
    next_fertilize: "2026-01-29"
    fertilizer_type: "Tomato fertilizer, NPK 5-6-8"
    prune_months: ["March", "September"]
    prune_instructions: "Remove suckers regularly..."
    harvest_months: ["July", "August", "September"]
    harvest_notes: "Pick when fully colored..."
    companion_plants: "Basil, Marigolds, Carrots"
    bee_friendly: true
    toxicity: "Safe"
    care_instructions: "Fertilize regularly..."
    special_notes: "Requires sunny location"
```

### Dynamic Icons

The icon changes based on plant type:

| Plant Type | Icon |
|------------|------|
| Tree | `mdi:tree` |
| Shrub | `mdi:tree-outline` |
| Vegetable | `mdi:carrot` |
| Herb | `mdi:leaf` |
| Lawn | `mdi:grass` |
| Plant (default) | `mdi:flower` |

### Use Cases

**Dashboard Cards:**
```yaml
type: entity
entity: sensor.garden_care_tomatoes
name: Tomatoes
```

**Automation Example:**
```yaml
automation:
  - alias: "Notify when Tomatoes need water"
    trigger:
      - platform: state
        entity_id: sensor.garden_care_tomatoes
        to: "Needs Water"
    action:
      - service: notify.mobile_app
        data:
          title: "Garden Alert"
          message: "Your tomatoes need watering!"
```

---

## Aggregate Sensors

The following 5 sensors are always created:

---

## 🚰 Plants to Water

**Sensor ID:** `sensor.plants_to_water`

### When Plants Appear

A plant appears in this sensor when:
- The **"Next Water"** date (calculated formula) is **today or earlier**
- The plant has valid watering data configured

### How It Works

1. **Notion Formula:** `Next Water = Last Watered + Water Interval (days)`
2. **Sensor Logic:** Compares `Next Water` date to today's date
3. **Condition:** `if next_water_date <= today`

### Examples

| Today's Date | Next Water Date | Shows in Sensor? | Reason |
|--------------|-----------------|------------------|--------|
| 2026-01-25 | 2026-01-24 | ✅ Yes | Water date is yesterday (overdue) |
| 2026-01-25 | 2026-01-25 | ✅ Yes | Water date is today (due now) |
| 2026-01-25 | 2026-01-26 | ❌ No | Water date is tomorrow (not yet due) |
| 2026-01-25 | 2026-01-20 | ✅ Yes | Water date is 5 days ago (very overdue) |

### Sensor Attributes

```yaml
sensor.plants_to_water:
  state: 2  # Number of plants needing water
  attributes:
    plants:
      - "Apple Tree"
      - "Rose Bush"
    plant_details:
      - name: "Apple Tree"
        page_id: "abc123..."
        due_date: "2026-01-24"
      - name: "Rose Bush"
        page_id: "def456..."
        due_date: "2026-01-20"
```

### Troubleshooting

**Problem:** Plant needs water but doesn't show up

**Solutions:**
1. Check that "Last Watered" date is set in Notion
2. Verify "Water Interval (days)" has a number value
3. Confirm "Next Water" formula shows a date (not blank or error)
4. Check formula syntax: `dateAdd(prop("Last Watered"), prop("Water Interval (days)"), "days")`
5. Call service `notion_garden_care.refresh_database` to force update

---

## 🌿 Plants to Fertilize

**Sensor ID:** `sensor.plants_to_fertilize`

### When Plants Appear

A plant appears in this sensor when:
- The **"Next Fertilize"** date (calculated formula) is **today or earlier**
- The plant has valid fertilizing data configured

### How It Works

1. **Notion Formula:** `Next Fertilize = Last Fertilized + Fertilize Interval (days)`
2. **Sensor Logic:** Compares `Next Fertilize` date to today's date
3. **Condition:** `if next_fertilize_date <= today`

### Examples

| Today's Date | Next Fertilize Date | Shows in Sensor? | Reason |
|--------------|---------------------|------------------|--------|
| 2026-01-25 | 2026-01-20 | ✅ Yes | Fertilize date is 5 days ago (overdue) |
| 2026-01-25 | 2026-01-25 | ✅ Yes | Fertilize date is today (due now) |
| 2026-01-25 | 2026-02-10 | ❌ No | Fertilize date is in the future (not yet due) |

### Sensor Attributes

```yaml
sensor.plants_to_fertilize:
  state: 1  # Number of plants needing fertilizer
  attributes:
    plants:
      - "Tomatoes"
    plant_details:
      - name: "Tomatoes"
        page_id: "ghi789..."
        due_date: "2026-01-20"
```

### Troubleshooting

**Problem:** Plant needs fertilizer but doesn't show up

**Solutions:**
1. Check that "Last Fertilized" date is set in Notion
2. Verify "Fertilize Interval (days)" has a number value
3. Confirm "Next Fertilize" formula shows a date
4. Check formula syntax: `dateAdd(prop("Last Fertilized"), prop("Fertilize Interval (days)"), "days")`

---

## ✂️ Plants to Prune

**Sensor ID:** `sensor.plants_to_prune`

### When Plants Appear

A plant appears in this sensor when:
- The **current month name** is in the plant's **"Prune Months"** multi-select field
- Example: If today is January and plant has "January" selected → Plant appears

### How It Works

1. **Get current month:** Convert month number to name (1 → "January")
2. **Check multi-select:** Look for current month in "Prune Months" field
3. **Condition:** `if current_month in prune_months`

### Examples

| Today's Date | Current Month | Prune Months | Shows in Sensor? |
|--------------|---------------|--------------|------------------|
| 2026-01-25 | January | January, March | ✅ Yes |
| 2026-01-25 | January | March, April | ❌ No |
| 2026-03-15 | March | January, March | ✅ Yes |
| 2026-02-10 | February | January, March | ❌ No |

### Important Notes

- **Month-based, not date-based:** Shows all month long (Jan 1-31 if "January" is selected)
- **No "overdue" concept:** Either it's the right month or it isn't
- **Multi-month support:** A plant can have multiple pruning months

### Sensor Attributes

```yaml
sensor.plants_to_prune:
  state: 2  # Number of plants to prune this month
  attributes:
    plants:
      - "Rose Bush"
      - "Apple Tree"
    plant_details:
      - name: "Rose Bush"
        page_id: "jkl012..."
        months: ["February", "March"]
      - name: "Apple Tree"
        page_id: "mno345..."
        months: ["February", "March"]
```

### Troubleshooting

**Problem:** Plant should be pruned this month but doesn't show up

**Solutions:**
1. Check "Prune Months" field has the current month selected
2. Verify month name spelling (must be exactly "January", not "Jan")
3. Refresh sensor data

---

## 🌺 Active Plants Count

**Sensor ID:** `sensor.active_plants_count`

### When Plants Are Counted

A plant is counted when:
- The **"Active"** checkbox is **checked (true)**

### How It Works

1. **Loop through all plants** in the database
2. **Check "Active" checkbox** property
3. **Count:** Increment counter if checkbox is checked

### Examples

| Plant Name | Active Checkbox | Counted? |
|------------|-----------------|----------|
| Tomatoes | ✅ Checked | ✅ Yes |
| Rose Bush | ✅ Checked | ✅ Yes |
| Dead Plant | ❌ Unchecked | ❌ No |
| Removed Tree | ❌ Unchecked | ❌ No |

**Result:** If you have 10 plants total but 2 are marked inactive → Sensor shows **8**

### Use Cases

- Track only plants you're currently caring for
- Exclude dead, removed, or dormant plants from counts
- Get accurate statistics for your active garden

### Sensor State

```yaml
sensor.active_plants_count:
  state: 8  # Number of active plants
```

---

## 🗄️ Notion Garden Care Database

**Sensor ID:** `sensor.notion_garden_care_database`

### What It Shows

- **State:** Total number of **all plants** in the database (no filtering)
- **Attributes:** Full raw data from all Notion database entries

### How It Works

1. **Query Notion API:** Fetch all pages from the database
2. **Count:** Return total number of results
3. **No filtering:** All plants counted regardless of active status

### Sensor State

```yaml
sensor.notion_garden_care_database:
  state: 10  # Total plants in database
  attributes:
    results: [...]  # Full Notion data (may be truncated if too large)
    has_more: false
```

### Important Notes

- **May show warning:** "State attributes exceed maximum size" if you have many plants
- **This is normal:** Home Assistant limits attribute size to prevent database issues
- **Data still accessible:** Through the Notion API and other sensors

---

## ⏱️ Update Frequency

All sensors update automatically **every 60 minutes (1 hour)**.

### Manual Refresh

Force an immediate update anytime:

```yaml
service: notion_garden_care.refresh_database
```

Or use Developer Tools → Services → `notion_garden_care.refresh_database` → Call Service

---

## 🔧 Advanced: Formula Field Structure

Understanding the Notion API response format for formulas:

### Date Formula Response

```json
{
  "Next Water": {
    "type": "formula",
    "formula": {
      "type": "date",
      "date": {
        "start": "2026-01-25",
        "end": null,
        "time_zone": null
      }
    }
  }
}
```

### What the Sensor Extracts

1. Check `formula.type == "date"`
2. Extract `formula.date.start`
3. Compare to today's date string

### String Formula Response (Error Case)

If the formula is invalid or has missing data:

```json
{
  "Next Water": {
    "type": "formula",
    "formula": {
      "type": "string",
      "string": null
    }
  }
}
```

**Result:** Plant will not appear in sensor (formula type is "string", not "date")

---

## 📝 Summary Table

| Sensor | Logic Type | Updates When | Example |
|--------|-----------|--------------|---------|
| Plants to Water | Date comparison | Next Water ≤ Today | Due yesterday → Shows |
| Plants to Fertilize | Date comparison | Next Fertilize ≤ Today | Due 5 days ago → Shows |
| Plants to Prune | Month matching | Current month in list | January in ["Jan", "Mar"] → Shows |
| Active Plants Count | Checkbox check | Active = true | Checked → Counted |
| Database | Total count | Always | All plants counted |

---

## 🐛 Common Issues

### Issue: Sensor shows 0 but plants need care

**Cause:** Formula fields not calculating correctly in Notion

**Fix:**
1. Open plant in Notion
2. Check "Next Water" / "Next Fertilize" shows a date (not blank)
3. If blank, verify "Last Watered" and "Water Interval" have values
4. Re-check formula syntax in database properties

### Issue: Sensors not updating

**Cause:** Update coordinator not refreshing

**Fix:**
1. Call `notion_garden_care.refresh_database` service
2. Restart Home Assistant
3. Check Home Assistant logs for errors

### Issue: Date comparison seems wrong

**Cause:** Timezone differences or date format issues

**Fix:**
- Sensors use system date in format `YYYY-MM-DD`
- Notion formulas should output same format
- Check Notion workspace timezone settings

---

**Need help?** [Open an issue](https://github.com/pfalzcraft/notion-garden-care/issues)
