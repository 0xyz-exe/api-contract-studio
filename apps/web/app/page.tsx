import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  GitCompare,
  PlayCircle,
  ShieldCheck,
  Terminal,
  Zap,
} from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 md:py-32 border-b border-[#1e2438]">
        <div className="container max-w-6xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-8">
            <ShieldCheck className="h-4 w-4" /> Open-Source API Compatibility Platform
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight md:leading-none">
            Catch Breaking API Changes <br className="hidden md:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
              Before They Reach Production.
            </span>
          </h1>

          <p className="mt-6 text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            API Contract Studio defines, semantically diffs, and validates OpenAPI contracts against real implementations. Stop API regressions at the pull request.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/compare"
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-lg font-semibold text-sm transition shadow-lg shadow-emerald-950"
            >
              Try Interactive Diff <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/dashboard"
              className="flex items-center gap-2 bg-[#111420] hover:bg-[#1a2035] text-slate-200 border border-[#1e2438] px-6 py-3 rounded-lg font-semibold text-sm transition"
            >
              Open Dashboard
            </Link>
          </div>

          {/* Quick Terminal Snippet */}
          <div className="mt-14 max-w-xl mx-auto rounded-xl border border-[#1e2438] bg-[#111420] text-left p-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center gap-1.5 mb-3 text-slate-500">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></div>
              <div className="w-2.5 h-2.5 rounded-full bg-green-500/80"></div>
              <span className="ml-2 text-[11px] text-slate-400 font-sans">terminal — api-contract-studio</span>
            </div>
            <div className="text-slate-300">
              <span className="text-emerald-400">$</span> acs diff baseline.yaml candidate.yaml
            </div>
            <div className="mt-2 text-red-400 font-semibold">
              🚨 [HIGH] ACS-REQ-PARAM-ADDED-REQUIRED at #/paths/~1users/get/parameters/org_id [FAILS CI]
            </div>
            <div className="text-slate-400">
              Message: New required parameter &apos;org_id&apos; added to GET /users.
            </div>
            <div className="text-emerald-400/80 mt-1">
              Remediation: Make parameter &apos;org_id&apos; optional with a default value.
            </div>
          </div>
        </div>
      </section>

      {/* Core Features */}
      <section className="py-20 border-b border-[#1e2438] bg-[#0c0e17]">
        <div className="container max-w-6xl mx-auto px-4">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-white tracking-tight">Built for Developer Pipelines</h2>
            <p className="mt-3 text-slate-400 text-sm">
              From local pre-commit checks to production deployment gates, every compatibility rule is deterministic.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-xl border border-[#1e2438] bg-[#111420] flex flex-col">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                <GitCompare className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Semantic OpenAPI Diff</h3>
              <p className="text-sm text-slate-400 leading-relaxed flex-1">
                Goes beyond raw text diffs. Detects removed endpoints, narrowed enums, changed types, and newly required request bodies across OpenAPI 3.0 & 3.1.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-[#1e2438] bg-[#111420] flex flex-col">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
                <PlayCircle className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Live Contract Testing</h3>
              <p className="text-sm text-slate-400 leading-relaxed flex-1">
                Sends HTTP requests to running services and verifies observed HTTP status codes, headers, and response payloads against contract schemas.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-[#1e2438] bg-[#111420] flex flex-col">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4">
                <Terminal className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">CI/CD & CLI Ready</h3>
              <p className="text-sm text-slate-400 leading-relaxed flex-1">
                Deterministic exit codes (`0`, `1`, `2`, `3`), JSON / Markdown reports, and GitHub Actions integration to block breaking PRs automatically.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CI/CD Integration Section */}
      <section className="py-20 border-b border-[#1e2438]">
        <div className="container max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3">
                <Zap className="h-4 w-4" /> Automated Pull Request Gates
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight mb-4">
                Enforce Zero Breaking Changes in GitHub Actions
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed mb-6">
                Configure policy thresholds with a simple <code className="text-emerald-300 font-mono">.api-contract-studio.yml</code> file.
                Automatically post human-readable comparison reports directly into GitHub Pull Request comments.
              </p>
              <ul className="space-y-3 text-sm text-slate-300">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Compares candidate branch against trusted target base branch</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Fails CI on breaking changes; warns on potentially breaking changes</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Generates structured JSON artifacts for audit and reporting</span>
                </li>
              </ul>
            </div>

            <div className="rounded-xl border border-[#1e2438] bg-[#111420] p-5 font-mono text-xs shadow-2xl">
              <div className="text-slate-500 mb-2 font-sans text-[11px]">.api-contract-studio.yml</div>
              <pre className="text-slate-300 leading-relaxed overflow-x-auto">
{`version: 1

contracts:
  - name: public-api
    baseline: contracts/openapi.yaml
    candidate: contracts/candidate.yaml

policy:
  fail_on:
    - BREAKING
  potentially_breaking: warn
  severity_threshold: HIGH
  ignored_rules:
    - ACS-DOC-CHANGED

report:
  formats:
    - json
    - markdown`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-[#090a0f] border-t border-[#1e2438] text-xs text-slate-500">
        <div className="container max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span>API Contract Studio &bull; Apache-2.0 License</span>
          </div>
          <div>
            <span>Catch Breaking API Changes Before They Reach Production.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
