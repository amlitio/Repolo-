import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isProtectedRoute = createRouteMatcher(["/map(.*)", "/dashboard(.*)", "/admin(.*)"]);

const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

/**
 * Route protection for /map, /dashboard/*, and /admin. When Clerk env vars
 * aren't configured (e.g. this sandbox, or a fresh checkout before secrets
 * are provisioned) the middleware becomes a no-op pass-through rather than
 * throwing, so `next build`/`next dev` never hard-depend on Clerk being
 * reachable.
 */
export default clerkConfigured
  ? clerkMiddleware(async (auth, req) => {
      if (isProtectedRoute(req)) {
        await auth.protect();
      }
    })
  : () => NextResponse.next();

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
