"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, Ticket, Settings, BarChart2, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { ToastProvider } from "@/components/ui/toast";

const navItems = [
  { label: "Documents", href: "/dashboard/documents", icon: FileText },
  { label: "Tickets", href: "/dashboard/tickets", icon: Ticket },
  { label: "Configuration", href: "/dashboard/config", icon: Settings },
  { label: "Statistics", href: "/dashboard/stats", icon: BarChart2 },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <ToastProvider>
      <div className="flex min-h-screen bg-gray-50">
        {/* Sidebar */}
        <aside className="flex w-60 flex-col border-r border-gray-200 bg-white">
          {/* Logo / brand */}
          <div className="flex h-14 items-center gap-2 border-b border-gray-200 px-4">
            <Zap className="h-5 w-5 text-gray-900" />
            <span className="text-sm font-semibold text-gray-900">Frontline</span>
          </div>

          {/* Navigation */}
          <nav className="flex flex-col gap-1 p-3" aria-label="Main navigation">
            {navItems.map(({ label, href, icon: Icon }) => {
              const active = pathname === href || pathname.startsWith(href + "/");
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-gray-900 text-white"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {label}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <div className="mx-auto max-w-5xl p-6">{children}</div>
        </main>
      </div>
    </ToastProvider>
  );
}
