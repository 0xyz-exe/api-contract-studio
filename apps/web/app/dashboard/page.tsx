"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  FolderGit2,
  GitCompare,
  PlayCircle,
  Plus,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  Zap,
} from "lucide-react";
import { API_BASE, getStoredToken } from "@/lib/api";

interface Metrics {
  total_projects: number;
  total_contracts: number;
  total_comparisons: number;
  breaking_changes_detected: number;
  validation_success_rate: number;
  total_tests_run: number;
  test_pass_rate: number;
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics>({
    total_projects: 0,
    total_contracts: 0,
    total_comparisons: 0,
    breaking_changes_detected: 0,
    validation_success_rate: 100.0,
    total_tests_run: 0,
    test_pass_rate: 100.0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMetrics() {
      try {
        const token = getStoredToken();
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API_BASE}/dashboard/metrics`, { headers });
        if (res.ok) {
          const data = await res.json();
          setMetrics(data);
        }
      } catch (err) {
        console.error("Failed to load dashboard metrics", err);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1e2438] pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-emerald-500" />
            API Quality & Contract Governance Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time status of managed API specifications, contract test suites, and breaking change prevention.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/projects"
            className="flex items-center gap-2 bg-[#111420] hover:bg-[#1a2035] text-slate-200 border border-[#1e2438] px-4 py-2 rounded-lg font-medium text-sm transition"
          >
            <FolderGit2 className="h-4 w-4" /> Manage Projects
          </Link>
          <Link
            href="/compare"
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition shadow-lg shadow-emerald-950"
          >
            <GitCompare className="h-4 w-4" /> New Contract Diff
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="p-5 rounded-xl border border-[#1e2438] bg-[#111420]">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>API Projects</span>
            <FolderGit2 className="h-4 w-4 text-slate-500" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {loading ? "..." : metrics.total_projects}
          </div>
          <div className="text-xs text-slate-500 mt-2">Active project workspaces</div>
        </div>

        <div className="p-5 rounded-xl border border-[#1e2438] bg-[#111420]">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Registered Contracts</span>
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {loading ? "..." : metrics.total_contracts}
          </div>
          <div className="text-xs text-slate-500 mt-2">Version-controlled OpenAPI specs</div>
        </div>

        <div className="p-5 rounded-xl border border-[#1e2438] bg-[#111420]">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Breaking Changes Caught</span>
            <ShieldAlert className="h-4 w-4 text-red-400" />
          </div>
          <div className="text-3xl font-extrabold text-red-400 mt-2">
            {loading ? "..." : metrics.breaking_changes_detected}
          </div>
          <div className="text-xs text-slate-500 mt-2">Blocked before merging</div>
        </div>

        <div className="p-5 rounded-xl border border-[#1e2438] bg-[#111420]">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>CI Validation Pass Rate</span>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 mt-2">
            {loading ? "..." : `${metrics.validation_success_rate}%`}
          </div>
          <div className="text-xs text-slate-500 mt-2">Across automated comparisons</div>
        </div>
      </div>

      {/* Quick Launch & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-[#1e2438] bg-[#111420] p-6">
          <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
            <Zap className="h-4 w-4 text-emerald-400" /> Quick Workflows
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              href="/compare"
              className="p-4 rounded-lg border border-[#1e2438] bg-[#090a0f] hover:border-emerald-500/50 transition group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 text-white font-semibold text-sm group-hover:text-emerald-400 transition">
                  <GitCompare className="h-4 w-4 text-emerald-400" />
                  Semantic Contract Diff
                </div>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  Paste or select two OpenAPI specs to instantly analyze breaking changes, parameter updates, and schema modifications.
                </p>
              </div>
              <span className="text-xs text-emerald-400 font-medium flex items-center gap-1 mt-4">
                Launch Analyzer <ArrowRight className="h-3.5 w-3.5" />
              </span>
            </Link>

            <Link
              href="/test"
              className="p-4 rounded-lg border border-[#1e2438] bg-[#090a0f] hover:border-cyan-500/50 transition group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 text-white font-semibold text-sm group-hover:text-cyan-400 transition">
                  <PlayCircle className="h-4 w-4 text-cyan-400" />
                  Live Contract Testing
                </div>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  Execute automated HTTP requests against target environments and validate real payload conformity.
                </p>
              </div>
              <span className="text-xs text-cyan-400 font-medium flex items-center gap-1 mt-4">
                Execute Test Suite <ArrowRight className="h-3.5 w-3.5" />
              </span>
            </Link>
          </div>
        </div>

        <div className="rounded-xl border border-[#1e2438] bg-[#111420] p-6">
          <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> System Verification
          </h2>
          <div className="space-y-3 text-xs text-slate-300">
            <div className="flex items-center justify-between p-2.5 rounded bg-[#090a0f] border border-[#1e2438]">
              <span>OpenAPI Engine</span>
              <span className="text-emerald-400 font-semibold">3.0.x / 3.1.x</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-[#090a0f] border border-[#1e2438]">
              <span>SSRF Defense</span>
              <span className="text-emerald-400 font-semibold">Strict Guard Active</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-[#090a0f] border border-[#1e2438]">
              <span>Immutable Revisions</span>
              <span className="text-emerald-400 font-semibold">Enabled</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-[#090a0f] border border-[#1e2438]">
              <span>CLI Pipeline</span>
              <span className="text-emerald-400 font-semibold">acs v0.1.0</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
