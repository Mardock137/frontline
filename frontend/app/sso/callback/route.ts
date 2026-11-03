import { NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE_NAME, SESSION_MAX_AGE_SECONDS } from "@/lib/session";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function errorRedirect(request: NextRequest, reason: string): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = "/sso/error";
  url.search = `reason=${encodeURIComponent(reason)}`;
  return NextResponse.redirect(url);
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const ssoToken = request.nextUrl.searchParams.get("sso_token");
  if (!ssoToken) {
    return errorRedirect(request, "missing_token");
  }

  let sessionToken: string;
  try {
    const res = await fetch(`${API_URL}/auth/sso`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sso_token: ssoToken }),
    });
    if (!res.ok) {
      return errorRedirect(request, "invalid_token");
    }
    const body = (await res.json()) as { session_token?: string };
    if (!body.session_token) {
      return errorRedirect(request, "invalid_token");
    }
    sessionToken = body.session_token;
  } catch {
    return errorRedirect(request, "backend_error");
  }

  const dashboard = request.nextUrl.clone();
  dashboard.pathname = "/dashboard";
  dashboard.search = "";
  const response = NextResponse.redirect(dashboard);
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: sessionToken,
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
    sameSite: "lax",
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
  });
  return response;
}
