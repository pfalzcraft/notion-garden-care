"""Constants for the Notion Garden Care integration."""

DOMAIN = "notion_garden_care"

# Configuration
CONF_NOTION_TOKEN = "notion_token"
CONF_PARENT_PAGE_ID = "parent_page_id"
CONF_DATABASE_ID = "database_id"
CONF_CREATE_DATABASE = "create_database"
CONF_ADD_EXAMPLES = "add_example_plants"
CONF_CREATE_PLANT_SENSORS = "create_plant_sensors"
CONF_CONVERSATION_AGENT = "conversation_agent"

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
SERVICE_UPDATE_SANDED = "mark_as_sanded"
SERVICE_UPDATE_MOWED = "mark_as_mowed"
SERVICE_UPDATE_PROPERTY = "update_plant_property"
SERVICE_REFRESH_DATA = "refresh_database"
SERVICE_ADD_PLANT = "add_plant"

# Attributes
ATTR_PAGE_ID = "page_id"
ATTR_PLANT_NAME = "plant_name"
ATTR_PROPERTY_NAME = "property_name"
ATTR_PROPERTY_VALUE = "property_value"
ATTR_DATE = "date"
ATTR_ENTITY_ID = "entity_id"

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

# Lifecycle (Perennial/Annual)
LIFECYCLE = ["Perennial", "Annual", "Biennial"]

# Hardiness Zones
HARDINESS_ZONES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]

# Soil Types
SOIL_TYPES = ["Sandy", "Loamy", "Clay", "Silty", "Peaty", "Chalky", "Any"]

# Soil pH
SOIL_PH = ["Acidic (pH < 6)", "Neutral (pH 6-7)", "Alkaline (pH > 7)", "Any"]

# Additional Database Properties
PROPERTY_SUN_EXPOSURE = "Sun Exposure"
PROPERTY_HARVEST_MONTHS = "Harvest Months"
PROPERTY_HARVEST_NOTES = "Harvest Notes"
PROPERTY_COMPANION_PLANTS = "Companion Plants"
PROPERTY_BAD_COMPANIONS = "Bad Companions"
PROPERTY_BEE_FRIENDLY = "Bee Friendly"
PROPERTY_TOXICITY = "Toxicity"
PROPERTY_AERATION_INTERVAL = "Aeration Interval (days)"
PROPERTY_LAST_AERATION = "Last Aeration"
PROPERTY_NEXT_AERATION = "Next Aeration"
PROPERTY_LAST_HARVESTED = "Last Harvested"
PROPERTY_SANDING_INTERVAL = "Sanding Interval (days)"
PROPERTY_LAST_SANDED = "Last Sanded"
PROPERTY_NEXT_SANDING = "Next Sanding"
PROPERTY_LIFECYCLE = "Lifecycle"
PROPERTY_HARDINESS_ZONE = "Hardiness Zone"
PROPERTY_SOIL_TYPE = "Soil Type"
PROPERTY_SOIL_PH = "Soil pH"
PROPERTY_GROWTH_PER_YEAR = "Growth per Year"
PROPERTY_HEIGHT = "Height"
PROPERTY_WINTERIZE = "Winterize"

# All updatable properties (for service dropdown) - organized by category
UPDATABLE_PROPERTIES = [
    # ── Basic Info ──
    "Type",
    "Location",
    "Active",
    "Lifecycle",
    # ── Plant Characteristics ──
    "Height",
    "Growth per Year",
    "Hardiness Zone",
    # ── Environment ──
    "Sun Exposure",
    "Soil Type",
    "Soil pH",
    # ── Watering ──
    "Water Interval (days)",
    "Last Watered",
    "Water Amount",
    # ── Fertilizing ──
    "Fertilize Interval (days)",
    "Last Fertilized",
    "Fertilizer Type",
    # ── Pruning ──
    "Prune Months",
    "Last Pruned",
    "Prune Instructions",
    # ── Harvest ──
    "Harvest Months",
    "Last Harvested",
    "Harvest Notes",
    # ── Lawn Care ──
    "Aeration Interval (days)",
    "Last Aeration",
    "Sanding Interval (days)",
    "Last Sanded",
    # ── Companions & Safety ──
    "Companion Plants",
    "Bad Companions",
    "Bee Friendly",
    "Toxicity",
    "Winterize",
    # ── Notes ──
    "Care Instructions",
    "Special Notes",
    "Notes",
]

