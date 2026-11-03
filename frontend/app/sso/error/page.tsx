import Link from "next/link";

const WEBSITE_URL = process.env.NEXT_PUBLIC_WEBSITE_URL?.trim() || undefined;

const REASON_COPY: Record<string, { title: string; body: string }> = {
  missing_token: {
    title: "Sign-in failed",
    body: "The access token is missing. Go back to the external site and open the app again.",
  },
  invalid_token: {
    title: "Link expired or invalid",
    body: "This sign-in link is no longer valid. Go back to the site and try again: the link only lasts one minute.",
  },
  backend_error: {
    title: "Service temporarily unavailable",
    body: "We could not reach Frontline. Try again in a moment from the external site.",
  },
};

export default async function SsoErrorPage({
  searchParams,
}: {
  searchParams: Promise<{ reason?: string }>;
}) {
  const { reason } = await searchParams;
  const copy =
    REASON_COPY[reason ?? ""] ?? {
      title: "Sign-in failed",
      body: "The dashboard could not be opened. Go back to the external site and try again.",
    };

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-8 text-center shadow-sm">
        <h1 className="text-xl font-semibold text-gray-900">{copy.title}</h1>
        <p className="mt-3 text-sm text-gray-600">{copy.body}</p>
        {WEBSITE_URL ? (
          <Link
            href={WEBSITE_URL}
            className="mt-6 inline-flex h-9 items-center justify-center rounded-md bg-gray-900 px-4 text-sm font-medium text-white hover:bg-gray-700"
          >
            Back to the site
          </Link>
        ) : null}
      </div>
    </main>
  );
}
