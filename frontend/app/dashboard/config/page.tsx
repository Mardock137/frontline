"use client";

import { useEffect, useState } from "react";
import { Save, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { getAgentConfig, updateAgentConfig, type AgentConfig } from "@/lib/api";

export default function ConfigPage() {
  const { toast } = useToast();

  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAgentConfig()
      .then(setConfig)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const HEX_REGEX = /^#[0-9a-fA-F]{6}$/;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config) return;
    if (!HEX_REGEX.test(config.primary_color)) {
      toast({ variant: "error", title: "Invalid color", description: "Use the #RRGGBB format (e.g. #FF5733)" });
      return;
    }
    setSaving(true);
    try {
      const updated = await updateAgentConfig({
        agent_name: config.agent_name,
        company_display_name: config.company_display_name,
        primary_color: config.primary_color,
        tone: config.tone,
        default_language: config.default_language,
        welcome_message: config.welcome_message,
      });
      setConfig(updated);
      toast({ variant: "success", title: "Configuration saved" });
    } catch (err) {
      toast({ variant: "error", title: "Save error", description: (err as Error).message });
    } finally {
      setSaving(false);
    }
  };

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

  if (!config) return null;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agent configuration</h1>
        <p className="mt-1 text-sm text-gray-500">
          Customize the name, color, tone and welcome message of your AI agent.
        </p>
      </div>

      <form onSubmit={handleSave}>
        <div className="flex flex-col gap-6">
          {/* Identity */}
          <Card>
            <CardHeader>
              <CardTitle>Identity</CardTitle>
              <CardDescription>Agent name and branding.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="agent_name">Agent name</Label>
                  <Input
                    id="agent_name"
                    value={config.agent_name}
                    onChange={(e) => setConfig({ ...config, agent_name: e.target.value })}
                    placeholder="e.g. Sofia"
                    required
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="company_display_name">Company name</Label>
                  <Input
                    id="company_display_name"
                    value={config.company_display_name}
                    onChange={(e) => setConfig({ ...config, company_display_name: e.target.value })}
                    placeholder="e.g. Acme Inc."
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="primary_color">Primary color</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      id="primary_color"
                      value={config.primary_color}
                      onChange={(e) => setConfig({ ...config, primary_color: e.target.value })}
                      className="h-9 w-12 cursor-pointer rounded border border-gray-300 p-0.5"
                    />
                    <Input
                      value={config.primary_color}
                      onChange={(e) => setConfig({ ...config, primary_color: e.target.value })}
                      placeholder="#000000"
                      pattern="^#[0-9a-fA-F]{6}$"
                      className="font-mono"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Behaviour */}
          <Card>
            <CardHeader>
              <CardTitle>Behaviour</CardTitle>
              <CardDescription>Agent tone of voice and language.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="tone">Tone</Label>
                  <Select
                    id="tone"
                    value={config.tone}
                    onChange={(e) =>
                      setConfig({ ...config, tone: e.target.value as "formal" | "informal" })
                    }
                  >
                    <option value="formal">Formal</option>
                    <option value="informal">Informal</option>
                  </Select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="default_language">Default language</Label>
                  <Select
                    id="default_language"
                    value={config.default_language}
                    onChange={(e) => setConfig({ ...config, default_language: e.target.value })}
                  >
                    {!["it", "en", "es", "fr", "de", "pt"].includes(config.default_language) && (
                      <option value={config.default_language}>{config.default_language}</option>
                    )}
                    <option value="it">Italiano (it)</option>
                    <option value="en">English (en)</option>
                    <option value="es">Español (es)</option>
                    <option value="fr">Français (fr)</option>
                    <option value="de">Deutsch (de)</option>
                    <option value="pt">Português (pt)</option>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Welcome message */}
          <Card>
            <CardHeader>
              <CardTitle>Welcome message</CardTitle>
              <CardDescription>
                First thing the agent says when a user opens the chat.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                id="welcome_message"
                value={config.welcome_message}
                onChange={(e) => setConfig({ ...config, welcome_message: e.target.value })}
                rows={4}
                placeholder="Ciao! Come posso aiutarti oggi?"
                required
              />
            </CardContent>
          </Card>

          {/* Save */}
          <div className="flex justify-end">
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {saving ? "Saving..." : "Save configuration"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
