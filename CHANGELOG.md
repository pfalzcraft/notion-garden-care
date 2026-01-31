# Changelog

All notable changes to the Notion Garden Care integration will be documented in this file.

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
