# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands must be run from `scripts/` with the Poetry venv activated (`.venv/`):

```powershell
# Activate venv
D:\Projects\prague_home\.venv\Scripts\Activate.ps1

# Run the full ETL pipeline (scrape → enrich → score → save)
cd scripts
python -m pipeline

# Launch the Dash web app
python app.py
```

Dependencies are managed with Poetry:
```powershell
poetry install   # install all deps
```

There are no tests or linters configured.

## Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `PragueHouseGMAPKey` | Google Maps API key (geocoding, directions, Places) |
| `MPBOX_PUBLIC_KEY` | Mapbox token for the route map in the Dash app |

## Architecture

The project is a Prague rental-property ranking tool with two runtime modes: a **pipeline** that collects and scores data, and a **Dash app** that visualises it.

### Data flow

```
data/search_urls.txt
        │
        ▼
Webscraper.get_units_urls()          ← Selenium + GDPR consent acceptance
        │  /en/detail/... URL list
        ▼
Webscraper.extract_units_details()   ← requests + __NEXT_DATA__ SSR parsing
        │  raw DataFrame
        ▼
Gmaps._get_home_location()           ← geocodes Address → (lat, lng)
Gmaps.get_nearest_poi()              ← Places API → nearest Shop/tram/etc coords
Gmaps.journey_details()              ← Directions API → dur/dist/walk per POI × mode
Gmaps.get_school_journey_details()   ← Directions API → school travel times
Gmaps.get_closest_crossfitbox()      ← Directions API → nearest crossfit box
        │  enriched DataFrame
        ▼
Preprocess.clean_lst_columns()       ← unwrap nested-list columns (elevator, etc.)
Preprocess.clean_data_format()       ← fillna(0) on journey columns, to_numeric
        │
        ▼
Score.get_score()                    ← weighted scoring across 4 categories
        │
        ▼
data/data.pkl                        ← pickled DataFrame, loaded by app.py
```

### Scoring weights (`score.py`)

| Category | Weight | Key columns |
|----------|--------|-------------|
| School transit time | 0.50 | `school_transit_dur`, `school_transit_twalk` |
| Nearest crossfit box | 0.05 | `crossfit_mode`, `crossfit_dur` |
| 7 nearby POIs (walking) | 0.25 | `{place}_walking_dur` for each in `nearby_places.txt` |
| Unit details | 0.20 | `bedrooms`, `usable_area`, `energy_class` |

Score thresholds are hardcoded in `score.py`. All four components return `(score, score_dict)` tuples; `score_dict` is stored per-row in `data.pkl` and used by the app's waterfall chart.

### Key design constraints

- **Working directory matters**: `pipeline.py`, `gmaps.py`, and `app.py` all resolve data files with relative paths from `scripts/` (e.g. `../data/data.pkl`). Always run from `scripts/`.
- **GDPR consent wall**: sreality.cz redirects headless Chrome to `cmp.seznam.cz`. `Webscraper.get_units_urls()` detects the redirect and clicks the "Agree" button in the `SZN-CWL` shadow DOM, then saves the resulting consent cookies to `self.consent_cookies` for use by `_fetch_estate_ssr()`.
- **SSR parsing**: Detail page data is extracted from the `__NEXT_DATA__` JSON embedded in each page's HTML (React Query `dehydratedState`, query key `"estate"`). The old `/api/cs/v2/estates` API is dead; the new `/api/v1/` requires auth.
- **POI coordinates**: `extendedPois` in the new sreality API is a list of category strings, not lat/lon dicts. `Gmaps.get_nearest_poi()` uses the Google Maps Places API (`places_nearby`) to find real coordinates; `PLACE_TYPE_MAP` in `gmaps.py` maps the 7 category names to Google Places types.
- **`Preprocess` stale-reference gotcha**: `Pipeline.__init__` creates `self.preprocess = Preprocess(self.data)` before data is scraped. `preprocess_data()` must sync `self.preprocess.data = self.data` before calling any clean method.

### Data files (`data/`)

| File | Purpose |
|------|---------|
| `search_urls.txt` | One search URL per line, fed to the pipeline |
| `nearby_places.txt` | Comma-separated POI category names (`Shop,Playground,tram,...`) — drives column generation |
| `school_address.txt` | Target school coordinates as a Python tuple literal |
| `crossfit.pkl` | DataFrame with `name` and `geo` columns for Prague crossfit gyms |
| `data.pkl` | Pipeline output; loaded at startup by `app.py` |
