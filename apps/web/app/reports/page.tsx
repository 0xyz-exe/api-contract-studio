"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Download,
  FileText,
  GitCompare,
  PlayCircle,
  Terminal,
  ShieldAlert,
  CheckCircle2,
  Calendar,
  ArrowRight,
} from "lucide-react";

export default function ReportsPage() {
  const [reports] = useState([
    {
      id: "comp-sample-1",
      type: "comparison",
      title: "Petstore Service Diff",
      baseline: "v1.0.0",
      candidate: "v2.0.0",
      breaking_count: 3,
      passed_policy: false,
      timestamp: "2026-10-27",
    },
    {
      id: "test-sample-1",
      type: "test",
      title: "Public Health & Status API Test",
      baseline: "v1.0.0",
      candidate: "http://127.0.0.1:8000",
      breaking_count: 0,
      passed_policy: true,
      timestamp: "2026-10-27",
    },
  ]);

  const downloadJson = (item: any) => {
    const blob = new Blob([JSON.stringify(item, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${item.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadMarkdown = (item: any) => {
    const md = `# API Contract Studio Report: ${item.title}\n\nType: ${item.type}\nStatus: ${item.passed_policy ? "PASSED" : "FAILED"}\nBreaking Changes: ${item.breaking_count}\nDate: ${item.timestamp}\n`;
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${item.id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1e2438] pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Terminal className="h-6 w-6 text-emerald-500" /> Contract Audit & Compliance Reports
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Export machine-readable JSON and PR-ready Markdown comparison summaries for release audits.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-[#1e2438] bg-[#111420] overflow-hidden">
        <div className="p-4 border-b border-[#1e2438] font-bold text-sm text-white flex items-center justify-between">
          <span>Recent Contract Reports</span>
          <span className="text-xs text-slate-400 font-normal">Audit Trail</span>
        </div>
        <div className="divide-y divide-[#1e2438]">
          {reports.map((r) => (
            <div key={r.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-[#090a0f] border border-[#1e2438] mt-0.5">
                  {r.type === "comparison" ? (
                    <GitCompare className="h-5 w-5 text-emerald-400" />
                  ) : (
                    <PlayCircle className="h-5 w-5 text-cyan-400" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-bold text-white">{r.title}</h3>
                    {r.passed_policy ? (
                      <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                        PASSED
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded">
                        POLICY VIOLATION
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 flex flex-wrap items-center gap-3">
                    <span>Baseline: <code className="text-slate-300 font-mono">{r.baseline}</code></span>
                    <span>&rarr;</span>
                    <span>Candidate: <code className="text-slate-300 font-mono">{r.candidate}</code></span>
                    <span>&bull;</span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" /> {r.timestamp}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                <button
                  onClick={() => downloadMarkdown(r)}
                  className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-[#090a0f] border border-[#1e2438] px-3 py-1.5 rounded-lg transition"
                >
                  <Download className="h-3.5 w-3.5" /> Markdown
                </button>
                <button
                  onClick={() => downloadJson(r)}
                  className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-[#090a0f] border border-[#1e2438] px-3 py-1.5 rounded-lg transition"
                >
                  <Download className="h-3.5 w-3.5" /> JSON
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
