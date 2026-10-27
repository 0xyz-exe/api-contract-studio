"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, GitCompare, PlayCircle, FolderGit2, BarChart3, Terminal } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
    { href: "/projects", label: "Projects", icon: FolderGit2 },
    { href: "/contracts", label: "Contracts", icon: ShieldCheck },
    { href: "/compare", label: "Visual Diff", icon: GitCompare },
    { href: "/test", label: "Live Testing", icon: PlayCircle },
    { href: "/reports", label: "Reports", icon: Terminal },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center px-4">
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <ShieldCheck className="h-6 w-6 text-emerald-500" />
          <span className="font-bold tracking-tight text-foreground">API Contract Studio</span>
          <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-500 uppercase tracking-wider">
            v0.1
          </span>
        </Link>
        <nav className="flex items-center space-x-4 text-sm font-medium lg:space-x-6">
          {links.map((link) => {
            const Icon = link.icon;
            const active = pathname === link.href || pathname?.startsWith(link.href + "/");
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1.5 transition-colors hover:text-foreground/80 ${
                  active ? "text-foreground font-semibold" : "text-muted-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center space-x-3 text-sm">
          <Link
            href="/compare"
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 transition"
          >
            Quick Compare
          </Link>
          <Link
            href="/login"
            className="text-muted-foreground hover:text-foreground text-xs font-medium"
          >
            Sign In
          </Link>
        </div>
      </div>
    </header>
  );
}
