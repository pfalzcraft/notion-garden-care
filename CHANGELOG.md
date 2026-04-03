# Changelog

All notable changes to the Notion Garden Care integration will be documented in this file.

## [1.9.0] - 2026-04-03

### Fixed
- **Integration setup failing on first step**: Token validation now uses the `/users/me` endpoint instead of `search`, which could fail for fresh integrations that haven't yet been connected to any Notion pages. Setup now works reliably for brand new integrations. (Fixes #2, #3)

### Changed
- **AI plant addition is now location-aware**: When adding a plant via AI, the integration automatically reads your Home Assistant system settings (coordinates, elevation, country, timezone) and passes them to the AI. Advice is now tailored to your local climate, correct hemisphere, and growing season — watering intervals, pruning months, harvest months, hardiness zone, and winterize flag are all adjusted accordingly. No manual location input required. (Fixes #4)
- **Location field left blank on AI plant creation**: The `Location` field in Notion (e.g. "Back garden", "Kitchen windowsill") is no longer auto-filled by AI — this is personal information only you know. Fill it in manually after adding a plant.

### Documentation
- Updated Quick Start **Step 2** in README and INSTALLATION.md to reflect the current Notion integration creation UI, which now requires selecting a workspace and enabling content capabilities (Read, Update, Insert). (Fixes #1, #3)
- README Step 5 updated to document location-aware AI behaviour and the manual Location field expectation.

---

## [1.8.2] - 2026-03-01

### Changed
- **Location is now a free-text field** instead of a fixed dropdown. You can now enter any location description (e.g. "Back garden bed 3", "South-facing balcony", "Kitchen windowsill") instead of being limited to Garden / Balcony / Terrace / Conservatory / Indoor.
  - On startup the integration automatically converts the existing `Location` select column to a text column in your Notion database.
  - AI-added plants will now receive a descriptive location text rather than a fixed category.

---

## [1.8.1] - 2026-03-01

### Fixed
- **Database migration not running**: The auto-migration introduced in 1.8.0 used the `notion_client` library for `databases.update`, which did not apply changes correctly. Rewritten to use `httpx` directly (consistent with all other API calls in the integration). The `"type"` key is now stripped from property specs as required by the Notion PATCH API. Error logging upgraded from `WARNING` to `ERROR` with full traceback for easier diagnosis.

---

## [1.8.0] - 2026-03-01

### Added
- **Plant Date field**: New `Plant Date` date property to record when a plant was planted
- **Additional Information field**: New `Additional Information` rich-text property for any extra notes the user wants to track per plant
- **Delete Plant action**: New `delete_plant` service/action to remove a plant from the Notion database by selecting its sensor entity — moves the Notion page to trash and removes the corresponding HA sensor automatically
- **Automatic database migration**: On every startup the integration now checks whether the Notion database contains all required columns and adds any that are missing (including the two new fields above). Existing databases are upgraded automatically without any manual steps.

### Changed
- `update_plant_property` action now lists `Plant Date` and `Additional Information` in the property selector
- Both new fields are included in individual plant sensor attributes (`plant_date`, `additional_information`)

---

## [1.7.0] - 2026-02-01

### Changed
- **Documentation Updates**: Improved Quick Start guide
  - Added Step 1: Create a Notion account (for new users)
  - Added Step 5: Configure AI Agent (optional but recommended)
  - Added "Verify Resources" troubleshooting section
- **Terminology Update**: Updated documentation to use "actions" instead of "services" (Home Assistant 2024+ terminology)
  - Button examples now use `perform-action` syntax
  - Developer Tools references updated

### Fixed
- **Repository Cleanup**: Removed test files and folders from git tracking
  - Removed `homeassistant/config/` test files
  - Updated `.gitignore` to exclude test scripts and Docker config folders

---

## [1.6.2] - 2026-02-01

### Changed
- **Automatic Dashboard Creation**: The dashboard is now created automatically - no manual setup required
  - Creates both the YAML config file and the dashboard registry entry
  - Dashboard appears in the sidebar immediately after integration setup
  - Uses HA's lovelace API with fallback to direct storage file creation
  - Dismisses any setup notification automatically when dashboard is created

### Fixed
- **Blocking Call Warnings**: Fixed warnings about blocking calls in the event loop
  - Moved directory scanning to executor thread
  - Moved Notion client initialization to executor thread
- **HA 2026.2 Compatibility**: Fixed deprecation warning for lovelace data access
- **Database Sensor Size**: Fixed "State attributes exceed maximum size of 16384 bytes" warning
  - Database sensor now stores only summary data instead of full raw Notion API response
  - Includes plant names, types, active status, and page IDs

---

## [1.6.1] - 2026-01-31

### Changed
- **Dashboard Setup**: The integration no longer auto-creates the dashboard entry (which caused issues with HA's internal state). Instead, it:
  - Creates the `garden-care.yaml` configuration file automatically
  - Shows a persistent notification with setup instructions
  - Users need to manually add the dashboard once via Settings → Dashboards → Add Dashboard (YAML mode)
- This change ensures the dashboard works reliably across all HA installations

### Fixed
- **Dashboard Strategy**: Fixed issue where auto-created dashboard would show "original-states" instead of the custom strategy
- Cleans up old `garden-care-dashboard.yaml` and `lovelace.garden-care` files from previous versions

---

## [1.6.0] - 2026-01-31

### Fixed
- **Custom Element Registration**: Fixed "already been used with this registry" error that prevented the dashboard strategy and cards from loading
- Both `garden-care-strategy.js` and `plant-care-card.js` now check if elements are already registered before defining them
- This fixes issues when the JS files are loaded multiple times (e.g., after hot reload or navigation)

---

## [1.5.1] - 2026-01-31

### Fixed
- **Dashboard Upgrade Fix**: Fixed issue where upgrading from older versions would keep the old "original-states" dashboard instead of switching to the new YAML-based strategy
- The integration now automatically deletes the old `lovelace.garden-care` storage file on startup to ensure clean upgrades

### Added
- **Integration Icons**: Added `icon.png`, `icon@2x.png`, and `logo.png` for better branding in Home Assistant UI

---

## [1.5.0] - 2026-01-31

### Added
- **Lawn Mowing Tracking**: New `mark_as_mowed` service for lawn care
- **Last Mowed**: New date property in database schema for lawns
- **Care Instruction URLs**: AI-generated plants now include URLs to care guides
  - `Care Instructions URL` - General care guide link
  - `Prune Instructions URL` - Pruning guide link
  - `Harvest Instructions URL` - Harvesting guide link
- **Visual Button Feedback**: Action buttons now show loading/success/error states
- **Last Action Dates**: Plant cards now display both "Next" and "Last" dates for each care task

### Changed
- **Simplified Dashboard**: Garden Care dashboard now uses a single clean view with just the Add Plant form and plant cards (removed Overview view)
- **Dashboard Mode**: Changed from storage mode to YAML mode for more reliable strategy loading
- **Conditional Care Rows**: Prune and Harvest rows only appear on plant cards if the plant has those months defined
- **Harvest Button**: Added dedicated "Harvested" action button to plant cards

### Fixed
- **Plant Creation**: Fixed issue where adding new plants via AI would fail if the database didn't have URL properties
- **Graceful Fallback**: Plant creation now automatically retries without URL properties for older databases
- **Dashboard Strategy**: Fixed issue where dashboard would use "original-states" instead of "custom:garden-care" strategy

### Technical
- Improved error logging for plant creation debugging
- Added fallback mechanism for URL properties in `_create_plant_in_notion`
- Dashboard now uses YAML config file (`garden-care-dashboard.yaml`) for reliable strategy loading
- Bumped frontend version to 1.5.0 for cache busting

## [1.4.0] - 2026-01-25

### Added
- Initial public release
- Notion database auto-creation
- Individual plant sensors
- Aggregate sensors (plants to water, fertilize, prune)
- AI-powered plant addition
- Custom plant care cards
- Auto-generated dashboard with strategy
- Services: mark_as_watered, mark_as_fertilized, mark_as_pruned, mark_as_harvested, mark_as_aerated, mark_as_sanded
- Extended plant properties (lifecycle, hardiness zone, soil type, etc.)

---

For more information, see the [README](README.md).
