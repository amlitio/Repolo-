import type {
  CountyRiskScore,
  FloodZone,
  MapLayerDefinition,
  Paginated,
  PropertyRiskScore,
  SourceRegistryEntry,
  WaterObservation,
  WaterStation,
  WeatherAlert,
} from "@firip/shared";
import { apiFetch } from "./client";
import {
  auditLogEntrySchema,
  countyRiskScoreSchema,
  featureCollectionSchema,
  hybridSearchResultSchema,
  ingestionRunSchema,
  mapLayerDefinitionSchema,
  mapSearchResultSchema,
  orgSchema,
  paginated,
  procurementOpportunitySchema,
  projectSchema,
  propertyRiskScoreSchema,
  rankedOpportunitySchema,
  rbacMeSchema,
  researchAskResponseSchema,
  riskExplainSchema,
  sessionSchema,
  sourceRegistryEntrySchema,
  subscriptionSchema,
  waterObservationSchema,
  waterStationSchema,
  waterSummarySchema,
  weatherAlertSchema,
} from "./schemas";
import { z } from "zod";

/** GeoJSON FeatureCollection, typed loosely - geometry shape is validated downstream by MapCanvas/mapbox-gl. */
export type FeatureCollectionResponse = z.infer<typeof featureCollectionSchema>;
export type MapSearchResult = z.infer<typeof mapSearchResultSchema>;
export type HybridSearchResult = z.infer<typeof hybridSearchResultSchema>;
export type ResearchAskResponse = z.infer<typeof researchAskResponseSchema>;
export type RiskExplainResponse = z.infer<typeof riskExplainSchema>;
export type WaterSummaryResponse = z.infer<typeof waterSummarySchema>;
export type ProcurementOpportunity = z.infer<typeof procurementOpportunitySchema>;
export type Project = z.infer<typeof projectSchema>;
export type RankedOpportunity = z.infer<typeof rankedOpportunitySchema>;
export type IngestionRun = z.infer<typeof ingestionRunSchema>;
export type AuditLogEntry = z.infer<typeof auditLogEntrySchema>;
export type Session = z.infer<typeof sessionSchema>;
export type Org = z.infer<typeof orgSchema>;
export type RbacMe = z.infer<typeof rbacMeSchema>;
export type Subscription = z.infer<typeof subscriptionSchema>;

// ---------------------------------------------------------------------------
// Auth / org / rbac
// ---------------------------------------------------------------------------

export async function getSession(): Promise<Session> {
  const data = await apiFetch<unknown>("/auth/session");
  return sessionSchema.parse(data);
}

export async function getOrgs(): Promise<Org[]> {
  const data = await apiFetch<unknown>("/orgs");
  return z.array(orgSchema).parse(data);
}

export async function getRbacMe(): Promise<RbacMe> {
  const data = await apiFetch<unknown>("/rbac/me");
  return rbacMeSchema.parse(data);
}

// ---------------------------------------------------------------------------
// Map
// ---------------------------------------------------------------------------

export async function getMapLayers(): Promise<MapLayerDefinition[]> {
  const data = await apiFetch<unknown>("/map/layers");
  return z.array(mapLayerDefinitionSchema).parse(data) as MapLayerDefinition[];
}

export interface QueryMapFeaturesParams {
  layerId: string;
  bbox: [number, number, number, number];
  zoom?: number;
}

export async function queryMapFeatures(
  params: QueryMapFeaturesParams
): Promise<FeatureCollectionResponse> {
  const data = await apiFetch<unknown>("/map/features/query", {
    query: {
      layer_id: params.layerId,
      bbox: params.bbox.join(","),
      zoom: params.zoom,
    },
  });
  return featureCollectionSchema.parse(data);
}

export async function searchMap(q: string): Promise<MapSearchResult[]> {
  const data = await apiFetch<unknown>("/map/search", { query: { q } });
  return z.array(mapSearchResultSchema).parse(data);
}

// ---------------------------------------------------------------------------
// Water
// ---------------------------------------------------------------------------

export interface GetWaterStationsParams {
  countyFips?: string;
  sourceId?: string;
  page?: number;
}

export async function getWaterStations(
  params: GetWaterStationsParams = {}
): Promise<Paginated<WaterStation>> {
  const data = await apiFetch<unknown>("/water/stations", {
    query: { county_fips: params.countyFips, source_id: params.sourceId, page: params.page },
  });
  return paginated(waterStationSchema).parse(data) as Paginated<WaterStation>;
}

export interface GetWaterObservationsParams {
  stationId?: string;
  parameter?: string;
  start?: string;
  end?: string;
  page?: number;
}

export async function getWaterObservations(
  params: GetWaterObservationsParams = {}
): Promise<Paginated<WaterObservation>> {
  const data = await apiFetch<unknown>("/water/observations", {
    query: {
      station_id: params.stationId,
      parameter: params.parameter,
      start: params.start,
      end: params.end,
      page: params.page,
    },
  });
  return paginated(waterObservationSchema).parse(data) as Paginated<WaterObservation>;
}

export async function getWaterSummary(countyFips: string): Promise<WaterSummaryResponse> {
  const data = await apiFetch<unknown>("/water/summary", { query: { county_fips: countyFips } });
  return waterSummarySchema.parse(data);
}

// ---------------------------------------------------------------------------
// Flood
// ---------------------------------------------------------------------------

export interface GetFloodZonesParams {
  countyFips?: string;
  bbox?: [number, number, number, number];
}

