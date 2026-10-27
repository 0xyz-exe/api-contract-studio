"use client";

import { useState } from "react";
import { Settings as SettingsIcon, Shield, Sliders, Save, CheckCircle2 } from "lucide-react";

export default function SettingsPage() {
  const [failOnBreaking, setFailOnBreaking] = useState(true);
  const [warnPotentiallyBreaking, setWarnPotentiallyBreaking] = useState(true);
  const [severityThreshold, setSeverityThreshold] = useState("HIGH");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="container max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between border-b border-[#1e2438] pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <SettingsIcon className="h-6 w-6 text-emerald-500" /> Platform & Policy Settings
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Global compatibility policies, breaking change enforcement, and CI threshold defaults.
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        <div className="rounded-xl border border-[#1e2438] bg-[#111420] p-6 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-400" /> Contract Policy Gates
          </h2>

          <div className="space-y-4 pt-2">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={failOnBreaking}
                onChange={(e) => setFailOnBreaking(e.target.checked)}
                className="mt-0.5 rounded border-[#1e2438] bg-[#090a0f] text-emerald-500 focus:ring-emerald-500"
              />
              <div>
                <span className="text-sm font-semibold text-white block">Fail CI on Breaking Changes</span>
                <span className="text-xs text-slate-400 block mt-0.5">
                  Block PR merges when endpoints are removed, required parameters added, or response properties deleted.
                </span>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={warnPotentiallyBreaking}
                onChange={(e) => setWarnPotentiallyBreaking(e.target.checked)}
                className="mt-0.5 rounded border-[#1e2438] bg-[#090a0f] text-emerald-500 focus:ring-emerald-500"
              />
              <div>
                <span className="text-sm font-semibold text-white block">Warn on Potentially Breaking Changes</span>
                <span className="text-xs text-slate-400 block mt-0.5">
                  Flag ambiguous changes (e.g. enum additions in responses, optional field removals) for engineer review.
                </span>
              </div>
            </label>
          </div>
        </div>

        <div className="rounded-xl border border-[#1e2438] bg-[#111420] p-6 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Sliders className="h-4 w-4 text-emerald-400" /> Severity Threshold
          </h2>

          <div className="max-w-xs">
            <label className="block text-xs font-medium text-slate-300 mb-1">Minimum Failure Severity</label>
            <select
              value={severityThreshold}
              onChange={(e) => setSeverityThreshold(e.target.value)}
              className="w-full bg-[#090a0f] border border-[#1e2438] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="CRITICAL">CRITICAL (Only total removals / breaking auth)</option>
              <option value="HIGH">HIGH (Standard: required params, removed fields)</option>
              <option value="MEDIUM">MEDIUM (Include enum & status changes)</option>
              <option value="LOW">LOW (Strict)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            type="submit"
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-lg text-xs font-semibold transition shadow-lg shadow-emerald-950"
          >
            <Save className="h-4 w-4" /> Save Policy Settings
          </button>
          {saved && (
            <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
              <CheckCircle2 className="h-4 w-4" /> Settings updated successfully
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
