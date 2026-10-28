import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("archova_session")?.value;

  // Protect /chat and any nested subroutes under /chat
  if (pathname === "/chat" || pathname.startsWith("/chat/")) {
    if (!token) {
      const redirectUrl = new URL("/signin", request.url);
      redirectUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(redirectUrl);
    }
  }

  return NextResponse.next();
}

export default proxy;

export const config = {
  matcher: [
    "/chat",
    "/chat/:path*",
  ],
};

