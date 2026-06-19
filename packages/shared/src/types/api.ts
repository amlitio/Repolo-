export interface ApiErrorBody {
  code: string;
  message: string;
  details: unknown[];
}

export interface ApiErrorResponse {
  success: false;
  error: ApiErrorBody;
}

/**
 * Success responses are returned as the resource itself (FastAPI
 * response_model=T, HTTP 200/201). Only failures use the envelope above,
 * produced by a single global exception handler - see
 * apps/api/app/core/errors.py.
 */
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

import type { RiskGrade } from "../constants/scoring";

export interface RiskFactor {
  key: string;
  label: string;
  weight: number;
  raw_value: number | string | null;
  normalized_score: number;
  source_id: string | null;
}

export interface PropertyRiskScore {
  property_id: string;
  score: number;
  grade: RiskGrade;
  factors: RiskFactor[];
  explanation: string;
  model_version: string;
  computed_at: string;
}

export interface CountyRiskScore {
  county_fips: string;
  county_name: string;
  score: number;
  grade: RiskGrade;
  factors: RiskFactor[];
  explanation: string;
  model_version: string;
  computed_at: string;
}

export interface WaterStation {
  id: string;
  source_id: string;
  external_id: string;
  name: string;
  agency: string;
  county_fips: string | null;
  latitude: number;
  longitude: number;
  parameter_types: string[];
}

export interface WaterObservation {
  station_id: string;
  parameter: string;
  value: number;
  unit: string;
  observed_at: string;
  qualifier: string | null;
}

export interface WeatherAlert {
  id: string;
  event: string;
  severity: "Extreme" | "Severe" | "Moderate" | "Minor" | "Unknown";
  certainty: string;
  urgency: string;
  headline: string;
  description: string;
  area_desc: string;
  county_fips: string[];
  effective_at: string;
  expires_at: string;
  source_id: string;
}

export interface HurricaneTrack {
  storm_id: string;
  name: string;
  season: number;
  advisory_num: string;
  classification: string;
  issued_at: string;
  geometry: GeoJSON.Geometry;
}

export interface FloodZone {
  id: string;
  fips: string;
  zone_label: string;
  is_special_flood_hazard_area: boolean;
  base_flood_elevation: number | null;
  geometry: GeoJSON.Geometry;
  effective_date: string | null;
}

export interface MapLayerDefinition {
  id: string;
  name: string;
  category: "flood" | "weather" | "water" | "risk" | "hurricane" | "procurement" | "boundary";
  source_id: string;
  default_visible: boolean;
  min_zoom: number;
  max_zoom: number;
  legend: { label: string; color: string }[];
}
