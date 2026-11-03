"use client";

import { useEffect, useState } from "react";
import { MessageSquare, Ticket, AlertTriangle, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getStats, type Stats } from "@/lib/api";

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  description?: string;
  accent?: "default" | "warning" | "success" | "danger";
}

const ACCENT_STYLES: Record<string, string> = {
  default: "bg-gray-900 text-white",
  warning: "bg-yellow-500 text-white",
  success: "bg-green-600 text-white",
  danger: "bg-red-600 text-white",
};

function StatCard({ title, value, icon, description, accent = "default" }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-gray-500">{title}</CardTitle>
          <span className={`rounded-md p-2 ${ACCENT_STYLES[accent]}`}>{icon}</span>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        {description && <p className="mt-1 text-xs text-gray-500">{description}</p>}
      </CardContent>
    </Card>
  );
}

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        <AlertCircle className="h-4 w-4 shrink-0" />
        {error}
      </div>
    );
  }

  if (!stats) return null;

  const { total_conversations, tickets_by_status, escalation_open_count } = stats;
  const total_tickets =
    tickets_by_status.open + tickets_by_status.in_progress + tickets_by_status.closed;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Statistics</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your AI agent&apos;s activity.
        </p>
      </div>

      {/* Top metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total conversations"
          value={total_conversations}
          icon={<MessageSquare className="h-4 w-4" />}
          description="All conversations started"
        />
        <StatCard
          title="Total tickets"
          value={total_tickets}
          icon={<Ticket className="h-4 w-4" />}
          description="Opened by the agent"
        />
        <StatCard
          title="Open escalations"
          value={escalation_open_count}
          icon={<AlertTriangle className="h-4 w-4" />}
          description="Require human intervention"
          accent={escalation_open_count > 0 ? "danger" : "default"}
        />
        <StatCard
          title="Closed tickets"
          value={tickets_by_status.closed}
          icon={<CheckCircle className="h-4 w-4" />}
          description="Successfully resolved"
          accent="success"
        />
      </div>

      {/* Ticket breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Tickets by status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            {(
              [
                {
                  label: "Open",
                  value: tickets_by_status.open,
                  color: "bg-yellow-500",
                },
                {
                  label: "In progress",
                  value: tickets_by_status.in_progress,
                  color: "bg-blue-500",
                },
                {
                  label: "Closed",
                  value: tickets_by_status.closed,
                  color: "bg-green-500",
                },
              ] as const
            ).map(({ label, value, color }) => {
              const pct = total_tickets > 0 ? Math.round((value / total_tickets) * 100) : 0;
              return (
                <div key={label} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">{label}</span>
                    <span className="font-semibold text-gray-900">
                      {value}
                      <span className="ml-1 font-normal text-gray-400">({pct}%)</span>
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                    <div
                      className={`h-2 rounded-full ${color} transition-all`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
