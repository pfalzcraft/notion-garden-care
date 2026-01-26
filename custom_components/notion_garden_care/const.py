"""Constants for the Notion Garden Care integration."""

DOMAIN = "notion_garden_care"

# Configuration
CONF_NOTION_TOKEN = "notion_token"
CONF_PARENT_PAGE_ID = "parent_page_id"
CONF_DATABASE_ID = "database_id"
CONF_CREATE_DATABASE = "create_database"
CONF_ADD_EXAMPLES = "add_example_plants"
CONF_CREATE_PLANT_SENSORS = "create_plant_sensors"

# Notion API
NOTION_API_VERSION = "2022-06-28"
NOTION_API_URL = "https://api.notion.com/v1"

# Scan interval (in seconds)
SCAN_INTERVAL = 3600  # 1 hour

# Services
SERVICE_UPDATE_WATERED = "mark_as_watered"
SERVICE_UPDATE_FERTILIZED = "mark_as_fertilized"
SERVICE_UPDATE_PRUNED = "mark_as_pruned"
SERVICE_UPDATE_AERATED = "mark_as_aerated"
SERVICE_UPDATE_HARVESTED = "mark_as_harvested"
SERVICE_UPDATE_PROPERTY = "update_plant_property"
SERVICE_REFRESH_DATA = "refresh_database"

# Attributes
ATTR_PAGE_ID = "page_id"
ATTR_PLANT_NAME = "plant_name"
ATTR_PROPERTY_NAME = "property_name"
ATTR_PROPERTY_VALUE = "property_value"
ATTR_DATE = "date"

# Database Properties
PROPERTY_NAME = "Name"
PROPERTY_TYPE = "Type"
PROPERTY_LOCATION = "Location"
PROPERTY_ACTIVE = "Active"
PROPERTY_WATER_INTERVAL = "Water Interval (days)"
PROPERTY_LAST_WATERED = "Last Watered"
PROPERTY_NEXT_WATER = "Next Water"
PROPERTY_WATER_AMOUNT = "Water Amount"
PROPERTY_FERTILIZE_INTERVAL = "Fertilize Interval (days)"
PROPERTY_LAST_FERTILIZED = "Last Fertilized"
PROPERTY_NEXT_FERTILIZE = "Next Fertilize"
PROPERTY_FERTILIZER_TYPE = "Fertilizer Type"
PROPERTY_PRUNE_MONTHS = "Prune Months"
PROPERTY_PRUNE_INSTRUCTIONS = "Prune Instructions"
PROPERTY_LAST_PRUNED = "Last Pruned"
PROPERTY_CARE_INSTRUCTIONS = "Care Instructions"
PROPERTY_SPECIAL_NOTES = "Special Notes"
PROPERTY_NOTES = "Notes"

# Plant Types
PLANT_TYPES = ["Plant", "Tree", "Shrub", "Vegetable", "Herb", "Lawn"]

# Locations
LOCATIONS = ["Garden", "Balcony", "Terrace", "Conservatory", "Indoor"]

# Water Amounts
WATER_AMOUNTS = ["Low", "Medium", "High"]

# Sun Exposure
SUN_EXPOSURE = ["Full Sun", "Partial Sun", "Partial Shade", "Full Shade"]

# Months
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Toxicity Levels
TOXICITY = ["Safe", "Toxic to Pets", "Toxic to Children", "Toxic to Both"]

# Additional Database Properties
PROPERTY_SUN_EXPOSURE = "Sun Exposure"
PROPERTY_HARVEST_MONTHS = "Harvest Months"
PROPERTY_HARVEST_NOTES = "Harvest Notes"
PROPERTY_COMPANION_PLANTS = "Companion Plants"
PROPERTY_BEE_FRIENDLY = "Bee Friendly"
PROPERTY_TOXICITY = "Toxicity"
PROPERTY_AERATION_INTERVAL = "Aeration Interval (days)"
PROPERTY_LAST_AERATION = "Last Aeration"
PROPERTY_NEXT_AERATION = "Next Aeration"

