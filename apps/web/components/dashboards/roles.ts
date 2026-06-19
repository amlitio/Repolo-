export const DASHBOARD_ROLES = [
  "executive",
  "government",
  "engineering",
  "contractor",
  "investor",
  "emergency-management",
] as const;

export type DashboardRole = (typeof DASHBOARD_ROLES)[number];

export function isDashboardRole(value: string): value is DashboardRole {
  return (DASHBOARD_ROLES as readonly string[]).includes(value);
}

export const DASHBOARD_ROLE_LABELS: Record<DashboardRole, string> = {
  executive: "Executive",
  government: "Government",
  engineering: "Engineering",
  contractor: "Contractor",
  investor: "Investor",
  "emergency-management": "Emergency Management",
};

export const DASHBOARD_ROLE_DESCRIPTIONS: Record<DashboardRole, string> = {
  executive: "Portfolio-level risk exposure, active alerts, and project pipeline at a glance.",
  government: "County-level risk posture, water conditions, and active weather alerts.",
  engineering: "Water station telemetry, flood zone status, and project pipeline detail.",
  contractor: "Procurement opportunities and ranked leads relevant to flood resilience work.",
  investor: "County risk scores and procurement/project pipeline for capital allocation.",
  "emergency-management": "Active alerts, county risk, and subscription management for rapid response.",
};
