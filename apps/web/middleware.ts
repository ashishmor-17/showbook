import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Define protected path patterns
  const isProtectedRoute = 
    pathname.startsWith("/profile") || 
    pathname.startsWith("/bookings");

  // Check if token exists in cookies
  const token = request.cookies.get("showbook_access_token")?.value;

  if (isProtectedRoute && !token) {
    const url = new URL("/login", request.url);
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Configure paths that will trigger this middleware
export const config = {
  matcher: [
    "/profile/:path*",
    "/bookings/:path*",
  ],
};
