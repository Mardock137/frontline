import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE_NAME } from "@/lib/session";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ALLOWED_ROOTS = new Set(["documents", "dashboard"]);

const MUTATING_METHODS = new Set(["POST", "PATCH", "DELETE"]);

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

function isAllowedPath(segments: string[]): boolean {
  if (segments.length === 0) {
    return false;
  }
  if (!ALLOWED_ROOTS.has(segments[0])) {
    return false;
  }
  return segments.every(
    (segment) => segment.length > 0 && segment !== "." && segment !== "..",
  );
}

function requestHost(request: NextRequest): string | null {
  const forwarded = request.headers.get("x-forwarded-host");
  const raw = (forwarded ?? request.headers.get("host"))?.split(",")[0]?.trim();
  return raw ? raw : null;
}

function hostsMatch(origin: string, hostHeader: string): boolean {
  let originUrl: URL;
  try {
    originUrl = new URL(origin);
  } catch {
    return false;
  }
  if (!originUrl.host) {
    return false;
  }
  let requestUrl: URL;
  try {
    requestUrl = new URL(`${originUrl.protocol}//${hostHeader}`);
  } catch {
    return false;
  }
  return originUrl.host.toLowerCase() === requestUrl.host.toLowerCase();
}

function isSameOriginMutation(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  if (origin) {
    const host = requestHost(request);
    return host !== null && hostsMatch(origin, host);
  }
  return request.headers.get("sec-fetch-site") === "same-origin";
}

async function proxy(
  request: NextRequest,
  context: RouteContext,
): Promise<NextResponse> {
  if (
    MUTATING_METHODS.has(request.method) &&
    !isSameOriginMutation(request)
  ) {
    return new NextResponse(null, { status: 403 });
  }

  const { path } = await context.params;
  if (!isAllowedPath(path)) {
    return new NextResponse(null, { status: 404 });
  }

  const destination = `${API_URL}/${path.map((segment) => encodeURIComponent(segment)).join("/")}${request.nextUrl.search}`;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const hasBody = request.method === "POST" || request.method === "PATCH";

  let upstream: Response;
  try {
    upstream = await fetch(destination, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: "no-store",
    });
  } catch {
    return new NextResponse(null, { status: 502 });
  }

  if (upstream.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  const responseHeaders = new Headers();
  const upstreamType = upstream.headers.get("content-type");
  if (upstreamType) {
    responseHeaders.set("Content-Type", upstreamType);
  }

  return new NextResponse(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