# Example Plants - properties organized by category
EXAMPLE_PLANTS = [
    {
        # ── Basic Info ──
        "Name": "Tomatoes",
        "Type": "Vegetable",
        "Location": "Garden",
        "Active": True,
        "Lifecycle": "Annual",
        # ── Plant Characteristics ──
        "Height": "1-2m (3-6ft)",
        "Growth per Year": "Full growth in one season",
        "Hardiness Zone": "10",
        # ── Environment ──
        "Sun Exposure": "Full Sun",
        "Soil Type": "Loamy",
        "Soil pH": "Neutral (pH 6-7)",
        # ── Watering ──
        "Water Interval (days)": 2,
        "Water Amount": "High",
        # ── Fertilizing ──
        "Fertilize Interval (days)": 14,
        "Fertilizer Type": "Tomato fertilizer, NPK 5-6-8",
        # ── Pruning ──
        "Prune Months": ["March", "September"],
        "Prune Instructions": "Remove suckers regularly. Cut back to ground level after harvest.",
        # ── Harvest ──
        "Harvest Months": ["July", "August", "September"],
        "Harvest Notes": "Pick when fully colored and slightly soft. Harvest regularly to encourage more fruit.",
        # ── Companions & Safety ──
        "Companion Plants": "Basil, Marigolds, Carrots",
        "Bad Companions": "Brassicas, Fennel, Corn",
        "Bee Friendly": True,
        "Toxicity": "Safe",
        "Winterize": False,
        # ── Notes ──
        "Care Instructions": "Fertilize regularly and water sufficiently. Provide support.",
        "Special Notes": "Requires sunny location",
    },
    {
        # ── Basic Info ──
        "Name": "Rose Bush",
        "Type": "Plant",
        "Location": "Garden",
        "Active": True,
        "Lifecycle": "Perennial",
        # ── Plant Characteristics ──
        "Height": "1-2m (3-6ft)",
        "Growth per Year": "30-60cm (1-2ft)",
        "Hardiness Zone": "5",
        # ── Environment ──
        "Sun Exposure": "Full Sun",
        "Soil Type": "Loamy",
        "Soil pH": "Neutral (pH 6-7)",
        # ── Watering ──
        "Water Interval (days)": 7,
        "Water Amount": "Medium",
        # ── Fertilizing ──
        "Fertilize Interval (days)": 30,
        "Fertilizer Type": "Rose fertilizer",
        # ── Pruning ──
        "Prune Months": ["February", "March"],
        "Prune Instructions": "Cut back to 3-5 buds in spring. Remove weak and diseased shoots.",
        # ── Companions & Safety ──
        "Companion Plants": "Lavender, Geraniums, Garlic",
        "Bad Companions": "Buxus, other roses too close",
        "Bee Friendly": True,
        "Toxicity": "Toxic to Pets",
        "Winterize": True,
        # ── Notes ──
        "Care Instructions": "Remove spent blooms after flowering",
        "Special Notes": "Frost-sensitive, protect in winter",
    },
    {
        # ── Basic Info ──
        "Name": "Apple Tree",
        "Type": "Tree",
        "Location": "Garden",
        "Active": True,
        "Lifecycle": "Perennial",
        # ── Plant Characteristics ──
        "Height": "3-5m (10-16ft)",
        "Growth per Year": "30-60cm (1-2ft)",
        "Hardiness Zone": "4",
        # ── Environment ──
        "Sun Exposure": "Full Sun",
        "Soil Type": "Loamy",
        "Soil pH": "Neutral (pH 6-7)",
        # ── Watering ──
        "Water Interval (days)": 14,
        "Water Amount": "High",
        # ── Fertilizing ──
        "Fertilize Interval (days)": 90,
        "Fertilizer Type": "Fruit tree fertilizer",
        # ── Pruning ──
        "Prune Months": ["February", "March"],
        "Prune Instructions": "Thinning cut: Remove diseased, inward-growing and crossing branches.",
        # ── Harvest ──
        "Harvest Months": ["September", "October"],
        "Harvest Notes": "Apples are ready when they come off easily with a gentle twist.",
        # ── Companions & Safety ──
        "Companion Plants": "Chives, Nasturtiums, Clover",
        "Bad Companions": "Walnut, Grass close to trunk",
        "Bee Friendly": True,
        "Toxicity": "Safe (seeds contain cyanide - don't eat in large quantities)",
        "Winterize": False,
        # ── Notes ──
        "Care Instructions": "Check regularly for pests",
        "Special Notes": "Needs pollinator nearby",
    },
    {
        # ── Basic Info ──
        "Name": "Basil",
        "Type": "Herb",
        "Location": "Balcony",
        "Active": True,
        "Lifecycle": "Annual",
        # ── Plant Characteristics ──
        "Height": "30-60cm (1-2ft)",
        "Growth per Year": "Full growth in one season",
        "Hardiness Zone": "10",
        # ── Environment ──
        "Sun Exposure": "Full Sun",
        "Soil Type": "Loamy",
        "Soil pH": "Neutral (pH 6-7)",
        # ── Watering ──
        "Water Interval (days)": 3,
        "Water Amount": "Medium",
        # ── Fertilizing ──
        "Fertilize Interval (days)": 21,
        "Fertilizer Type": "Liquid fertilizer for herbs",
        # ── Pruning ──
        "Prune Months": ["May", "June", "July", "August"],
        "Prune Instructions": "Harvest leaves regularly to encourage branching. Remove flowers.",
        # ── Harvest ──
        "Harvest Months": ["June", "July", "August", "September"],
        "Harvest Notes": "Pick leaves in the morning for best flavor. Use fresh or dry for storage.",
        # ── Companions & Safety ──
        "Companion Plants": "Tomatoes, Peppers",
        "Bad Companions": "Sage, Rue",
        "Bee Friendly": True,
        "Toxicity": "Safe",
        "Winterize": False,
        # ── Notes ──
        "Care Instructions": "Keep warm and sunny, not too wet",
        "Special Notes": "Not winter-hardy, harvest in autumn",
    },
    {
        # ── Basic Info ──
        "Name": "Lawn",
        "Type": "Lawn",
        "Location": "Garden",
        "Active": True,
        "Lifecycle": "Perennial",
        # ── Plant Characteristics ──
        "Height": "5-10cm (2-4in)",
        "Growth per Year": "Continuous growth during season",
        "Hardiness Zone": "3",
        # ── Environment ──
        "Sun Exposure": "Partial Sun",
        "Soil Type": "Loamy",
        "Soil pH": "Neutral (pH 6-7)",
        # ── Watering ──
        "Water Interval (days)": 3,
        "Water Amount": "Medium",
        # ── Fertilizing ──
        "Fertilize Interval (days)": 60,
        "Fertilizer Type": "Lawn fertilizer, NPK 20-5-10",
        # ── Lawn Care ──
        "Aeration Interval (days)": 365,
        "Sanding Interval (days)": 365,
        # ── Companions & Safety ──
        "Winterize": False,
        # ── Notes ──
        "Care Instructions": "Mow regularly, keep at 3-4 inches height. Water deeply but infrequently.",
        "Special Notes": "Aerate and sand annually in spring or fall. Overseed bare patches.",
    }
]
