/** Stable map-layer identifiers shared by the API (/map/layers) and the web layer manager. */
export const MAP_LAYER_IDS = {
  FEMA_FLOOD_ZONES: "fema-flood-zones",
  NOAA_ALERTS: "noaa-alerts",
  HURRICANE_TRACKS: "hurricane-tracks",
  USGS_WATER_STATIONS: "usgs-water-stations",
  SFWMD_STATIONS: "sfwmd-stations",
  SJRWMD_STATIONS: "sjrwmd-stations",
  SWFWMD_STATIONS: "swfwmd-stations",
  COUNTY_RISK_HEATMAP: "county-risk-heatmap",
  PROCUREMENT_LOCATIONS: "procurement-locations",
  COUNTY_BOUNDARIES: "county-boundaries",
} as const;

export type MapLayerId = (typeof MAP_LAYER_IDS)[keyof typeof MAP_LAYER_IDS];
