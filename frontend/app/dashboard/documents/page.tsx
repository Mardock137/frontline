"use client";

import React, { useEffect, useRef, useState } from "react";
import { Upload, Trash2, FileText, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import { deleteDocument, getDocuments, uploadDocument, type Document } from "@/lib/api";

const STATUS_VARIANT: Record<string, "success" | "warning" | "destructive" | "secondary"> = {
  ready: "success",
  processing: "warning",
  pending: "secondary",
  error: "destructive",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function DocumentsPage() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [docToDelete, setDocToDelete] = useState<Document | null>(null);

  const fetchDocuments = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getDocuments()
      .then((docs) => {
        setDocuments(docs);
        setError(null);
      })
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false));
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadDocument(file);
      toast({
        variant: "success",
        title: "Document uploaded",
        description: `${file.name} — ${result.chunk_count} indexed chunks`,
      });
      await fetchDocuments();
    } catch (err) {
      toast({
        variant: "error",
        title: "Upload error",
        description: (err as Error).message,
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteConfirm = async () => {
    if (!docToDelete) return;
    const doc = docToDelete;
    setDocToDelete(null);
    setDeletingId(doc.id);
    try {
      await deleteDocument(doc.id);
      toast({ variant: "success", title: "Document deleted" });
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch (err) {
      toast({
        variant: "error",
        title: "Delete error",
        description: (err as Error).message,
      });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload PDF, DOCX or TXT files to feed the agent&apos;s knowledge base.
          </p>
        </div>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={handleUpload}
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {uploading ? "Uploading..." : "Upload document"}
          </Button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && documents.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16">
            <FileText className="h-12 w-12 text-gray-300" />
            <p className="text-sm text-gray-500">
              No documents yet. Upload your first file to get started.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Document list */}
      {!loading && documents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Knowledge base ({documents.length} {documents.length === 1 ? "file" : "files"})</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Chunks</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="w-12" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">{doc.filename}</TableCell>
                    <TableCell className="text-gray-500">{doc.content_type}</TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[doc.status] ?? "secondary"}>
                        {doc.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{doc.chunk_count}</TableCell>
                    <TableCell className="text-gray-500">{formatDate(doc.created_at)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={deletingId === doc.id}
                        onClick={() => setDocToDelete(doc)}
                        aria-label="Delete document"
                      >
                        {deletingId === doc.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4 text-red-500" />
                        )}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={docToDelete !== null} onOpenChange={(open) => { if (!open) setDocToDelete(null); }}>
        <DialogContent className="relative">
          <DialogHeader>
            <DialogTitle>Delete document</DialogTitle>
            <DialogDescription>
              You are about to delete{" "}
              <span className="font-semibold text-gray-900">{docToDelete?.filename}</span>.
              This action is irreversible and will also remove all chunks from the knowledge base.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDocToDelete(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
