import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Frontline",
  description: "AI-powered customer support chat",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
