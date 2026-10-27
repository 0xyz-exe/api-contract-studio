"use client";

import { useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Download,
  FileCode,
  Filter,
  Info,
  Search,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

const SAMPLE_BASELINE = `openapi: 3.0.3
info:
  title: User Accounts API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  required: [id, email]
                  properties:
                    id:
                      type: string
                    email:
                      type: string
                    tier:
                      type: string
                      enum: [free, pro, enterprise]
  /users/{id}:
    delete:
      summary: Delete user
      responses:
        '204':
          description: User deleted
`;

const SAMPLE_CANDIDATE = `openapi: 3.0.3
info:
  title: User Accounts API
  version: 2.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
        - name: org_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  required: [id]
                  properties:
                    id:
                      type: string
                    tier:
                      type: string
                      enum: [free, pro]
`;

interface Finding {
  rule_id: string;
  category: string;
  severity: string;
  compatibility: string;
  location: string;
  old_value: string | null;
  new_value: string | null;
  message: string;
  remediation: string;
  fails_ci: boolean;
}

interface DiffSummary {
  total_changes: number;
  breaking_count: number;
  potentially_breaking_count: number;
  non_breaking_count: number;
  informational_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  passed_policy: boolean;
}

interface DiffReport {
  id?: string;
  baseline_title: string;
  baseline_version: string;
  candidate_title: string;
  candidate_version: string;
  summary: DiffSummary;
  findings: Finding[];
  timestamp: string;
}

export default function ComparePage() {
  const [baselineContent, setBaselineContent] = useState(SAMPLE_BASELINE);
  const [candidateContent, setCandidateContent] = useState(SAMPLE_CANDIDATE);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<DiffReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [compatFilter, setCompatFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set());

  const runDiff = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/contracts/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_content: baselineContent,
          candidate_content: candidateContent,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Comparison request failed" }));
        throw new Error(err.detail || "Comparison error");
      }
      const data: DiffReport = await res.json();
      setReport(data);
      // Auto expand first 5 findings
      setExpandedIndices(new Set(Array.from({ length: Math.min(5, data.findings.length) }, (_, i) => i)));
    } catch (err: any) {
      setError(err.message || "Failed to compare specifications");
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const downloadReport = (format: "json" | "markdown") => {
    if (!report) return;
    let content = "";
    let mime = "application/json";
    let filename = `api-contract-diff.${format === "json" ? "json" : "md"}`;

    if (format === "json") {
      content = JSON.stringify(report, null, 2);
    } else {
      content = `# API Contract Comparison Report\n\nBaseline: ${report.baseline_title} (v${report.baseline_version})\nCandidate: ${report.candidate_title} (v${report.candidate_version})\nPassed: ${report.summary.passed_policy ? "Yes" : "No"}\n\n## Findings\n\n` +
        report.findings.map(f => `- **[${f.severity}] ${f.rule_id}**: ${f.message}\n  Location: \`${f.location}\`\n  Remediation: ${f.remediation}\n`).join("\n");
      mime = "text/markdown";
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredFindings = (report?.findings || []).filter((f) => {
    if (compatFilter !== "ALL" && f.compatibility !== compatFilter) return false;
    if (severityFilter !== "ALL" && f.severity !== severityFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      const match =
        f.rule_id.toLowerCase().includes(q) ||
        f.location.toLowerCase().includes(q) ||
        f.message.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1e2438] pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Zap className="h-6 w-6 text-emerald-500" />
            Visual Contract Diff & Breaking Change Analyzer
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Compare two OpenAPI revisions semantically and enforce zero breaking changes before merging.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={runDiff}
            disabled={loading}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg font-medium text-sm transition shadow-lg shadow-emerald-950"
          >
            {loading ? "Comparing..." : "Run Semantic Diff"}
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300 text-sm flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Inputs Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="rounded-xl border border-[#1e2438] bg-[#111420] p-4 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileCode className="h-4 w-4 text-slate-400" /> Baseline Specification (Current / Production)
            </span>
            <span className="text-xs text-slate-500 font-mono">YAML / JSON</span>
          </div>
          <textarea
            value={baselineContent}
            onChange={(e) => setBaselineContent(e.target.value)}
            rows={12}
            className="w-full font-mono text-xs p-3 bg-[#090a0f] text-slate-200 border border-[#1e2438] rounded-lg focus:outline-none focus:border-emerald-500 leading-relaxed resize-y"
            placeholder="Paste baseline OpenAPI specification..."
          />
        </div>

        <div className="rounded-xl border border-[#1e2438] bg-[#111420] p-4 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileCode className="h-4 w-4 text-emerald-400" /> Candidate Specification (PR / Proposed)
            </span>
            <span className="text-xs text-slate-500 font-mono">YAML / JSON</span>
          </div>
          <textarea
            value={candidateContent}
            onChange={(e) => setCandidateContent(e.target.value)}
            rows={12}
            className="w-full font-mono text-xs p-3 bg-[#090a0f] text-slate-200 border border-[#1e2438] rounded-lg focus:outline-none focus:border-emerald-500 leading-relaxed resize-y"
            placeholder="Paste candidate OpenAPI specification..."
          />
        </div>
      </div>

      {/* Results Section */}
      {report && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="p-4 rounded-xl border border-[#1e2438] bg-[#111420]">
              <div className="text-xs text-slate-400 font-medium">Total Changes</div>
              <div className="text-2xl font-bold text-white mt-1">{report.summary.total_changes}</div>
            </div>
            <div className="p-4 rounded-xl border border-red-950/60 bg-red-950/20">
              <div className="text-xs text-red-400 font-medium flex items-center gap-1">
                <ShieldAlert className="h-3.5 w-3.5" /> Breaking
              </div>
              <div className="text-2xl font-bold text-red-400 mt-1">{report.summary.breaking_count}</div>
            </div>
            <div className="p-4 rounded-xl border border-amber-950/60 bg-amber-950/20">
              <div className="text-xs text-amber-400 font-medium flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5" /> Potentially Breaking
              </div>
              <div className="text-2xl font-bold text-amber-400 mt-1">{report.summary.potentially_breaking_count}</div>
            </div>
            <div className="p-4 rounded-xl border border-emerald-950/60 bg-emerald-950/20">
              <div className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Non-Breaking
              </div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">{report.summary.non_breaking_count}</div>
            </div>
            <div className="p-4 rounded-xl border border-[#1e2438] bg-[#111420]">
              <div className="text-xs text-slate-400 font-medium">CI Gate Status</div>
              <div className="mt-1">
                {report.summary.passed_policy ? (
                  <span className="inline-flex items-center gap-1 text-emerald-400 text-sm font-bold">
                    <CheckCircle2 className="h-4 w-4" /> PASSED
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-red-400 text-sm font-bold">
                    <ShieldAlert className="h-4 w-4" /> FAILED
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Filters Bar & Actions */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 rounded-xl border border-[#1e2438] bg-[#111420]">
            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              {/* Search */}
              <div className="relative min-w-[240px]">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Filter by rule, path, pointer..."
                  className="w-full bg-[#090a0f] border border-[#1e2438] rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Compatibility filter */}
              <div className="flex items-center gap-1.5 text-xs">
                <Filter className="h-3.5 w-3.5 text-slate-400" />
                <select
                  value={compatFilter}
                  onChange={(e) => setCompatFilter(e.target.value)}
                  className="bg-[#090a0f] border border-[#1e2438] rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="ALL">All Compatibilities</option>
                  <option value="BREAKING">🚨 Breaking</option>
                  <option value="POTENTIALLY_BREAKING">⚠️ Potentially Breaking</option>
                  <option value="NON_BREAKING">🟢 Non-Breaking</option>
                </select>
              </div>

              {/* Severity filter */}
              <div className="flex items-center gap-1.5 text-xs">
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="bg-[#090a0f] border border-[#1e2438] rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                  <option value="INFO">Info</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => downloadReport("markdown")}
                className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-[#090a0f] border border-[#1e2438] px-3 py-1.5 rounded-lg transition"
              >
                <Download className="h-3.5 w-3.5" /> Markdown
              </button>
              <button
                onClick={() => downloadReport("json")}
                className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-[#090a0f] border border-[#1e2438] px-3 py-1.5 rounded-lg transition"
              >
                <Download className="h-3.5 w-3.5" /> JSON
              </button>
            </div>
          </div>

          {/* Findings List */}
          <div className="space-y-3">
            {filteredFindings.length === 0 ? (
              <div className="p-8 text-center border border-[#1e2438] rounded-xl bg-[#111420] text-slate-400 text-sm">
                No findings match the selected filters.
              </div>
            ) : (
              filteredFindings.map((finding, idx) => {
                const isExpanded = expandedIndices.has(idx);
                const isBreaking = finding.compatibility === "BREAKING";
                const isPot = finding.compatibility === "POTENTIALLY_BREAKING";

                return (
                  <div
                    key={idx}
                    className={`rounded-xl border transition ${
                      isBreaking
                        ? "border-red-950/80 bg-red-950/10 hover:border-red-800"
                        : isPot
                        ? "border-amber-950/80 bg-amber-950/10 hover:border-amber-800"
                        : "border-[#1e2438] bg-[#111420] hover:border-slate-700"
                    }`}
                  >
                    <button
                      onClick={() => toggleExpand(idx)}
                      className="w-full text-left p-4 flex items-start justify-between gap-4"
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-slate-400" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-slate-400" />
                          )}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <span className="font-mono text-xs font-bold text-white px-2 py-0.5 rounded bg-[#1e2438]">
                              {finding.rule_id}
                            </span>
                            <span
                              className={`text-[11px] font-semibold uppercase px-2 py-0.5 rounded ${
                                isBreaking
                                  ? "bg-red-500/20 text-red-400"
                                  : isPot
                                  ? "bg-amber-500/20 text-amber-400"
                                  : "bg-emerald-500/20 text-emerald-400"
                              }`}
                            >
                              {finding.compatibility.replace("_", " ")}
                            </span>
                            <span className="text-[11px] text-slate-400 font-mono">
                              [{finding.severity}]
                            </span>
                            {finding.fails_ci && (
                              <span className="text-[10px] font-bold text-red-400 border border-red-500/30 px-1.5 py-0.2 rounded bg-red-500/10">
                                FAILS CI
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-200 font-medium">{finding.message}</p>
                          <div className="text-xs font-mono text-slate-500 mt-1">{finding.location}</div>
                        </div>
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4 pt-1 border-t border-[#1e2438]/60 space-y-3 text-xs">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
                          <div className="p-3 rounded-lg bg-[#090a0f] border border-[#1e2438]">
                            <span className="text-slate-400 font-semibold block mb-1">Baseline Value</span>
                            <code className="text-red-400 font-mono break-all">
                              {finding.old_value !== null ? finding.old_value : "—"}
                            </code>
                          </div>
                          <div className="p-3 rounded-lg bg-[#090a0f] border border-[#1e2438]">
                            <span className="text-slate-400 font-semibold block mb-1">Candidate Value</span>
                            <code className="text-emerald-400 font-mono break-all">
                              {finding.new_value !== null ? finding.new_value : "—"}
                            </code>
                          </div>
                        </div>

                        <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-emerald-300">
                          <span className="font-semibold block mb-1 flex items-center gap-1.5">
                            <Info className="h-3.5 w-3.5" /> Recommended Remediation
                          </span>
                          <p className="leading-relaxed">{finding.remediation}</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
