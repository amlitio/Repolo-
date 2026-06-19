import { z } from "zod";

/**
 * Runtime validation schemas mirroring packages/shared/src/types/api.ts and
 * registry.ts. These exist to catch backend/frontend contract drift at the
 * client boundary (e.g. apps/api still mid-development) rather than letting
 * malformed data silently propagate into React state. Shapes intentionally
 * match the shared TS interfaces field-for-field; if @firip/shared changes,
 * update both.
 */

export const riskGradeSchema = z.enum(["A", "B", "C", "D", "F"]);

export const riskFactorSchema = z.object({
  key: z.string(),
  label: z.string(),
  weight: z.number(),
  raw_value: z.union([z.number(), z.string(), z.null()]),
  normalized_score: z.number(),
  source_id: z.string().nullable(),
});

export const propertyRiskScoreSchema = z.object({
  property_id: z.string(),
  score: z.number(),
  grade: riskGradeSchema,
  factors: z.array(riskFactorSchema),
  explanation: z.string(),
  model_version: z.string(),
  computed_at: z.string(),
});

export const countyRiskScoreSchema = z.object({
  county_fips: z.string(),
  county_name: z.string(),
  score: z.number(),
  grade: riskGradeSchema,
  factors: z.array(riskFactorSchema),
  explanation: z.string(),
  model_version: z.string(),
  computed_at: z.string(),
});

export const riskExplainSchema = z.object({
  factors: z.array(riskFactorSchema),
  methodology: z.string(),
});

export const waterStationSchema = z.object({
  id: z.string(),
  source_id: z.string(),
  external_id: z.string(),
  name: z.string(),
  agency: z.string(),
  county_fips: z.string().nullable(),
  latitude: z.number(),
  longitude: z.number(),
  parameter_types: z.array(z.string()),
});

export const waterObservationSchema = z.object({
  station_id: z.string(),
  parameter: z.string(),
  value: z.number(),
  unit: z.string(),
  observed_at: z.string(),
  qualifier: z.string().nullable(),
});

export const waterSummarySchema = z.object({
  station_count: z.number(),
  latest_levels: z.array(z.unknown()),
  trend: z.string(),
});

export const weatherAlertSchema = z.object({
  id: z.string(),
  event: z.string(),
  severity: z.enum(["Extreme", "Severe", "Moderate", "Minor", "Unknown"]),
  certainty: z.string(),
  urgency: z.string(),
  headline: z.string(),
  description: z.string(),
  area_desc: z.string(),
  county_fips: z.array(z.string()),
  effective_at: z.string(),
  expires_at: z.string(),
  source_id: z.string(),
});

export const mapLayerLegendItemSchema = z.object({
  label: z.string(),
  color: z.string(),
});

export const mapLayerDefinitionSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.enum(["flood", "weather", "water", "risk", "hurricane", "procurement", "boundary"]),
  source_id: z.string(),
  default_visible: z.boolean(),
  min_zoom: z.number(),
  max_zoom: z.number(),
  legend: z.array(mapLayerLegendItemSchema),
});

export const mapSearchResultSchema = z.object({
  type: z.string(),
  id: z.string(),
  name: z.string(),
  fips: z.string().nullable().optional(),
  centroid: z.tuple([z.number(), z.number()]),
});

export const hybridSearchResultSchema = z.object({
  type: z.string(),
  id: z.string(),
  title: z.string(),
  snippet: z.string(),
  score: z.number(),
});

export const researchCitationSchema = z.object({
  source_id: z.string(),
  url: z.string(),
  snippet: z.string(),
});

export const researchAskResponseSchema = z.object({
  answer: z.string(),
  citations: z.array(researchCitationSchema),
});

export const procurementOpportunitySchema = z.object({
  id: z.string(),
  title: z.string(),
  county_fips: z.string().nullable().optional(),
  agency: z.string().optional(),
  status: z.string().optional(),
  posted_at: z.string().nullable().optional(),
  due_at: z.string().nullable().optional(),
  url: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
});

export const projectSchema = z.object({
  id: z.string(),
  name: z.string(),
  county_fips: z.string().nullable().optional(),
  status: z.string().optional(),
  description: z.string().nullable().optional(),
});

export const rankedOpportunitySchema = z.object({
  id: z.string(),
  title: z.string(),
  score: z.number(),
  rationale: z.string().optional(),
});

export const sourceRegistryEntrySchema = z.object({
  id: z.string(),
  name: z.string(),
  agency: z.string(),
  level: z.enum(["federal", "state", "regional", "county", "municipal"]),
  category: z.string(),
  access_method: z.string(),
  base_url: z.string(),
  docs_url: z.string(),
  auth_required: z.boolean(),
  license: z.string(),
  refresh_cadence: z.string(),
  data_quality_status: z.enum([
    "verified",
    "partially_verified",
    "needs_verification",
    "degraded",
    "unavailable",
  ]),
  verified_at: z.string().nullable(),
  notes: z.string(),
});

export const ingestionRunSchema = z.object({
  id: z.string(),
  source_id: z.string(),
  started_at: z.string(),
  finished_at: z.string().nullable(),
  status: z.string(),
  records_fetched: z.number(),
  records_normalized: z.number(),
  error_message: z.string().nullable(),
});

export const auditLogEntrySchema = z.object({
  id: z.string(),
  actor_user_id: z.string().nullable(),
  organization_id: z.string().nullable(),
  action: z.string(),
  resource_type: z.string(),
  resource_id: z.string().nullable(),
  occurred_at: z.string(),
});

export const sessionSchema = z.object({
  user_id: z.string(),
  email: z.string().nullable().optional(),
  name: z.string().nullable().optional(),
});

export const orgSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string().optional(),
});

export const rbacMeSchema = z.object({
  role: z.string(),
  permissions: z.array(z.string()).optional(),
});

export const subscriptionSchema = z.object({
  id: z.string(),
  county_fips: z.string().nullable().optional(),
  property_id: z.string().nullable().optional(),
  channel: z.string(),
  alert_types: z.array(z.string()),
  created_at: z.string().optional(),
});

export function paginated<T extends z.ZodTypeAny>(item: T) {
  return z.object({
    items: z.array(item),
    total: z.number(),
    page: z.number(),
    page_size: z.number(),
  });
}

/** GeoJSON FeatureCollection - kept loose; geometry/property validation lives in MapCanvas as needed. */
export const featureCollectionSchema = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(z.unknown()),
});
