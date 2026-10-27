"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Plus,
  ShieldCheck,
  Upload,
  Globe,
  Layers,
  ArrowRight,
  GitCommit,
} from "lucide-react";
import { API_BASE, getStoredToken } from "@/lib/api";

interface Contract {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  active_version: string;
  revisions_count: number;
  created_at: string;
}

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [showImport, setShowImport] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [specContent, setSpecContent] = useState("");
  const [importUrl, setImportUrl] = useState("");
  const [activeTab, setActiveTab] = useState<"paste" | "url">("paste");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadContracts = async () => {
    try {
      const token = getStoredToken();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      // First get projects
      const pRes = await fetch(`${API_BASE}/projects`, { headers });
      if (pRes.ok) {
        const projects = await pRes.json();
        const allContracts: Contract[] = [];
        for (const p of projects) {
          const cRes = await fetch(`${API_BASE}/projects/${p.id}/contracts`, { headers });
          if (cRes.ok) {
            const cList = await cRes.json();
            allContracts.push(...cList);
          }
        }
        setContracts(allContracts);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContracts();
  }, []);

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      let finalContent = specContent;
      if (activeTab === "url") {
        if (!importUrl) throw new Error("Please enter a valid URL");
        const fetchRes = await fetch(importUrl);
        if (!fetchRes.ok) throw new Error(`Failed to fetch URL: HTTP ${fetchRes.status}`);
        finalContent = await fetchRes.text();
      }

      if (!finalContent.trim()) throw new Error("Contract specification cannot be empty");

      const token = getStoredToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      // Get or create default project
      const pRes = await fetch(`${API_BASE}/projects`, { headers });
      const projects = await pRes.json();
      let projectId = projects[0]?.id;

      if (!projectId) {
        const newP = await fetch(`${API_BASE}/projects`, {
          method: "POST",
          headers,
          body: JSON.stringify({ name: "Default Project", description: "Default workspace" }),
        }).then(r => r.json());
        projectId = newP.id;
      }

      const res = await fetch(`${API_BASE}/projects/${projectId}/contracts`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          name: name || "Imported Contract",
          description,
          initial_content: finalContent,
          version: version || "1.0.0",
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create contract");
      }

      setShowImport(false);
      setName("");
      setDescription("");
      setSpecContent("");
      setImportUrl("");
      loadContracts();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1e2438] pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-emerald-500" /> API Contracts
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Registered OpenAPI specifications with automated immutable revision histories.
          </p>
        </div>
        <button
          onClick={() => setShowImport(true)}
          className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition shadow-lg shadow-emerald-950"
        >
          <Plus className="h-4 w-4" /> Import Contract
        </button>
      </div>

      {showImport && (
        <div className="mb-8 p-6 rounded-xl border border-emerald-500/30 bg-[#111420] max-w-2xl">
          <h3 className="text-base font-bold text-white mb-4">Import OpenAPI Contract</h3>

          {error && (
            <div className="mb-4 p-3 rounded bg-red-950/40 border border-red-800 text-red-300 text-xs">
              {error}
            </div>
          )}

          <div className="flex border-b border-[#1e2438] mb-4 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("paste")}
              className={`pb-2 px-3 border-b-2 transition ${
                activeTab === "paste"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-white"
              }`}
            >
              Paste YAML / JSON
            </button>
            <button
              onClick={() => setActiveTab("url")}
              className={`pb-2 px-3 border-b-2 transition ${
                activeTab === "url"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-white"
              }`}
            >
              Public URL
            </button>
          </div>

          <form onSubmit={handleImport} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Contract Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Users API"
                  className="w-full bg-[#090a0f] border border-[#1e2438] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Version</label>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="1.0.0"
                  className="w-full bg-[#090a0f] border border-[#1e2438] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {activeTab === "paste" ? (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">OpenAPI Specification</label>
                <textarea
                  required
                  rows={8}
                  value={specContent}
                  onChange={(e) => setSpecContent(e.target.value)}
                  placeholder="openapi: 3.0.3&#10;info:&#10;  title: My Service&#10;  version: 1.0.0&#10;paths: ..."
                  className="w-full font-mono text-xs bg-[#090a0f] border border-[#1e2438] rounded-lg p-3 text-white focus:outline-none focus:border-emerald-500 leading-relaxed"
                />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Specification URL</label>
                <input
                  type="url"
                  value={importUrl}
                  onChange={(e) => setImportUrl(e.target.value)}
                  placeholder="https://example.com/openapi.json"
                  className="w-full bg-[#090a0f] border border-[#1e2438] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-xs font-semibold disabled:opacity-50 transition"
              >
                {submitting ? "Importing..." : "Save Contract"}
              </button>
              <button
                type="button"
                onClick={() => setShowImport(false)}
                className="bg-[#1e2438] text-slate-300 hover:text-white px-4 py-2 rounded-lg text-xs font-semibold transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-sm text-slate-400 py-8">Loading contracts...</div>
      ) : contracts.length === 0 ? (
        <div className="text-center py-16 border border-[#1e2438] rounded-xl bg-[#111420]">
          <FileText className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No contracts registered yet</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Import an OpenAPI specification or paste YAML to start contract validation and breaking change tracking.
          </p>
          <button
            onClick={() => setShowImport(true)}
            className="mt-4 inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-xs transition"
          >
            <Plus className="h-4 w-4" /> Import Contract
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {contracts.map((c) => (
            <div
              key={c.id}
              className="p-6 rounded-xl border border-[#1e2438] bg-[#111420] flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-bold text-white tracking-tight">{c.name}</h3>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    v{c.active_version}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 mb-4">
                  {c.description || "OpenAPI contract specification."}
                </p>
              </div>

              <div className="pt-4 border-t border-[#1e2438] flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1 font-mono">
                  <GitCommit className="h-3.5 w-3.5 text-slate-400" />
                  {c.revisions_count} {c.revisions_count === 1 ? "rev" : "revs"}
                </span>
                <Link
                  href="/compare"
                  className="flex items-center gap-1 text-emerald-400 hover:underline font-medium"
                >
                  Diff Changes <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
