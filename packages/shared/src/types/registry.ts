export type DataQualityStatus =
  | "verified"
  | "partially_verified"
  | "needs_verification"
  | "degraded"
  | "unavailable";

export type SourceLevel = "federal" | "state" | "regional" | "county" | "municipal";

export type WaterManagementDistrict =
  | "NWFWMD"
  | "SRWMD"
  | "SJRWMD"
  | "SWFWMD"
  | "SFWMD";

export interface SourceRegistryEntry {
  id: string;
  name: string;
  agency: string;
  level: SourceLevel;
  category: string;
  access_method: string;
  base_url: string;
  docs_url: string;
  auth_required: boolean;
  license: string;
  refresh_cadence: string;
  data_quality_status: DataQualityStatus;
  verified_at: string | null;
  notes: string;
}

export interface CountyRegistryEntry {
  fips: string;
  name: string;
  state: "FL";
  region: string;
  water_management_districts: WaterManagementDistrict[];
  gis_open_data_url: string | null;
  procurement_url: string | null;
  permits_url: string | null;
  parcels_url: string | null;
  access_method: string | null;
  license: string | null;
  refresh_cadence: string;
  schema_notes: string | null;
  data_quality_status: DataQualityStatus;
  verified_at: string | null;
}
