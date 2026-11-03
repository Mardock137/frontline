"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Loader2, Ticket as TicketIcon, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/toast";
import { getTickets, updateTicketStatus, type Ticket, type TicketStatus } from "@/lib/api";

const STATUS_LABEL: Record<TicketStatus, string> = {
  open: "Open",
  in_progress: "In progress",
  closed: "Closed",
};

const STATUS_VARIANT: Record<TicketStatus, "warning" | "info" | "secondary"> = {
  open: "warning",
  in_progress: "info",
  closed: "secondary",
};

const NEXT_STATUS: Record<TicketStatus, TicketStatus | null> = {
  open: "in_progress",
  in_progress: "closed",
  closed: null,
};

const NEXT_LABEL: Record<TicketStatus, string | null> = {
  open: "Take on",
  in_progress: "Close",
  closed: null,
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function TicketsPage() {
  const { toast } = useToast();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTickets()
      .then(setTickets)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleStatusChange = async (ticket: Ticket) => {
    const next = NEXT_STATUS[ticket.status];
    if (!next) return;
    setUpdatingId(ticket.id);
    try {
      const updated = await updateTicketStatus(ticket.id, next);
      setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
      toast({ variant: "success", title: `Ticket updated to "${STATUS_LABEL[next]}"` });
    } catch (err) {
      toast({ variant: "error", title: "Update error", description: (err as Error).message });
    } finally {
      setUpdatingId(null);
    }
  };

  const escalationOpen = tickets.filter((t) => t.is_escalation && t.status !== "closed");

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tickets</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage support tickets opened by the AI agent or flagged for escalation.
        </p>
      </div>

      {/* Escalation alert */}
      {escalationOpen.length > 0 && (
        <div className="flex items-center gap-3 rounded-md border border-orange-200 bg-orange-50 p-4">
          <AlertTriangle className="h-5 w-5 shrink-0 text-orange-500" />
          <p className="text-sm text-orange-800">
            <span className="font-semibold">{escalationOpen.length}</span>{" "}
            {escalationOpen.length === 1 ? "open escalation ticket" : "open escalation tickets"} requiring
            immediate attention.
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      )}

      {/* Empty */}
      {!loading && !error && tickets.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16">
            <TicketIcon className="h-12 w-12 text-gray-300" />
            <p className="text-sm text-gray-500">No tickets yet.</p>
          </CardContent>
        </Card>
      )}

      {/* Table */}
      {!loading && tickets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>All tickets ({tickets.length})</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Subject</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="w-36" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {tickets.map((ticket) => {
                  const nextLabel = NEXT_LABEL[ticket.status];
                  return (
                    <TableRow key={ticket.id}>
                      <TableCell>
                        <p className="font-medium text-gray-900">{ticket.subject}</p>
                        <p className="mt-0.5 line-clamp-1 text-xs text-gray-500">
                          {ticket.description}
                        </p>
                      </TableCell>
                      <TableCell>
                        {ticket.is_escalation ? (
                          <Badge variant="destructive">
                            <AlertTriangle className="mr-1 h-3 w-3" />
                            Escalation
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Standard</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={STATUS_VARIANT[ticket.status]}>
                          {STATUS_LABEL[ticket.status]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-gray-500">{formatDate(ticket.created_at)}</TableCell>
                      <TableCell>
                        {nextLabel && (
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={updatingId === ticket.id}
                            onClick={() => handleStatusChange(ticket)}
                          >
                            {updatingId === ticket.id ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : null}
                            {nextLabel}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
