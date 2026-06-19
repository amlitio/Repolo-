/** Centralized React Query key factory - keeps cache invalidation consistent across hooks. */
export const queryKeys = {
  session: () => ["session"] as const,
  orgs: () => ["orgs"] as const,
  rbacMe: () => ["rbac-me"] as const,
  mapLayers: () => ["map-layers"] as const,
  mapFeatures: (layerId: string, bbox: [number, number, number, number], zoom?: number) =>
    ["map-features", layerId, bbox.join(","), zoom] as const,
  mapSearch: (q: string) => ["map-search", q] as const,
  waterStations: (countyFips?: string, sourceId?: string) =>
    ["water-stations", countyFips, sourceId] as const,
  waterObservations: (stationId?: string, parameter?: string) =>
    ["water-observations", stationId, parameter] as const,
  waterSummary: (countyFips: string) => ["water-summary", countyFips] as const,
  floodZones: (countyFips?: string) => ["flood-zones", countyFips] as const,
  propertyRisk: (address?: string, propertyId?: string) =>
    ["property-risk", address, propertyId] as const,
  countyRisk: (fips: string) => ["county-risk", fips] as const,
  riskExplain: (propertyId?: string, countyFips?: string) =>
    ["risk-explain", propertyId, countyFips] as const,
  procurementOpportunities: (countyFips?: string, q?: string, page?: number) =>
    ["procurement-opportunities", countyFips, q, page] as const,
  projects: (page?: number) => ["projects", page] as const,
  rankedOpportunities: () => ["ranked-opportunities"] as const,
  hybridSearch: (q: string) => ["hybrid-search", q] as const,
  alerts: (countyFips?: string, active?: boolean) => ["alerts", countyFips, active] as const,
  subscriptions: () => ["subscriptions"] as const,
  adminSources: (page?: number) => ["admin-sources", page] as const,
  adminIngestionRuns: (sourceId?: string) => ["admin-ingestion-runs", sourceId] as const,
  adminAuditLogs: (page?: number) => ["admin-audit-logs", page] as const,
};