# Example Plants
EXAMPLE_PLANTS = [
    {
        "Name": "Tomatoes",
        "Type": "Vegetable",
        "Location": "Garden",
        "Active": True,
        "Sun Exposure": "Full Sun",
        "Fertilize Interval (days)": 14,
        "Fertilizer Type": "Tomato fertilizer, NPK 5-6-8",
        "Water Interval (days)": 2,
        "Water Amount": "High",
        "Prune Months": ["March", "September"],
        "Prune Instructions": "Remove suckers regularly. Cut back to ground level after harvest.",
        "Harvest Months": ["July", "August", "September"],
        "Harvest Notes": "Pick when fully colored and slightly soft. Harvest regularly to encourage more fruit.",
        "Companion Plants": "Basil, Marigolds, Carrots",
        "Bee Friendly": True,
        "Toxicity": "Safe",
        "Care Instructions": "Fertilize regularly and water sufficiently. Provide support.",
        "Special Notes": "Requires sunny location"
    },
    {
        "Name": "Rose Bush",
        "Type": "Plant",
        "Location": "Garden",
        "Active": True,
        "Sun Exposure": "Full Sun",
        "Fertilize Interval (days)": 30,
        "Fertilizer Type": "Rose fertilizer",
        "Water Interval (days)": 7,
        "Water Amount": "Medium",
        "Prune Months": ["February", "March"],
        "Prune Instructions": "Cut back to 3-5 buds in spring. Remove weak and diseased shoots.",
        "Companion Plants": "Lavender, Geraniums, Garlic",
        "Bee Friendly": True,
        "Toxicity": "Toxic to Pets",
        "Care Instructions": "Remove spent blooms after flowering",
        "Special Notes": "Frost-sensitive, protect in winter"
    },
    {
        "Name": "Apple Tree",
        "Type": "Tree",
        "Location": "Garden",
        "Active": True,
        "Sun Exposure": "Full Sun",
        "Fertilize Interval (days)": 90,
        "Fertilizer Type": "Fruit tree fertilizer",
        "Water Interval (days)": 14,
        "Water Amount": "High",
        "Prune Months": ["February", "March"],
        "Prune Instructions": "Thinning cut: Remove diseased, inward-growing and crossing branches.",
        "Harvest Months": ["September", "October"],
        "Harvest Notes": "Apples are ready when they come off easily with a gentle twist.",
        "Bee Friendly": True,
        "Toxicity": "Safe (seeds contain cyanide - don't eat in large quantities)",
        "Care Instructions": "Check regularly for pests",
        "Special Notes": "Needs pollinator nearby"
    },
    {
        "Name": "Basil",
        "Type": "Herb",
        "Location": "Balcony",
        "Active": True,
        "Sun Exposure": "Full Sun",
        "Fertilize Interval (days)": 21,
        "Fertilizer Type": "Liquid fertilizer for herbs",
        "Water Interval (days)": 3,
        "Water Amount": "Medium",
        "Prune Months": ["May", "June", "July", "August"],
        "Prune Instructions": "Harvest leaves regularly to encourage branching. Remove flowers.",
        "Harvest Months": ["June", "July", "August", "September"],
        "Harvest Notes": "Pick leaves in the morning for best flavor. Use fresh or dry for storage.",
        "Companion Plants": "Tomatoes, Peppers",
        "Bee Friendly": True,
        "Toxicity": "Safe",
        "Care Instructions": "Keep warm and sunny, not too wet",
        "Special Notes": "Not winter-hardy, harvest in autumn"
    },
    {
        "Name": "Lawn",
        "Type": "Lawn",
        "Location": "Garden",
        "Active": True,
        "Sun Exposure": "Partial Sun",
        "Fertilize Interval (days)": 60,
        "Fertilizer Type": "Lawn fertilizer, NPK 20-5-10",
        "Water Interval (days)": 3,
        "Water Amount": "Medium",
        "Aeration Interval (days)": 365,
        "Care Instructions": "Mow regularly, keep at 3-4 inches height. Water deeply but infrequently.",
        "Special Notes": "Aerate annually in spring or fall. Overseed bare patches."
    }
]
