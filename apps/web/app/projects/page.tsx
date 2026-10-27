"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderGit2,
  Plus,
  ShieldCheck,
  Calendar,
  Layers,
  ArrowRight,
} from "lucide-react";
import { API_BASE, getStoredToken } from "@/lib/api";

interface Project {
  id: string;
  name: string;
  description?: string;
  contracts_count: number;
  created_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadProjects = async () => {
    try {
      const token = getStoredToken();
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/projects`, { headers });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      const token = getStoredToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers,
        body: JSON.stringify({ name, description }),
      });
      if (res.ok) {
        setName("");
        setDescription("");
        setShowCreate(false);
        loadProjects();
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1e2438] pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FolderGit2 className="h-6 w-6 text-emerald-500" /> API Projects
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Organize API contracts, environments, and automated regression test suites by team or service.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition shadow-lg shadow-emerald-950"
        >
          <Plus className="h-4 w-4" /> New Project
        </button>
      </div>

      {showCreate && (
        <div className="mb-8 p-6 rounded-xl border border-emerald-500/30 bg-[#111420] max-w-xl">
          <h3 className="text-base font-bold text-white mb-4">Create Project Workspace</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Project Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Payments Core Service"
                className="w-full bg-[#090a0f] border border-[#1e2438] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Description (Optional)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief summary of this API domain..."
                rows={3}
                className="w-full bg-[#090a0f] border border-[#1e2438] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-xs font-semibold disabled:opacity-50 transition"
              >
                {submitting ? "Creating..." : "Save Project"}
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="bg-[#1e2438] text-slate-300 hover:text-white px-4 py-2 rounded-lg text-xs font-semibold transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-sm text-slate-400 py-8">Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 border border-[#1e2438] rounded-xl bg-[#111420]">
          <FolderGit2 className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No projects created yet</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Create your first API project workspace to register OpenAPI specifications and monitor contract health.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-4 inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-xs transition"
          >
            <Plus className="h-4 w-4" /> Create Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              className="p-6 rounded-xl border border-[#1e2438] bg-[#111420] flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-bold text-white tracking-tight">{proj.name}</h3>
                  <span className="text-xs font-mono text-slate-500">{proj.id.slice(0, 8)}</span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 mb-4">
                  {proj.description || "No description provided."}
                </p>
              </div>

              <div className="pt-4 border-t border-[#1e2438] flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Layers className="h-3.5 w-3.5 text-emerald-400" />
                  {proj.contracts_count} {proj.contracts_count === 1 ? "Contract" : "Contracts"}
                </span>
                <Link
                  href={`/contracts`}
                  className="flex items-center gap-1 text-emerald-400 hover:underline font-medium"
                >
                  View Contracts <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
