import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { QueryProvider } from "@/lib/providers/QueryProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "FIRIP - Florida Flood & Water Risk Intelligence",
  description:
    "Florida flood and water risk intelligence platform: live flood zones, water station telemetry, property and county risk scoring, procurement intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const clerkPublishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  const body = (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 font-sans text-slate-200 antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );

  // Skip wrapping in ClerkProvider entirely when no publishable key is
  // configured (e.g. this sandbox build environment) so `next build` never
  // depends on reaching Clerk's network endpoints or throws at render time.
  if (!clerkPublishableKey) {
    return body;
  }

  return <ClerkProvider publishableKey={clerkPublishableKey}>{body}</ClerkProvider>;
}
