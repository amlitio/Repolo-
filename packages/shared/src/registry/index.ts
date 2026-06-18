import countiesData from "../../data/counties.json";
import sourcesData from "../../data/sources.json";
import type { CountyRegistryEntry, SourceRegistryEntry } from "../types/registry";

export const COUNTIES: CountyRegistryEntry[] = countiesData as CountyRegistryEntry[];
export const SOURCES: SourceRegistryEntry[] = sourcesData as SourceRegistryEntry[];

export function getCountyByFips(fips: string): CountyRegistryEntry | undefined {
  return COUNTIES.find((c) => c.fips === fips);
}

export function getCountyByName(name: string): CountyRegistryEntry | undefined {
  return COUNTIES.find((c) => c.name.toLowerCase() === name.toLowerCase());
}

export function getSourceById(id: string): SourceRegistryEntry | undefined {
  return SOURCES.find((s) => s.id === id);
}

export function getSourcesByCategory(category: string): SourceRegistryEntry[] {
  return SOURCES.filter((s) => s.category === category);
}

export function getCountiesByWmd(
  wmd: CountyRegistryEntry["water_management_districts"][number]
): CountyRegistryEntry[] {
  return COUNTIES.filter((c) => c.water_management_districts.includes(wmd));
}