export async function getFloodZones(
  params: GetFloodZonesParams = {}
): Promise<FeatureCollectionResponse> {
  const data = await apiFetch<unknown>("/flood/zones", {
    query: {
      county_fips: params.countyFips,
      bbox: params.bbox?.join(","),
    },
  });
  return featureCollectionSchema.parse(data);
}

// Re-exported for call sites that want the raw shared type name.
export type { FloodZone };

// ---------------------------------------------------------------------------
// Risk
// ---------------------------------------------------------------------------

export interface GetPropertyRiskParams {
  address?: string;
  propertyId?: string;
}

export async function getPropertyRisk(
  params: GetPropertyRiskParams
): Promise<PropertyRiskScore> {
  const data = await apiFetch<unknown>("/risk/property", {
    query: { address: params.address, property_id: params.propertyId },
  });
  return propertyRiskScoreSchema.parse(data) as PropertyRiskScore;
}

export async function getCountyRisk(fips: string): Promise<CountyRiskScore> {
  const data = await apiFetch<unknown>("/risk/county", { query: { fips } });
  return countyRiskScoreSchema.parse(data) as CountyRiskScore;
}

export interface ExplainRiskParams {
  propertyId?: string;
  countyFips?: string;
}

export async function explainRisk(params: ExplainRiskParams): Promise<RiskExplainResponse> {
  const data = await apiFetch<unknown>("/risk/explain", {
    query: { property_id: params.propertyId, county_fips: params.countyFips },
  });
  return riskExplainSchema.parse(data);
}

// ---------------------------------------------------------------------------
// Procurement / projects / opportunities
// ---------------------------------------------------------------------------

export interface GetProcurementOpportunitiesParams {
  countyFips?: string;
  q?: string;
  page?: number;
}

export async function getProcurementOpportunities(
  params: GetProcurementOpportunitiesParams = {}
): Promise<Paginated<ProcurementOpportunity>> {
  const data = await apiFetch<unknown>("/procurement/opportunities", {
    query: { county_fips: params.countyFips, q: params.q, page: params.page },
  });
  return paginated(procurementOpportunitySchema).parse(data);
}

export interface GetProjectsParams {
  page?: number;
}

export async function getProjects(params: GetProjectsParams = {}): Promise<Paginated<Project>> {
  const data = await apiFetch<unknown>("/projects", { query: { page: params.page } });
  return paginated(projectSchema).parse(data);
}

export async function rankOpportunities(): Promise<RankedOpportunity[]> {
  const data = await apiFetch<unknown>("/opportunities/rank");
  return z.array(rankedOpportunitySchema).parse(data);
}

// ---------------------------------------------------------------------------
// Search / research
// ---------------------------------------------------------------------------

export interface HybridSearchParams {
  q: string;
  topK?: number;
}

export async function hybridSearch(params: HybridSearchParams): Promise<HybridSearchResult[]> {
  const data = await apiFetch<unknown>("/search/hybrid", {
    query: { q: params.q, top_k: params.topK },
  });
  return z.array(hybridSearchResultSchema).parse(data);
}

export interface AskResearchPayload {
  question: string;
  context_filters?: Record<string, unknown>;
}

export async function askResearch(payload: AskResearchPayload): Promise<ResearchAskResponse> {
  const data = await apiFetch<unknown>("/research/ask", { method: "POST", body: payload });
  return researchAskResponseSchema.parse(data);
}

// ---------------------------------------------------------------------------
// Alerts / subscriptions
// ---------------------------------------------------------------------------

export interface GetAlertsParams {
  countyFips?: string;
  active?: boolean;
  page?: number;
}

export async function getAlerts(params: GetAlertsParams = {}): Promise<Paginated<WeatherAlert>> {
  const data = await apiFetch<unknown>("/alerts", {
    query: { county_fips: params.countyFips, active: params.active, page: params.page },
  });
  return paginated(weatherAlertSchema).parse(data) as Paginated<WeatherAlert>;
}

export interface CreateSubscriptionPayload {
  county_fips?: string;
  property_id?: string;
  channel: string;
  alert_types: string[];
}

export async function createSubscription(
  payload: CreateSubscriptionPayload
): Promise<Subscription> {
  const data = await apiFetch<unknown>("/subscriptions", { method: "POST", body: payload });
  return subscriptionSchema.parse(data);
}

export async function listSubscriptions(): Promise<Subscription[]> {
  const data = await apiFetch<unknown>("/subscriptions");
  return z.array(subscriptionSchema).parse(data);
}

export async function sendTestNotification(): Promise<{ sent: boolean }> {
  const data = await apiFetch<unknown>("/notifications/test", { method: "POST" });
  return z.object({ sent: z.boolean() }).parse(data);
}

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

export interface AdminListParams {
  page?: number;
}

export async function adminListSources(
  params: AdminListParams = {}
): Promise<Paginated<SourceRegistryEntry>> {
  const data = await apiFetch<unknown>("/admin/sources", { query: { page: params.page } });
  return paginated(sourceRegistryEntrySchema).parse(data) as Paginated<SourceRegistryEntry>;
}

export interface AdminListIngestionRunsParams {
  sourceId?: string;
  page?: number;
}

export async function adminListIngestionRuns(
  params: AdminListIngestionRunsParams = {}
): Promise<Paginated<IngestionRun>> {
  const data = await apiFetch<unknown>("/admin/ingestion-runs", {
    query: { source_id: params.sourceId, page: params.page },
  });
  return paginated(ingestionRunSchema).parse(data);
}

export async function adminListAuditLogs(
  params: AdminListParams = {}
): Promise<Paginated<AuditLogEntry>> {
  const data = await apiFetch<unknown>("/admin/audit-logs", { query: { page: params.page } });
  return paginated(auditLogEntrySchema).parse(data);
}
