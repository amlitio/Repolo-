import Link from "next/link";
import { Button } from "@/components/ui/Button";

const FEATURES = [
  {
    title: "Live flood & water intelligence",
    description:
      "FEMA flood zones, USGS/SFWMD/SJRWMD/SWFWMD water station telemetry, NOAA alerts, and hurricane tracks on one dark, dense map canvas.",
  },
  {
    title: "Property & county risk scoring",
    description:
      "Transparent A-F risk grades with explainable factor breakdowns, built on a shared, versioned scoring model.",
  },
  {
    title: "Procurement & opportunity intelligence",
    description:
      "Surface flood-resilience procurement opportunities and projects across all 67 Florida counties as ingestion comes online.",
  },
];

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col bg-slate-950">
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400" aria-hidden />
          <span className="font-mono text-sm font-semibold tracking-widest text-slate-100">
            FIRIP
          </span>
        </div>
        <nav className="flex items-center gap-3">
          <Link href="/sign-in" className="text-xs text-slate-400 hover:text-slate-100">
            Sign in
          </Link>
          <Link href="/sign-up">
            <Button size="sm">Get started</Button>
          </Link>
        </nav>
      </header>

      <section className="flex flex-1 flex-col items-center justify-center gap-8 px-6 py-24 text-center">
        <div className="max-w-2xl space-y-4">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-cyan-400">
            Florida flood &amp; water risk intelligence
          </p>
          <h1 className="text-3xl font-semibold text-slate-50 sm:text-4xl">
            One terminal for Florida&apos;s flood, water, and resilience risk data.
          </h1>
          <p className="text-sm text-slate-400 sm:text-base">
            FIRIP unifies FEMA flood zones, real-time water station telemetry, NOAA weather
            alerts, hurricane tracks, and explainable property/county risk scoring into a single
            map-first workspace for government, engineering, and investment teams.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/map">
            <Button size="lg">Launch Map</Button>
          </Link>
          <Link href="/sign-up">
            <Button size="lg" variant="outline">
              Create account
            </Button>
          </Link>
        </div>
      </section>

      <section className="grid gap-px border-t border-slate-800 bg-slate-800 sm:grid-cols-3">
        {FEATURES.map((feature) => (
          <div key={feature.title} className="bg-slate-950 p-6">
            <h2 className="text-sm font-semibold text-slate-100">{feature.title}</h2>
            <p className="mt-2 text-xs text-slate-400">{feature.description}</p>
          </div>
        ))}
      </section>

      <footer className="border-t border-slate-800 px-6 py-4 text-center text-[11px] text-slate-500">
        FIRIP - Florida Risk + Water Intelligence Platform
      </footer>
    </main>
  );
}
